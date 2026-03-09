from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
import asyncio

from keyboards import (
    get_flood_confirm_keyboard, get_flood_stop_keyboard, 
    get_back_to_main_keyboard, get_main_keyboard, get_snos_type_keyboard
)
from database import db
from services import flood_worker, load_working_proxies
from session_manager import SessionManager
from config import FLOOD_DURATION, CHANNEL_USERNAME, SNOS_IMAGE, BOT_USERNAME, CHANNEL_LINK
from emojis import Emojis
import config

router = Router()
flood_tasks = {}
flood_active = {}
session_manager = SessionManager()

class FloodStates(StatesGroup):
    waiting_for_snos_type = State()
    waiting_for_phone = State()
    waiting_for_username = State()
    flood_active = State()

@router.callback_query(F.data == "flood_menu")
async def flood_menu(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    
    # Получаем актуальное имя из Telegram
    try:
        user = await callback.bot.get_chat(user_id)
        current_first_name = user.first_name or ""
        
        # Обновляем имя в базе
        db.update_user_name(user_id, current_first_name)
    except Exception as e:
        print(f"Ошибка получения имени: {e}")
        user_data = db.get_user(user_id)
        current_first_name = user_data[2] if user_data else ""
    
    print(f"Проверка имени для флуда: {current_first_name}")
    
    # Проверяем наличие бота в ИМЕНИ (first_name)
    if not current_first_name or BOT_USERNAME not in current_first_name:
        await callback.answer(
            f"{Emojis.ERROR} Добавьте @{BOT_USERNAME} в своё имя!\n\n"
            f"Текущее имя: {current_first_name}\n"
            f"Настройки → Имя → добавить {BOT_USERNAME}\n"
            f"Например: {BOT_USERNAME} Вадим",
            show_alert=True
        )
        return
    
    # Проверяем подписку на канал
    try:
        chat_member = await callback.bot.get_chat_member(
            chat_id=f"@{CHANNEL_USERNAME}",
            user_id=user_id
        )
        if chat_member.status in ['left', 'kicked']:
            await callback.answer(
                f"{Emojis.ERROR} Вы не подписаны на канал!\n\n"
                f"Подпишитесь: {CHANNEL_LINK}",
                show_alert=True
            )
            return
    except Exception as e:
        print(f"Ошибка проверки подписки: {e}")
        await callback.answer(
            f"{Emojis.ERROR} Ошибка проверки подписки!",
            show_alert=True
        )
        return
    
    sub_type, sub_until = db.get_subscription_type(user_id)
    
    try:
        await callback.message.delete()
    except:
        pass
    
    photo = FSInputFile(SNOS_IMAGE)
    await callback.message.answer_photo(
        photo=photo,
        caption=f"{Emojis.FLOOD} <b>Sn0s</b>\n\n"
                f"{Emojis.SETTINGS} <b>Выберите тип сноса:</b>\n\n"
                f"{Emojis.PHONE} • По номеру телефона\n"
                f"{Emojis.PROFILE} • По юзернейму (@username)",
        reply_markup=get_snos_type_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(FloodStates.waiting_for_snos_type)
    await callback.answer()

@router.callback_query(F.data == "snos_phone")
async def snos_phone(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    
    photo = FSInputFile(SNOS_IMAGE)
    await callback.message.answer_photo(
        photo=photo,
        caption=f"{Emojis.FLOOD} <b>Sn0s по номеру телефона</b>\n\n"
                f"{Emojis.PHONE} Введите номер телефона в формате:\n"
                f"<code>+79590002234</code>",
        reply_markup=get_back_to_main_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(FloodStates.waiting_for_phone)
    await callback.answer()

@router.callback_query(F.data == "snos_username")
async def snos_username(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    
    # Проверяем подписку для использования сессий
    sub_type, _ = db.get_subscription_type(user_id)
    if sub_type == 'none':
        await callback.answer(
            f"{Emojis.ERROR} Для сноса по юзернейму нужна VIP подписка!",
            show_alert=True
        )
        return
    
    await callback.message.delete()
    
    photo = FSInputFile(SNOS_IMAGE)
    await callback.message.answer_photo(
        photo=photo,
        caption=f"{Emojis.FLOOD} <b>Sn0s по юзернейму</b>\n\n"
                f"{Emojis.PROFILE} Введите юзернейм пользователя:\n"
                f"<code>@username</code> или просто <code>username</code>\n\n"
                f"{Emojis.INFO} <i>Пользователь будет забанен во всех ваших каналах и чатах</i>",
        reply_markup=get_back_to_main_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(FloodStates.waiting_for_username)
    await callback.answer()

@router.message(FloodStates.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    phone = message.text.strip()
    
    # Проверяем формат номера
    if not phone.startswith('+') or len(phone) < 10 or not phone[1:].isdigit():
        await message.answer(
            f"{Emojis.ERROR} <b>Неверный формат номера!</b>\n\n"
            f"{Emojis.PHONE} Используйте формат: <code>+79590002234</code>\n"
            f"{Emojis.REPLY} Попробуйте снова:",
            reply_markup=get_back_to_main_keyboard(),
            parse_mode="HTML"
        )
        return
    
    await state.update_data(phone=phone)
    
    await message.answer(
        f"{Emojis.PHONE} <b>Номер:</b> <code>{phone}</code>\n\n"
        f"{Emojis.FLOOD} <b>Запустить Sn0s на 10 минут?</b>",
        reply_markup=get_flood_confirm_keyboard(),
        parse_mode="HTML"
    )

@router.message(FloodStates.waiting_for_username)
async def process_username(message: Message, state: FSMContext):
    username = message.text.strip()
    user_id = message.from_user.id
    
    # Очищаем username от @ если есть
    clean_username = username.replace('@', '').strip()
    
    if not clean_username:
        await message.answer(
            f"{Emojis.ERROR} <b>Неверный формат юзернейма!</b>\n\n"
            f"{Emojis.PROFILE} Введите юзернейм пользователя:\n"
            f"<code>@username</code>",
            reply_markup=get_back_to_main_keyboard(),
            parse_mode="HTML"
        )
        return
    
    await state.update_data(username=clean_username)
    
    # Отправляем сообщение о начале процесса
    status_msg = await message.answer(
        f"{Emojis.FLOOD} <b>Запуск Sn0s по юзернейму...</b>\n\n"
        f"{Emojis.PROFILE} <b>Цель:</b> @{clean_username}\n"
        f"{Emojis.TIME} <b>Поиск сессий и каналов...</b>",
        parse_mode="HTML"
    )
    
    # Выполняем глобальный бан
    total_bans, sessions_with_bans, failed_bans = await session_manager.execute_global_ban(clean_username)
    
    # Удаляем статусное сообщение
    try:
        await status_msg.delete()
    except:
        pass
    
    if total_bans > 0:
        # Простое сообщение с общим результатом
        await message.answer(
            f"{Emojis.SUCCESS} <b>Sn0s успешно выполнен!</b>\n\n"
            f"{Emojis.PROFILE} <b>Цель:</b> @{clean_username}\n"
            f"{Emojis.COUNT} <b>Забанено в каналах/чатах:</b> {total_bans}\n"
            f"{Emojis.STATS} <b>Сессий использовано:</b> {sessions_with_bans}",
            reply_markup=get_main_keyboard(),
            parse_mode="HTML"
        )
    else:
        # Сообщение об ошибке
        error_reasons = []
        for fail in failed_bans[:3]:
            if "нет прав" in fail.lower():
                error_reasons.append("• Нет прав администратора в каналах")
            elif "не найден" in fail.lower():
                error_reasons.append("• Пользователь не найден")
            else:
                error_reasons.append(f"• {fail.split(':')[-1].strip()}")
        
        error_text = "\n".join(error_reasons) if error_reasons else "• Неизвестная ошибка"
        
        await message.answer(
            f"{Emojis.ERROR} <b>Sn0s не удался</b>\n\n"
            f"{Emojis.PROFILE} <b>Цель:</b> @{clean_username}\n"
            f"{Emojis.INFO} <b>Причины:</b>\n"
            f"{error_text}\n\n"
            f"{Emojis.SUPPORT} Проверьте права администратора в каналах",
            reply_markup=get_main_keyboard(),
            parse_mode="HTML"
        )
    
    await state.clear()

@router.callback_query(F.data == "flood_confirm")
async def flood_confirm(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    data = await state.get_data()
    phone = data.get('phone')
    
    if not phone:
        await callback.message.edit_text(
            f"{Emojis.ERROR} <b>Ошибка! Попробуйте снова.</b>",
            reply_markup=get_back_to_main_keyboard(),
            parse_mode="HTML"
        )
        await state.clear()
        await callback.answer()
        return
    
    sub_type, _ = db.get_subscription_type(user_id)
    
    # Обновляем время последнего флуда
    db.update_last_flood(user_id)
    
    # Устанавливаем флаг активности
    flood_active[user_id] = True
    
    # Получаем статус подписки для отображения
    if sub_type == 'forever':
        sub_status = "Forever VIP"
    elif sub_type in ['1day', '7days', '30days']:
        sub_status = "VIP"
    elif sub_type == 'trial':
        sub_status = "Триал"
    else:
        sub_status = "Обычный"
    
    # Показываем статусное сообщение
    status_message = await callback.message.edit_text(
        f"{Emojis.FLOOD} <b>Sn0s запущен для номера</b> <code>{phone}</code>\n\n"
        f"{Emojis.TIME} <b>Длительность:</b> 10 минут\n"
        f"{Emojis.VIP} <b>Статус:</b> {sub_status}\n"
        f"{Emojis.STOP} Нажмите кнопку ниже для остановки",
        reply_markup=get_flood_stop_keyboard(),
        parse_mode="HTML"
    )
    
    # Запускаем флуд в фоне
    task = asyncio.create_task(
        flood_worker(phone, status_message, callback.bot, user_id, FLOOD_DURATION, flood_active)
    )
    flood_tasks[user_id] = task
    
    await state.set_state(FloodStates.flood_active)
    await callback.answer()

@router.callback_query(F.data == "flood_stop")
async def flood_stop(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    
    # Сбрасываем флаг активности
    if user_id in flood_active:
        flood_active[user_id] = False
    
    # Отменяем задачу если она есть
    if user_id in flood_tasks:
        flood_tasks[user_id].cancel()
        try:
            await flood_tasks[user_id]
        except asyncio.CancelledError:
            print(f"Задача флуда для пользователя {user_id} отменена")
        except Exception as e:
            print(f"Ошибка при отмене задачи: {e}")
        finally:
            if user_id in flood_tasks:
                del flood_tasks[user_id]
    
    # Удаляем из словаря активности
    if user_id in flood_active:
        del flood_active[user_id]
    
    # Получаем информацию о подписке для отображения кулдауна
    sub_type, _ = db.get_subscription_type(user_id)
    
    if sub_type == 'forever':
        cooldown_text = "0 секунд"
    elif sub_type in ['1day', '7days', '30days', 'trial']:
        cooldown_text = "1 минута"
    else:
        cooldown_text = "5 минут"
    
    try:
        await callback.message.edit_text(
            f"{Emojis.STOP} <b>Sn0s остановлен!</b>\n\n"
            f"{Emojis.TIME} Следующий Sn0s можно запустить через {cooldown_text}.\n"
            f"{Emojis.BACK} Нажмите кнопку ниже для возврата в меню",
            reply_markup=get_back_to_main_keyboard(),
            parse_mode="HTML"
        )
    except:
        # Если не удалось отредактировать, отправляем новое сообщение
        await callback.message.answer(
            f"{Emojis.STOP} <b>Sn0s остановлен!</b>\n\n"
            f"{Emojis.TIME} Следующий Sn0s можно запустить через {cooldown_text}.\n"
            f"{Emojis.BACK} Нажмите кнопку ниже для возврата в меню",
            reply_markup=get_back_to_main_keyboard(),
            parse_mode="HTML"
        )
    
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "flood_cancel")
async def flood_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    
    try:
        await callback.message.delete()
    except:
        pass
    
    photo = FSInputFile(SNOS_IMAGE)
    await callback.message.answer_photo(
        photo=photo,
        caption=f"{Emojis.BACK} <b>Действие отменено</b>\n\n"
                f"{Emojis.MAIN} Возвращаю в главное меню...",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

# Обработчик для проверки статуса флуда
@router.message(Command("status"))
async def flood_status(message: Message):
    user_id = message.from_user.id
    
    if user_id in flood_active and flood_active[user_id]:
        await message.answer(
            f"{Emojis.FLOOD} <b>Sn0s активен!</b>\n\n"
            f"У вас запущен процесс Sn0s.",
            parse_mode="HTML"
        )
    else:
        can_flood, remaining, sub_type = db.can_flood(user_id)
        
        if can_flood:
            await message.answer(
                f"{Emojis.SUCCESS} <b>Sn0s доступен!</b>\n\n"
                f"Вы можете запустить Sn0s.",
                parse_mode="HTML"
            )
        else:
            minutes = remaining // 60
            seconds = remaining % 60
            await message.answer(
                f"{Emojis.TIME} <b>Sn0s на паузе</b>\n\n"
                f"До следующего запуска: {minutes} мин {seconds} сек",
                parse_mode="HTML"
            )
