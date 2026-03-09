from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import db
from keyboards import get_back_to_main_keyboard, get_main_keyboard, get_admin_support_keyboard
from config import ADMIN_IDS, SUPPORT_IMAGE
from emojis import Emojis

router = Router()

class SupportStates(StatesGroup):
    waiting_for_problem = State()

class AdminReplyStates(StatesGroup):
    waiting_for_reply = State()

def is_admin(user_id):
    """Проверка, является ли пользователь администратором"""
    return user_id in ADMIN_IDS

@router.callback_query(F.data == "support")
async def support_menu(callback: CallbackQuery, state: FSMContext):
    """Меню поддержки для пользователей"""
    await state.clear()
    
    try:
        await callback.message.delete()
    except:
        pass
    
    # Отправляем картинку поддержки
    photo = FSInputFile(SUPPORT_IMAGE)
    await callback.message.answer_photo(
        photo=photo,
        caption=f"{Emojis.SUPPORT} <b>Поддержка</b>\n\n"
                f"Опишите вашу проблему или вопрос.\n"
                f"Мы ответим вам в ближайшее время!",
        reply_markup=get_back_to_main_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(SupportStates.waiting_for_problem)
    await callback.answer()

@router.message(SupportStates.waiting_for_problem)
async def process_support_message(message: Message, state: FSMContext):
    """Обработка сообщения от пользователя в поддержку"""
    user_id = message.from_user.id
    problem_text = message.text
    
    # Создаем тикет в базе данных
    ticket_id = db.create_ticket(user_id, problem_text)
    
    # Отправляем подтверждение пользователю с картинкой
    photo = FSInputFile(SUPPORT_IMAGE)
    await message.answer_photo(
        photo=photo,
        caption=f"{Emojis.SUCCESS} <b>Ваше обращение принято!</b>\n\n"
                f"{Emojis.TICKET} <b>Номер обращения:</b> #{ticket_id}\n"
                f"{Emojis.TIME} <b>Ожидайте ответа в ближайшее время.</b>",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )
    
    # Отправляем уведомление всем администраторам
    try:
        user = await message.bot.get_chat(user_id)
        username = user.username or "Нет username"
        first_name = user.first_name or "Не указано"
        
        for admin_id in ADMIN_IDS:
            try:
                await message.bot.send_message(
                    admin_id,
                    f"{Emojis.SUPPORT} <b>Новое обращение в поддержку!</b>\n\n"
                    f"{Emojis.TICKET} <b>Ticket ID:</b> #{ticket_id}\n"
                    f"{Emojis.PROFILE} <b>Пользователь:</b> {first_name}\n"
                    f"{Emojis.PHONE} <b>Username:</b> @{username}\n"
                    f"{Emojis.ID} <b>User ID:</b> <code>{user_id}</code>\n\n"
                    f"<b>📝 Сообщение:</b>\n{problem_text}",
                    parse_mode="HTML"
                )
            except Exception as e:
                print(f"Ошибка отправки уведомления админу {admin_id}: {e}")
                continue
    except Exception as e:
        print(f"Ошибка получения информации о пользователе: {e}")
    
    await state.clear()

@router.callback_query(F.data == "admin_support")
async def admin_support(callback: CallbackQuery):
    """Просмотр открытых обращений для админа"""
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
    
    for ticket in tickets[:5]:  # Показываем последние 5 тикетов
        ticket_id, user_id, message_text, created_at, status, _, _ = ticket
        
        try:
            user = await callback.bot.get_chat(user_id)
            user_name = user.first_name or "Не указано"
            username = f"@{user.username}" if user.username else "Нет username"
        except:
            user_name = "Неизвестно"
            username = "Неизвестно"
        
        # Форматируем время
        from datetime import datetime
        created_date = datetime.fromtimestamp(created_at).strftime("%d.%m.%Y %H:%M")
        
        await callback.message.answer(
            f"{Emojis.TICKET} <b>Обращение #{ticket_id}</b>\n\n"
            f"{Emojis.PROFILE} <b>Пользователь:</b> {user_name}\n"
            f"{Emojis.PHONE} <b>Username:</b> {username}\n"
            f"{Emojis.ID} <b>ID:</b> <code>{user_id}</code>\n"
            f"{Emojis.DATE} <b>Время:</b> {created_date}\n\n"
            f"<b>📝 Сообщение:</b>\n{message_text}",
            reply_markup=get_admin_support_keyboard(ticket_id),
            parse_mode="HTML"
        )
    
    await callback.answer()

@router.callback_query(F.data.startswith("reply_ticket_"))
async def reply_to_ticket(callback: CallbackQuery, state: FSMContext):
    """Ответ на конкретный тикет"""
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
    """Обработка ответа админа на тикет"""
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
    
    # Сохраняем ответ в базе данных
    db.reply_to_ticket(ticket_id, reply_text)
    
    # Отправляем ответ пользователю
    try:
        await message.bot.send_message(
            user_id,
            f"{Emojis.SUPPORT} <b>Ответ от поддержки</b>\n\n"
            f"<b>На ваше обращение #{ticket_id} получен ответ:</b>\n\n"
            f"{reply_text}",
            parse_mode="HTML"
        )
        
        await message.answer(
            f"{Emojis.SUCCESS} <b>Ответ отправлен пользователю!</b>\n\n"
            f"Тикет #{ticket_id} закрыт.",
            parse_mode="HTML"
        )
    except Exception as e:
        await message.answer(
            f"{Emojis.ERROR} <b>Не удалось отправить ответ пользователю</b>\n\n{str(e)}",
            parse_mode="HTML"
        )
    
    await state.clear()
