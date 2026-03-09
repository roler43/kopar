from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import time

from database import db
from keyboards import get_back_to_main_keyboard, get_profile_keyboard, get_admin_promo_keyboard
from emojis import Emojis
from config import ADMIN_IDS, PROMO_IMAGE

router = Router()

class PromoStates(StatesGroup):
    waiting_for_promo_code = State()
    waiting_for_promo_create_code = State()
    waiting_for_promo_create_hours = State()
    waiting_for_promo_create_uses = State()

def is_admin(user_id):
    """Проверка, является ли пользователь администратором"""
    return user_id in ADMIN_IDS

# ============= АКТИВАЦИЯ ПРОМОКОДА (ДЛЯ ПОЛЬЗОВАТЕЛЕЙ) =============

@router.callback_query(F.data == "activate_promo")
async def activate_promo_start(callback: CallbackQuery, state: FSMContext):
    """Начало активации промокода"""
    user_id = callback.from_user.id
    
    try:
        await callback.message.delete()
    except:
        pass
    
    # Отправляем картинку для промокодов
    try:
        photo = FSInputFile(PROMO_IMAGE)
        await callback.message.answer_photo(
            photo=photo,
            caption=f"{Emojis.TICKET} <b>Активация промокода</b>\n\n"
                    f"{Emojis.PHONE} Введите промокод:",
            reply_markup=get_back_to_main_keyboard(),
            parse_mode="HTML"
        )
    except:
        await callback.message.answer(
            f"{Emojis.TICKET} <b>Активация промокода</b>\n\n"
            f"{Emojis.PHONE} Введите промокод:",
            reply_markup=get_back_to_main_keyboard(),
            parse_mode="HTML"
        )
    
    await state.set_state(PromoStates.waiting_for_promo_code)
    await callback.answer()

@router.message(PromoStates.waiting_for_promo_code)
async def process_promo_code(message: Message, state: FSMContext):
    """Обработка введенного промокода"""
    user_id = message.from_user.id
    promo_code = message.text.strip().upper()
    
    # Активируем промокод
    success, result_text = db.use_promo(promo_code, user_id)
    
    if success:
        # Получаем обновленную информацию о подписке
        sub_type, sub_until = db.get_subscription_type(user_id)
        
        if sub_type != 'none' and sub_until > int(time.time()):
            if sub_type == 'forever':
                time_left = "Навсегда"
            else:
                days_left = (sub_until - int(time.time())) // 86400
                hours_left = ((sub_until - int(time.time())) % 86400) // 3600
                time_left = f"{days_left}д {hours_left}ч"
        else:
            time_left = "Нет активной подписки"
        
        await message.answer(
            f"{Emojis.SUCCESS} <b>{result_text}</b>\n\n"
            f"{Emojis.VIP} <b>Текущий статус подписки:</b> {time_left}",
            reply_markup=get_profile_keyboard(sub_type != 'none'),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            f"{Emojis.ERROR} <b>{result_text}</b>",
            reply_markup=get_profile_keyboard(False),
            parse_mode="HTML"
        )
    
    await state.clear()

# ============= УПРАВЛЕНИЕ ПРОМОКОДАМИ (ДЛЯ АДМИНОВ) =============

@router.callback_query(F.data == "admin_promos")
async def admin_promos_menu(callback: CallbackQuery):
    """Меню управления промокодами"""
    if not is_admin(callback.from_user.id):
        await callback.answer(f"{Emojis.ERROR} Доступ запрещен!", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"{Emojis.TICKET} <b>Управление промокодами</b>\n\n"
        f"{Emojis.SETTINGS} Выберите действие:",
        reply_markup=get_admin_promo_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "admin_create_promo")
async def admin_create_promo_start(callback: CallbackQuery, state: FSMContext):
    """Создание нового промокода - шаг 1: ввод кода"""
    if not is_admin(callback.from_user.id):
        await callback.answer(f"{Emojis.ERROR} Доступ запрещен!", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"{Emojis.TICKET} <b>Создание промокода</b>\n\n"
        f"{Emojis.PHONE} Введите код промокода (например: VIP2024):",
        parse_mode="HTML"
    )
    await state.set_state(PromoStates.waiting_for_promo_create_code)
    await callback.answer()

@router.message(PromoStates.waiting_for_promo_create_code)
async def admin_create_promo_code(message: Message, state: FSMContext):
    """Создание промокода - шаг 2: сохранение кода и запрос часов"""
    if not is_admin(message.from_user.id):
        await message.answer(f"{Emojis.ERROR} Доступ запрещен!")
        await state.clear()
        return
    
    promo_code = message.text.strip().upper()
    await state.update_data(promo_code=promo_code)
    
    await message.answer(
        f"{Emojis.TICKET} <b>Создание промокода</b>\n\n"
        f"{Emojis.TICKET} Код: <code>{promo_code}</code>\n\n"
        f"{Emojis.TIME} Введите количество часов подписки, которые дает промокод:",
        parse_mode="HTML"
    )
    await state.set_state(PromoStates.waiting_for_promo_create_hours)

