import os
import asyncio
from telethon import TelegramClient
from telethon.tl.types import Channel, Chat, ChatBannedRights, User
from telethon.tl.functions.channels import EditBannedRequest, GetParticipantRequest
from telethon.tl.functions.messages import GetFullChatRequest
from telethon.errors import FloodWaitError, UserAdminInvalidError, ChatAdminRequiredError
from config import API_ID, API_HASH

class SessionManager:
    def __init__(self):
        self.clients = []
    
    def find_sessions(self) -> list:
        """Поиск всех сессий в директории sessions"""
        session_files = []
        sessions_dir = 'sessions'
        
        # Создаем папку если её нет
        if not os.path.exists(sessions_dir):
            os.makedirs(sessions_dir)
            return []
        
        for file in os.listdir(sessions_dir):
            if file.endswith('.session'):
                session_path = os.path.join(sessions_dir, file[:-8])  # Убираем .session
                session_files.append(session_path)
        
        return session_files
    
    async def init_clients(self) -> bool:
        """Инициализация всех клиентов из папки sessions"""
        sessions = self.find_sessions()
        print(f"[SessionManager] Найдено файлов сессий: {len(sessions)}")
        
        # Закрываем старые клиенты
        await self.disconnect_all()
        
        self.clients = []
        for session_path in sessions:
            try:
                client = TelegramClient(session_path, API_ID, API_HASH)
                await client.connect()
                
                if await client.is_user_authorized():
                    me = await client.get_me()
                    self.clients.append({
                        'client': client,
                        'name': os.path.basename(session_path),
                        'phone': me.phone if hasattr(me, 'phone') else 'Unknown',
                        'user_id': me.id,
                        'username': me.username
                    })
                    print(f"[SessionManager] ✅ Активна сессия: {os.path.basename(session_path)} (@{me.username})")
                else:
                    print(f"[SessionManager] ❌ Сессия не авторизована: {os.path.basename(session_path)}")
                    await client.disconnect()
            except Exception as e:
                print(f"[SessionManager] ❌ Ошибка сессии {os.path.basename(session_path)}: {e}")
                continue
        
        return len(self.clients) > 0
    
    async def check_admin_rights(self, client, dialog_entity):
        """Проверка прав администратора в диалоге"""
        try:
            me = await client.get_me()
            
            # Пытаемся получить информацию о себе как участнике
            if isinstance(dialog_entity, Channel):
                try:
                    participant = await client(GetParticipantRequest(
                        channel=dialog_entity,
                        participant=me
                    ))
                    
                    # Проверяем права администратора
                    if hasattr(participant, 'participant'):
                        if hasattr(participant.participant, 'admin_rights'):
                            admin_rights = participant.participant.admin_rights
                            if admin_rights and admin_rights.ban_users:
                                return True, "admin"
                except Exception as e:
                    # Если не удалось получить участника, возможно мы не в канале
                    return False, "not_member"
            
            elif isinstance(dialog_entity, Chat):
                # Для обычных чатов проверяем создателя или админа
                try:
                    full_chat = await client(GetFullChatRequest(dialog_entity.id))
                    if full_chat.full_chat:
                        # Проверяем, являемся ли мы создателем
                        if hasattr(full_chat.full_chat, 'participants'):
                            for participant in full_chat.full_chat.participants.participants:
                                if participant.user_id == me.id:
                                    if hasattr(participant, 'is_admin') and participant.is_admin:
                                        return True, "admin"
                                    elif hasattr(participant, 'is_creator') and participant.is_creator:
                                        return True, "creator"
                except:
                    pass
            
            return False, "no_rights"
            
        except Exception as e:
            print(f"[SessionManager] Ошибка проверки прав: {e}")
            return False, "error"
    
    async def get_all_dialogs(self, client):
        """Получение всех диалогов (каналы, чаты, группы) где есть права на бан"""
        dialogs_with_rights = []
        
        try:
            print(f"[SessionManager] Получение диалогов для сессии...")
            async for dialog in client.iter_dialogs():
                try:
                    entity = dialog.entity
                    
                    # Пропускаем диалоги без названия
                    if not hasattr(entity, 'title') or not entity.title:
                        continue
                    
                    # Проверяем права в этом диалоге
                    has_rights, rights_type = await self.check_admin_rights(client, entity)
                    
                    if has_rights:
                        dialogs_with_rights.append({
                            'entity': entity,
                            'title': entity.title,
                            'id': entity.id,
                            'type': 'channel' if isinstance(entity, Channel) else 'chat',
                        })
                    
                except Exception as e:
                    print(f"[SessionManager] Ошибка обработки диалога: {e}")
                    continue
                    
        except Exception as e:
            print(f"[SessionManager] Ошибка получения диалогов: {e}")
        
        print(f"[SessionManager] Найдено диалогов с правами: {len(dialogs_with_rights)}")
        return dialogs_with_rights
    
    async def get_all_channels_info(self):
        """Получение информации о всех каналах из всех сессий"""
        if not await self.init_clients():
            return []
        
        channels_info = []
        for session_info in self.clients:
            dialogs = await self.get_all_dialogs(session_info['client'])
            channels_info.append({
                'session_name': session_info['name'],
                'session_phone': session_info['phone'],
                'session_username': session_info['username'],
                'channels_count': len(dialogs),
                'channels': [f"{d['title']} ({d['type']})" for d in dialogs[:10]]
            })
        
        await self.disconnect_all()
        return channels_info
    
    async def get_target_user(self, client, target_username):
        """Получение пользователя по юзернейму"""
        try:
            # Убираем @ если есть
            clean_username = target_username.replace('@', '')
            entity = await client.get_entity(clean_username)
            
            if isinstance(entity, User):
                user_info = {
                    'id': entity.id,
                    'username': entity.username,
                    'first_name': entity.first_name,
                    'last_name': entity.last_name,
                    'access_hash': entity.access_hash
                }
                return user_info, None
            else:
                return None, "Это не пользователь, а канал/чат"
                
        except Exception as e:
            error_msg = str(e)
            if "Username not found" in error_msg:
                return None, "Пользователь не найден"
            elif "Username invalid" in error_msg:
                return None, "Неверный формат юзернейма"
            else:
                return None, f"Ошибка: {type(e).__name__}"
    
    async def ban_user_in_dialog(self, client, dialog, target_user):
        """Бан пользователя в конкретном диалоге"""
        try:
            rights = ChatBannedRights(
                until_date=None,
                view_messages=True,
                send_messages=True,
                send_media=True,
                send_stickers=True,
                send_gifs=True,
                send_games=True,
                send_inline=True,
                send_polls=True,
                change_info=True,
                invite_users=True,
                pin_messages=True,
            )
            
            # Получаем полную сущность пользователя
            try:
                user_entity = await client.get_entity(target_user['id'])
            except:
                user_entity = target_user['id']
            
            await client(EditBannedRequest(
                channel=dialog['entity'],
                participant=user_entity,
                banned_rights=rights
            ))
            
            return True, dialog['title'], None
            
        except FloodWaitError as e:
            print(f"[SessionManager] FloodWait: ждем {e.seconds} секунд")
            await asyncio.sleep(e.seconds)
            return False, dialog['title'], f"Flood wait {e.seconds}с"
        except UserAdminInvalidError:
            return False, dialog['title'], "Нельзя забанить администратора"
        except ChatAdminRequiredError:
            return False, dialog['title'], "Нет прав администратора"
        except Exception as e:
            error_msg = str(e)
            if "USER_NOT_PARTICIPANT" in error_msg:
                return False, dialog['title'], "Пользователь не в чате"
            elif "USER_ID_INVALID" in error_msg:
                return False, dialog['title'], "Неверный ID пользователя"
            elif "CHAT_ADMIN_REQUIRED" in error_msg:
                return False, dialog['title'], "Требуются права администратора"
            else:
                return False, dialog['title'], type(e).__name__
    
    async def execute_global_ban(self, target_username: str) -> tuple:
        """Выполнение глобального бана пользователя во всех каналах и чатах"""
        print(f"\n[SessionManager] 🚀 Запуск глобального бана для @{target_username}")
        
        if not await self.init_clients():
            print("[SessionManager] ❌ Нет активных сессий!")
            return 0, 0, ["Нет активных сессий"]
        
        total_bans = 0
        sessions_with_bans = 0
        failed_bans = []
        
        # Для каждой сессии
        for session_info in self.clients:
            client = session_info['client']
            session_name = session_info['name']
            
            try:
                # Получаем цель для бана
                target_user, error = await self.get_target_user(client, target_username)
                if not target_user:
                    failed_bans.append(f"Сессия {session_name}: {error}")
                    continue
                
                print(f"[SessionManager] ✅ Цель найдена: {target_user['first_name']}")
                
                # Получаем все диалоги с правами
                dialogs = await self.get_all_dialogs(client)
                if not dialogs:
                    failed_bans.append(f"Сессия {session_name}: нет прав в диалогах")
                    continue
                
                # Баним в каждом диалоге
                session_bans = 0
                for dialog in dialogs:
                    success, title, error = await self.ban_user_in_dialog(client, dialog, target_user)
                    
                    if success:
                        total_bans += 1
                        session_bans += 1
                    
                    # Небольшая задержка между банами
                    await asyncio.sleep(0.3)
                
                if session_bans > 0:
                    sessions_with_bans += 1
                    print(f"[SessionManager] 📊 Сессия {session_name}: {session_bans} банов")
                
            except Exception as e:
                failed_bans.append(f"Сессия {session_name}: ошибка {type(e).__name__}")
                continue
        
        print(f"\n[SessionManager] 🎯 Готово! Всего банов: {total_bans}")
        await self.disconnect_all()
        return total_bans, sessions_with_bans, failed_bans
    
    async def disconnect_all(self):
        """Отключение всех клиентов"""
        for session_info in self.clients:
            try:
                await session_info['client'].disconnect()
            except:
                pass
        self.clients = []
