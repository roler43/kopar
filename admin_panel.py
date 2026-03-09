import asyncio
import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest
from aiogram.utils.keyboard import InlineKeyboardBuilder
import time

from database import db
from keyboards import (
    get_admin_keyboard, get_proxy_settings_keyboard, 
    get_back_to_main_keyboard, get_admin_subscription_keyboard,
    get_admin_support_keyboard
)
from config import ADMIN_IDS, PROXIES_FILE, WORKING_PROXIES_FILE, BAD_PROXIES_FILE
from proxy_checker import check_all_proxies
from emojis import Emojis
import config

router = Router()

class MailingStates(StatesGroup):
    waiting_for_message = State()

class AdminReplyStates(StatesGroup):
    waiting_for_reply = State()

class SubscriptionManageStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_subscription_type = State()
    waiting_for_duration = State()

def is_admin(user_id):
    """Проверка, является ли пользователь администратором"""
    return user_id in ADMIN_IDS

@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer(f"{Emojis.ERROR} У вас нет доступа к админ-панели.")
        return
    
    await message.answer(
        f"{Emojis.ADMIN} <b>Админ-панель</b>\n\n"
        f"Выберите действие:",
        reply_markup=get_admin_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer(f"{Emojis.ERROR} Доступ запрещен!", show_alert=True)
        return
    
    stats = db.get_stats()
    
    proxies_count = 0
    working_count = 0
    bad_count = 0
    
    if os.path.exists(PROXIES_FILE):
        with open(PROXIES_FILE, 'r', encoding='utf-8') as f:
            proxies_count = len([line for line in f if line.strip() and not line.startswith('#')])
    
    if os.path.exists(WORKING_PROXIES_FILE):
        with open(WORKING_PROXIES_FILE, 'r', encoding='utf-8') as f:
            working_count = len([line for line in f if line.strip() and not line.startswith('#')])
    
    if os.path.exists(BAD_PROXIES_FILE):
        with open(BAD_PROXIES_FILE, 'r', encoding='utf-8') as f:
            bad_count = len([line for line in f if line.strip() and not line.startswith('#')])
    
    proxy_status = f"{Emojis.UNLOCK} Включен" if config.USE_PROXY else f"{Emojis.LOCK} Отключен"
    
    # Получаем список админов из config
    admins_list = "\n".join([f"• {admin_id}" for admin_id in ADMIN_IDS])
    
    await callback.message.edit_text(
        f"{Emojis.STATS} <b>Статистика</b>\n\n"
        f"{Emojis.PROFILE} <b>Пользователи:</b>\n"
        f"• Всего: {stats['users_total']}\n"
        f"• Флудов запущено: {stats['floods_total']}\n"
        f"• VIP: {stats['vip_total']}\n\n"
        f"{Emojis.ADMIN} <b>Администраторы:</b>\n"
        f"{admins_list}\n\n"
        f"{Emojis.PROXY} <b>Прокси:</b>\n"
        f"• Режим: {proxy_status}\n"
        f"• В файле: {proxies_count}\n"
        f"• Рабочих: {working_count}\n"
        f"• Нерабочих: {bad_count}\n\n"
        f"{Emojis.MONEY} <b>Доход:</b> ${stats['total_income']:.2f}\n"
        f"{Emojis.SUPPORT} <b>Открытых тикетов:</b> {stats['open_tickets']}",
        reply_markup=get_admin_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

# ============= УПРАВЛЕНИЕ ПОДПИСКАМИ =============

@router.callback_query(F.data == "admin_manage_subscriptions")
async def admin_manage_subscriptions(callback: CallbackQuery):
    """Меню управления подписками"""
    if not is_admin(callback.from_user.id):
        await callback.answer(f"{Emojis.ERROR} Доступ запрещен!", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"{Emojis.VIP} <b>Управление подписками</b>\n\n"
        f"Выберите действие:",
        reply_markup=get_admin_subscription_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "admin_give_subscription")
async def admin_give_subscription(callback: CallbackQuery, state: FSMContext):
    """Выдать подписку пользователю"""
    if not is_admin(callback.from_user.id):
        await callback.answer(f"{Emojis.ERROR} Доступ запрещен!", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"{Emojis.VIP} <b>Выдача подписки</b>\n\n"
        f"Введите ID пользователя, которому хотите выдать подписку:",
        parse_mode="HTML"
    )
    await state.set_state(SubscriptionManageStates.waiting_for_user_id)
    await state.update_data(action="give")
    await callback.answer()

@router.callback_query(F.data == "admin_remove_subscription")
async def admin_remove_subscription(callback: CallbackQuery, state: FSMContext):
    """Забрать подписку у пользователя"""
    if not is_admin(callback.from_user.id):
        await callback.answer(f"{Emojis.ERROR} Доступ запрещен!", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"{Emojis.VIP} <b>Забрать подписку</b>\n\n"
        f"Введите ID пользователя, у которого хотите забрать подписку:",
        parse_mode="HTML"
    )
    await state.set_state(SubscriptionManageStates.waiting_for_user_id)
    await state.update_data(action="remove")
    await callback.answer()

@router.callback_query(F.data == "admin_check_subscription")
async def admin_check_subscription(callback: CallbackQuery, state: FSMContext):
    """Проверить подписку пользователя"""
    if not is_admin(callback.from_user.id):
        await callback.answer(f"{Emojis.ERROR} Доступ запрещен!", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"{Emojis.VIP} <b>Проверка подписки</b>\n\n"
        f"Введите ID пользователя для проверки:",
        parse_mode="HTML"
    )
    await state.set_state(SubscriptionManageStates.waiting_for_user_id)
    await state.update_data(action="check")
    await callback.answer()

@router.message(SubscriptionManageStates.waiting_for_user_id)
async def process_subscription_user_id(message: Message, state: FSMContext):
    """Обработка введенного ID пользователя"""
    if not is_admin(message.from_user.id):
        await message.answer(f"{Emojis.ERROR} Доступ запрещен!")
        await state.clear()
        return
    
    try:
        target_user_id = int(message.text.strip())
    except ValueError:
        await message.answer(
            f"{Emojis.ERROR} <b>Неверный формат ID!</b>\n\n"
            f"ID должен быть числом. Попробуйте снова:",
            parse_mode="HTML"
        )
        return
    
    data = await state.get_data()
    action = data.get('action')
    
    # Проверяем существование пользователя
    user_data = db.get_user(target_user_id)
    
    if not user_data:
        # Если пользователя нет в БД, создаем запись
        try:
            user = await message.bot.get_chat(target_user_id)
            db.add_user(
                target_user_id,
                user.username or "",
                user.first_name or "",
                user.last_name or ""
            )
            await message.answer(
                f"{Emojis.SUCCESS} <b>Пользователь добавлен в базу данных!</b>",
                parse_mode="HTML"
            )
        except:
            await message.answer(
                f"{Emojis.ERROR} <b>Пользователь с ID {target_user_id} не найден в Telegram!</b>\n\n"
                f"Убедитесь, что пользователь запускал бота.",
                parse_mode="HTML"
            )
            await state.clear()
            return
    
    await state.update_data(target_user_id=target_user_id)
    
    if action == "give":
        # Выбор типа подписки
        keyboard = InlineKeyboardBuilder()
        keyboard.row(
            InlineKeyboardButton(text="1 день", callback_data="sub_type_1day"),
            InlineKeyboardButton(text="7 дней", callback_data="sub_type_7days"),
            width=2
        )
        keyboard.row(
            InlineKeyboardButton(text="30 дней", callback_data="sub_type_30days"),
            InlineKeyboardButton(text="Навсегда", callback_data="sub_type_forever"),
            width=2
        )
        keyboard.row(
            InlineKeyboardButton(text="◀️ Отмена", callback_data="admin_manage_subscriptions",
                               icon_custom_emoji_id=Emojis.BACK_ID),
            width=1
        )
        
        await message.answer(
            f"{Emojis.VIP} <b>Выберите тип подписки для пользователя {target_user_id}:</b>",
            reply_markup=keyboard.as_markup(),
            parse_mode="HTML"
        )
        await state.set_state(SubscriptionManageStates.waiting_for_subscription_type)
    
    elif action == "remove":
        # Забираем подписку
        db.cursor.execute(
            'UPDATE users SET subscription_type = "none", subscription_until = 0 WHERE user_id = ?',
            (target_user_id,)
        )
        db.conn.commit()
        
        await message.answer(
            f"{Emojis.SUCCESS} <b>Подписка успешно забрана у пользователя {target_user_id}!</b>",
            reply_markup=get_admin_keyboard(),
            parse_mode="HTML"
        )
        await state.clear()
        
        # Уведомляем пользователя
        try:
            await message.bot.send_message(
                target_user_id,
                f"{Emojis.VIP} <b>Уведомление от администрации</b>\n\n"
                f"Ваша VIP подписка была отозвана администратором.",
                parse_mode="HTML"
            )
        except:
            pass
    
    elif action == "check":
        # Проверяем подписку
        sub_type, sub_until = db.get_subscription_type(target_user_id)
        
        if sub_type == 'none':
            status = "❌ Нет активной подписки"
            until_text = "—"
        elif sub_type == 'forever':
            status = f"{Emojis.VIP} Навсегда"
            until_text = "Навсегда"
        else:
            days_left = (sub_until - int(time.time())) // 86400
            hours_left = ((sub_until - int(time.time())) % 86400) // 3600
            sub_names = {'1day': '1 день', '7days': '7 дней', '30days': '30 дней'}
            status = f"{Emojis.VIP} {sub_names[sub_type]}"
            until_text = f"{days_left}д {hours_left}ч (до {time.strftime('%d.%m.%Y %H:%M', time.localtime(sub_until))})"
        
        await message.answer(
            f"{Emojis.VIP} <b>Информация о подписке пользователя {target_user_id}</b>\n\n"
            f"Статус: {status}\n"
            f"Действует до: {until_text}",
            reply_markup=get_admin_keyboard(),
            parse_mode="HTML"
        )
        await state.clear()

@router.callback_query(F.data.startswith("sub_type_"))
async def process_subscription_type(callback: CallbackQuery, state: FSMContext):
    """Обработка выбранного типа подписки"""
    if not is_admin(callback.from_user.id):
        await callback.answer(f"{Emojis.ERROR} Доступ запрещен!", show_alert=True)
        return
    
    sub_type = callback.data.replace("sub_type_", "")
    data = await state.get_data()
    target_user_id = data.get('target_user_id')
    
    # Выдаем подписку
    if sub_type == 'forever':
        days = 36500
    else:
        days = int(sub_type.replace('day', '').replace('days', ''))
    
    db.update_subscription(target_user_id, days, sub_type)
    
    # Получаем информацию о подписке
    sub_names = {
        '1day': '1 день',
        '7days': '7 дней',
        '30days': '30 дней',
        'forever': 'Навсегда'
    }
    
    await callback.message.edit_text(
        f"{Emojis.SUCCESS} <b>Подписка успешно выдана!</b>\n\n"
        f"Пользователь: <code>{target_user_id}</code>\n"
        f"Тип подписки: {sub_names[sub_type]}\n"
        f"Администратор: {callback.from_user.id}",
        reply_markup=get_admin_keyboard(),
        parse_mode="HTML"
    )
    
    # Уведомляем пользователя
    try:
        await callback.bot.send_message(
            target_user_id,
            f"{Emojis.VIP} <b>Поздравляем!</b>\n\n"
            f"Администратор выдал вам VIP подписку <b>{sub_names[sub_type]}</b>!",
            parse_mode="HTML"
        )
    except:
        pass
    
    await state.clear()
    await callback.answer()

# ============= НАСТРОЙКИ ПРОКСИ =============

@router.callback_query(F.data == "admin_proxy_settings")
async def admin_proxy_settings(callback: CallbackQuery):
    """Настройки прокси"""
    if not is_admin(callback.from_user.id):
        await callback.answer(f"{Emojis.ERROR} Доступ запрещен!", show_alert=True)
        return
    
    status = f"{Emojis.UNLOCK} Включен" if config.USE_PROXY else f"{Emojis.LOCK} Отключен"
    
    await callback.message.edit_text(
        f"{Emojis.SETTINGS} <b>Настройки прокси</b>\n\n"
        f"Текущий статус: {status}\n\n"
        f"Выберите действие:",
        reply_markup=get_proxy_settings_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "proxy_on")
async def proxy_on(callback: CallbackQuery):
    """Включить прокси"""
    if not is_admin(callback.from_user.id):
        await callback.answer(f"{Emojis.ERROR} Доступ запрещен!", show_alert=True)
        return
    
    config.USE_PROXY = True
    status = f"{Emojis.UNLOCK} Включен"
    
    await callback.message.edit_text(
        f"{Emojis.SUCCESS} <b>Прокси включены!</b>\n\n"
        f"Теперь флуд будет использовать прокси.\n"
        f"Текущий статус: {status}",
        reply_markup=get_proxy_settings_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "proxy_off")
async def proxy_off(callback: CallbackQuery):
    """Выключить прокси"""
    if not is_admin(callback.from_user.id):
        await callback.answer(f"{Emojis.ERROR} Доступ запрещен!", show_alert=True)
        return
    
    config.USE_PROXY = False
    status = f"{Emojis.LOCK} Отключен"
    
    await callback.message.edit_text(
        f"{Emojis.SUCCESS} <b>Прокси отключены!</b>\n\n"
        f"Теперь флуд будет работать без прокси.\n"
        f"Текущий статус: {status}",
        reply_markup=get_proxy_settings_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "admin_check_proxies")
async def admin_check_proxies(callback: CallbackQuery):
    """Проверка прокси"""
    if not is_admin(callback.from_user.id):
        await callback.answer(f"{Emojis.ERROR} Доступ запрещен!", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"{Emojis.PROXY} <b>Проверка прокси...</b>\n\n"
        f"Это может занять некоторое время.\n"
        f"Пожалуйста, подождите...",
        parse_mode="HTML"
    )
    
    try:
        # Запускаем проверку прокси в отдельном потоке
        working, bad = await asyncio.to_thread(check_all_proxies)
        
        result_text = (
            f"{Emojis.SUCCESS} <b>Проверка прокси завершена!</b>\n\n"
            f"{Emojis.PROXY} <b>Результаты:</b>\n"
            f"• Всего проверено: {len(working) + len(bad)}\n"
            f"• {Emojis.UNLOCK} Рабочих: {len(working)}\n"
            f"• {Emojis.LOCK} Нерабочих: {len(bad)}\n\n"
        )
        
        if working:
            result_text += f"{Emojis.SUCCESS} Рабочие прокси сохранены в файл working_proxies.txt"
        else:
            result_text += f"{Emojis.ERROR} Нет рабочих прокси! Добавьте прокси в файл proxies.txt"
        
        await callback.message.edit_text(
            result_text,
            reply_markup=get_admin_keyboard(),
            parse_mode="HTML"
        )
    except Exception as e:
        await callback.message.edit_text(
            f"{Emojis.ERROR} <b>Ошибка при проверке прокси</b>\n\n"
            f"{str(e)}",
            reply_markup=get_admin_keyboard(),
            parse_mode="HTML"
        )
    
    await callback.answer()

# ============= РАССЫЛКА =============

@router.callback_query(F.data == "admin_mailing")
async def admin_mailing(callback: CallbackQuery, state: FSMContext):
    """Рассылка сообщений"""
    if not is_admin(callback.from_user.id):
        await callback.answer(f"{Emojis.ERROR} Доступ запрещен!", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"{Emojis.MAIL} <b>Рассылка</b>\n\n"
        f"Введите текст для рассылки всем пользователям:\n\n"
        f"<i>Поддерживается HTML разметка</i>",
        parse_mode="HTML"
    )
    await state.set_state(MailingStates.waiting_for_message)
    await callback.answer()

@router.message(MailingStates.waiting_for_message)
async def process_mailing(message: Message, state: FSMContext):
    """Обработка текста рассылки"""
    if not is_admin(message.from_user.id):
        await message.answer(f"{Emojis.ERROR} Доступ запрещен!")
        await state.clear()
        return
    
    text = message.text
    users = db.get_all_users()
    
    if not users:
        await message.answer(
            f"{Emojis.ERROR} <b>Нет пользователей для рассылки</b>",
            parse_mode="HTML"
        )
        await state.clear()
        return
    
    sent = 0
    failed = 0
    
    status_msg = await message.answer(
        f"{Emojis.MAIL} <b>Отправка рассылки...</b>\n\n"
        f"Прогресс: 0/{len(users)}",
        parse_mode="HTML"
    )
    
    for i, user_id in enumerate(users):
        try:
            await message.bot.send_message(
                user_id,
                f"{Emojis.MAIL} <b>Рассылка</b>\n\n{text}",
                parse_mode="HTML"
            )
            sent += 1
        except Exception as e:
            failed += 1
            print(f"Ошибка отправки пользователю {user_id}: {e}")
        
        if i % 10 == 0:
            try:
                await status_msg.edit_text(
                    f"{Emojis.MAIL} <b>Отправка рассылки...</b>\n\n"
                    f"Прогресс: {i}/{len(users)}\n"
                    f"✅ Успешно: {sent}\n"
                    f"❌ Ошибок: {failed}",
                    parse_mode="HTML"
                )
            except:
                pass
        
        await asyncio.sleep(0.05)
    
    await status_msg.edit_text(
        f"{Emojis.SUCCESS} <b>Рассылка завершена!</b>\n\n"
        f"📊 <b>Статистика:</b>\n"
        f"• Всего пользователей: {len(users)}\n"
        f"• {Emojis.SUCCESS} Отправлено: {sent}\n"
        f"• {Emojis.ERROR} Ошибок: {failed}",
        parse_mode="HTML"
    )
    
    await state.clear()

# ============= ПОДДЕРЖКА =============

@router.callback_query(F.data == "admin_support")
async def admin_support(callback: CallbackQuery):
    """Просмотр обращений в поддержку"""
    if not is_admin(callback.from_user.id):
        await callback.answer(f"{Emojis.ERROR} Доступ запрещен!", show_alert=True)
        return
    
    tickets = db.get_open_tickets()
    
    try:
        await callback.message.delete()
    except:
        pass
    
    if not tickets:
        await callback.message.answer(
            f"{Emojis.SUPPORT} <b>Открытых обращений нет</b>",
            reply_markup=get_back_to_main_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    for ticket in tickets[:5]:
        ticket_id, user_id, message_text, created_at, status, _, _ = ticket
        
        try:
            user = await callback.bot.get_chat(user_id)
            user_name = user.first_name
            username = f"@{user.username}" if user.username else "Нет username"
        except:
            user_name = "Неизвестно"
            username = "Неизвестно"
        
        await callback.message.answer(
            f"{Emojis.TICKET} <b>Обращение #{ticket_id}</b>\n\n"
            f"{Emojis.PROFILE} <b>Пользователь:</b> {user_name}\n"
            f"{Emojis.PHONE} <b>Username:</b> {username}\n"
            f"{Emojis.ID} <b>ID:</b> <code>{user_id}</code>\n"
            f"{Emojis.DATE} <b>Время:</b> {created_at}\n\n"
            f"<b>📝 Сообщение:</b>\n{message_text}",
            reply_markup=get_admin_support_keyboard(ticket_id),
            parse_mode="HTML"
        )
    
    await callback.answer()

@router.callback_query(F.data.startswith("reply_ticket_"))
async def reply_to_ticket(callback: CallbackQuery, state: FSMContext):
    """Ответ на тикет"""
    if not is_admin(callback.from_user.id):
        await callback.answer(f"{Emojis.ERROR} Доступ запрещен!", show_alert=True)
        return
    
    ticket_id = int(callback.data.split("_")[2])
    await state.update_data(ticket_id=ticket_id)
    
    await callback.message.edit_text(
        f"{Emojis.REPLY} <b>Ответ на обращение #{ticket_id}</b>\n\n"
        f"Введите ваш ответ:",
        parse_mode="HTML"
    )
    await state.set_state(AdminReplyStates.waiting_for_reply)
    await callback.answer()

@router.message(AdminReplyStates.waiting_for_reply)
async def process_admin_reply(message: Message, state: FSMContext):
    """Обработка ответа на тикет"""
    if not is_admin(message.from_user.id):
        await message.answer(f"{Emojis.ERROR} Доступ запрещен!")
        await state.clear()
        return
    
    data = await state.get_data()
    ticket_id = data.get('ticket_id')
    reply_text = message.text
    
    ticket = db.get_ticket(ticket_id)
    if not ticket:
        await message.answer(f"{Emojis.ERROR} <b>Тикет не найден!</b>", parse_mode="HTML")
        await state.clear()
        return
    
    user_id = ticket[1]
    
    db.reply_to_ticket(ticket_id, reply_text)
    
    try:
        await message.bot.send_message(
            user_id,
            f"{Emojis.SUPPORT} <b>Ответ от поддержки</b>\n\n"
            f"<b>На ваше обращение #{ticket_id} получен ответ:</b>\n\n"
            f"{reply_text}",
            parse_mode="HTML"
        )
        
        await message.answer(
            f"{Emojis.SUCCESS} <b>Ответ отправлен пользователю!</b>",
            parse_mode="HTML"
        )
    except Exception as e:
        await message.answer(
            f"{Emojis.ERROR} <b>Не удалось отправить ответ пользователю</b>\n\n{str(e)}",
            parse_mode="HTML"
        )
    
    await state.clear()

@router.callback_query(F.data == "back_to_admin")
async def back_to_admin(callback: CallbackQuery):
    """Возврат в админ-панель"""
    if not is_admin(callback.from_user.id):
        await callback.answer(f"{Emojis.ERROR} Доступ запрещен!", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"{Emojis.ADMIN} <b>Админ-панель</b>\n\n"
        f"Выберите действие:",
        reply_markup=get_admin_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "admin_check_sessions")
async def admin_check_sessions(callback: CallbackQuery):
    """Проверка сессий и каналов"""
    if not is_admin(callback.from_user.id):
        await callback.answer(f"{Emojis.ERROR} Доступ запрещен!", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"{Emojis.SETTINGS} <b>Проверка сессий...</b>\n\n"
        f"{Emojis.TIME} Получаю информацию о сессиях и каналах...",
        parse_mode="HTML"
    )
    
    from session_manager import SessionManager
    session_manager = SessionManager()
    channels_info = await session_manager.get_all_channels_info()
    
    if not channels_info:
        await callback.message.edit_text(
            f"{Emojis.ERROR} <b>Нет активных сессий!</b>\n\n"
            f"{Emojis.INFO} Добавьте .session файлы в папку sessions/\n\n"
            f"{Emojis.PHONE} Положите файлы сессий в папку sessions/ и перезапустите бота",
            reply_markup=get_admin_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    text = f"{Emojis.SUCCESS} <b>Информация о сессиях:</b>\n\n"
    
    total_channels = 0
    for info in channels_info:
        text += f"{Emojis.PROFILE} <b>Сессия:</b> {info['session_name']}\n"
        text += f"{Emojis.PHONE} <b>Телефон:</b> {info['session_phone']}\n"
        text += f"{Emojis.COUNT} <b>Каналов/чатов:</b> {info['channels_count']}\n"
        
        if info['channels']:
            text += f"{Emojis.CHANNEL} <b>Первые 10:</b>\n"
            for channel in info['channels'][:10]:
                text += f"  • {channel}\n"
        
        text += "\n"
        total_channels += info['channels_count']
    
    text += f"{Emojis.STATS} <b>Всего:</b> {len(channels_info)} сессий, {total_channels} каналов/чатов"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_admin_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()