@router.message(PromoStates.waiting_for_promo_create_hours)
async def admin_create_promo_hours(message: Message, state: FSMContext):
    """Создание промокода - шаг 3: сохранение часов и запрос лимита"""
    if not is_admin(message.from_user.id):
        await message.answer(f"{Emojis.ERROR} Доступ запрещен!")
        await state.clear()
        return
    
    try:
        hours = int(message.text.strip())
        if hours <= 0:
            raise ValueError
    except ValueError:
        await message.answer(
            f"{Emojis.ERROR} <b>Неверный формат!</b>\n\n"
            f"{Emojis.TIME} Введите положительное число часов:",
            parse_mode="HTML"
        )
        return
    
    await state.update_data(hours=hours)
    
    await message.answer(
        f"{Emojis.TICKET} <b>Создание промокода</b>\n\n"
        f"{Emojis.COUNT} Введите максимальное количество использований (0 - без лимита):",
        parse_mode="HTML"
    )
    await state.set_state(PromoStates.waiting_for_promo_create_uses)

@router.message(PromoStates.waiting_for_promo_create_uses)
async def admin_create_promo_final(message: Message, state: FSMContext):
    """Создание промокода - финальный шаг: создание"""
    if not is_admin(message.from_user.id):
        await message.answer(f"{Emojis.ERROR} Доступ запрещен!")
        await state.clear()
        return
    
    try:
        max_uses = int(message.text.strip())
        if max_uses < 0:
            raise ValueError
    except ValueError:
        await message.answer(
            f"{Emojis.ERROR} <b>Неверный формат!</b>\n\n"
            f"{Emojis.COUNT} Введите число использований (0 - без лимита):",
            parse_mode="HTML"
        )
        return
    
    data = await state.get_data()
    promo_code = data.get('promo_code')
    hours = data.get('hours')
    
    # Создаем промокод (без срока действия)
    success = db.create_promo(
        code=promo_code,
        hours=hours,
        max_uses=max_uses,
        created_by=message.from_user.id,
        expires_at=None
    )
    
    if success:
        await message.answer(
            f"{Emojis.SUCCESS} <b>Промокод успешно создан!</b>\n\n"
            f"{Emojis.TICKET} Код: <code>{promo_code}</code>\n"
            f"{Emojis.TIME} Часов: {hours}\n"
            f"{Emojis.COUNT} Лимит использований: {'∞' if max_uses == 0 else max_uses}",
            reply_markup=get_admin_promo_keyboard(),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            f"{Emojis.ERROR} <b>Промокод с таким кодом уже существует!</b>",
            reply_markup=get_admin_promo_keyboard(),
            parse_mode="HTML"
        )
    
    await state.clear()

@router.callback_query(F.data == "admin_list_promos")
async def admin_list_promos(callback: CallbackQuery):
    """Список всех промокодов"""
    if not is_admin(callback.from_user.id):
        await callback.answer(f"{Emojis.ERROR} Доступ запрещен!", show_alert=True)
        return
    
    promos = db.get_all_promos()
    
    if not promos:
        await callback.message.edit_text(
            f"{Emojis.TICKET} <b>Промокоды</b>\n\n"
            f"{Emojis.ERROR} Промокодов пока нет.",
            reply_markup=get_admin_promo_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    text = f"{Emojis.TICKET} <b>Список промокодов:</b>\n\n"
    
    for promo in promos[:10]:  # Показываем последние 10
        promo_id, code, hours, max_uses, used_count, created_by, created_at, expires_at = promo
        
        status = f"{Emojis.SUCCESS} Активен"
        if expires_at and expires_at < int(time.time()):
            status = f"{Emojis.ERROR} Истек"
        elif max_uses > 0 and used_count >= max_uses:
            status = f"{Emojis.TIME} Лимит исчерпан"
        
        from datetime import datetime
        created_date = datetime.fromtimestamp(created_at).strftime("%d.%m.%Y")
        
        text += (
            f"<b>{code}</b>\n"
            f"├ {Emojis.TIME} Часов: {hours}\n"
            f"├ {Emojis.COUNT} Использований: {used_count}/{max_uses if max_uses > 0 else '∞'}\n"
            f"├ {status}\n"
            f"└ {Emojis.DATE} Создан: {created_date}\n\n"
        )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_admin_promo_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()
