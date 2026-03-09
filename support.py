from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import db
from keyboards import get_back_to_main_keyboard, get_support_keyboard, get_admin_support_keyboard
from config import SUPPORT_IMAGE, ADMIN_ID, EMOJI

router = Router()

class SupportStates(StatesGroup):
    waiting_for_problem = State()

class AdminReplyStates(StatesGroup):
    waiting_for_reply = State()

@router.callback_query(F.data == "support")
async def support_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    
    await callback.message.answer_photo(
        photo=FSInputFile(SUPPORT_IMAGE),
        caption="<b>📞 Поддержка</b>\n\n"
                "Опишите вашу проблему или вопрос.\n"
                "Мы ответим вам в ближайшее время!",
        reply_markup=get_back_to_main_keyboard(),
        parse_mode="HTML"
    )
    await callback.message.delete()
    await state.set_state(SupportStates.waiting_for_problem)
    await callback.answer()

@router.message(SupportStates.waiting_for_problem)
async def process_support_message(message: Message, state: FSMContext):
    user_id = message.from_user.id
    problem_text = message.text
    
    # Создаем тикет
    ticket_id = db.create_ticket(user_id, problem_text)
    
    # Отправляем подтверждение пользователю
    await message.answer(
        f"<b>✅ Ваше обращение принято!</b>\n\n"
        f"<b>📋 Номер обращения:</b> #{ticket_id}\n"
        f"<b>⏱ Ожидайте ответа в ближайшее время.</b>",
        reply_markup=get_back_to_main_keyboard(),
        parse_mode="HTML"
    )
    
    # Отправляем уведомление админу
    user = await message.bot.get_chat(user_id)
    username = user.username or "Нет username"
    
    await message.bot.send_message(
        ADMIN_ID,
        f"<b>📞 Новое обращение в поддержку!</b>\n\n"
        f"<b>🆔 Ticket ID:</b> #{ticket_id}\n"
        f"<b>👤 Пользователь:</b> {user.first_name}\n"
        f"<b>📱 Username:</b> @{username}\n"
        f"<b>🆔 User ID:</b> <code>{user_id}</code>\n\n"
        f"<b>📝 Сообщение:</b>\n{problem_text}",
        parse_mode="HTML"
    )
    
    await state.clear()

@router.callback_query(F.data == "admin_support")
async def admin_support(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ запрещен!", show_alert=True)
        return
    
    tickets = db.get_open_tickets()
    
    if not tickets:
        await callback.message.edit_text(
            "<b>📞 Открытых обращений нет</b>",
            reply_markup=get_back_to_main_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    for ticket in tickets[:5]:  # Показываем последние 5
        ticket_id, user_id, message_text, created_at, status, _, _ = ticket
        
        user = await callback.bot.get_chat(user_id)
        
        await callback.message.answer(
            f"<b>📋 Обращение #{ticket_id}</b>\n\n"
            f"<b>👤 Пользователь:</b> {user.first_name}\n"
            f"<b>📱 ID:</b> <code>{user_id}</code>\n"
            f"<b>⏱ Время:</b> {created_at}\n\n"
            f"<b>📝 Сообщение:</b>\n{message_text}",
            reply_markup=get_admin_support_keyboard(ticket_id),
            parse_mode="HTML"
        )
    
    await callback.message.delete()
    await callback.answer()

@router.callback_query(F.data.startswith("reply_ticket_"))
async def reply_to_ticket(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ запрещен!", show_alert=True)
        return
    
    ticket_id = int(callback.data.split("_")[2])
    await state.update_data(ticket_id=ticket_id)
    
    await callback.message.edit_text(
        f"<b>✏️ Ответ на обращение #{ticket_id}</b>\n\n"
        f"Введите ваш ответ:",
        parse_mode="HTML"
    )
    await state.set_state(AdminReplyStates.waiting_for_reply)
    await callback.answer()

@router.message(AdminReplyStates.waiting_for_reply)
async def process_admin_reply(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Доступ запрещен!")
        await state.clear()
        return
    
    data = await state.get_data()
    ticket_id = data.get('ticket_id')
    reply_text = message.text
    
    # Получаем информацию о тикете
    ticket = db.get_ticket(ticket_id)
    if not ticket:
        await message.answer("<b>❌ Тикет не найден!</b>", parse_mode="HTML")
        await state.clear()
        return
    
    user_id = ticket[1]
    
    # Сохраняем ответ
    db.reply_to_ticket(ticket_id, reply_text)
    
    # Отправляем ответ пользователю
    try:
        await message.bot.send_message(
            user_id,
            f"<b>📞 Ответ от поддержки</b>\n\n"
            f"<b>На ваше обращение #{ticket_id} получен ответ:</b>\n\n"
            f"{reply_text}",
            parse_mode="HTML"
        )
        
        await message.answer(
            f"<b>✅ Ответ отправлен пользователю!</b>",
            parse_mode="HTML"
        )
    except Exception as e:
        await message.answer(
            f"<b>❌ Не удалось отправить ответ пользователю</b>\n\n{str(e)}",
            parse_mode="HTML"
        )
    
    await state.clear()
