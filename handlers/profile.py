from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
import time
import re

from database import db
from keyboards import get_profile_keyboard, get_vip_keyboard, get_payment_keyboard, get_back_to_main_keyboard, get_main_keyboard
from emojis import Emojis
from payment import create_payment
from config import PROFILE_IMAGE, VIP_IMAGE, BOT_USERNAME  # Добавлен VIP_IMAGE

router = Router()

def clean_emoji_text(text):
    """Очищает текст от тегов кастомных эмодзи если они вызывают ошибку"""
    pattern = r'<tg-emoji[^>]*>(.*?)</tg-emoji>'
    return re.sub(pattern, r'\1', text)

@router.callback_query(F.data == "profile")
async def profile_command(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    
    user_id = callback.from_user.id
    user_data = db.get_user(user_id)
    
    if not user_data:
        photo = FSInputFile(PROFILE_IMAGE)
        await callback.message.answer_photo(
            photo=photo,
            caption=f"{Emojis.ERROR} <b>Профиль не найден!</b>",
            reply_markup=get_main_keyboard(),
            parse_mode="HTML"
        )
        try:
            await callback.message.delete()
        except:
            pass
        await callback.answer()
        return
    
    # Распаковываем данные пользователя (14 полей)
    (user_id, username, first_name, last_name, 
     joined_date, last_flood, floods_count, is_admin, is_banned, 
     sub_type, sub_until, total_payments, free_trial_used, name_checked) = user_data
    
    joined_date_str = time.strftime("%d.%m.%Y %H:%M", time.localtime(joined_date))
    
    can_flood, remaining, current_sub = db.can_flood(user_id)
    
    # Формируем текст профиля
    profile_lines = []
    
    # Заголовок
    profile_lines.append(f"{Emojis.PROFILE} <b>Ваш профиль</b>\n")
    
    # Основная информация
    profile_lines.append(f"{Emojis.ID} <b>ID:</b> <code>{user_id}</code>")
    profile_lines.append(f"{Emojis.PROFILE} <b>Имя:</b> {first_name or 'Не указано'}")
    if username:
        profile_lines.append(f"{Emojis.PHONE} <b>Никнейм:</b> @{username}")
    profile_lines.append(f"{Emojis.DATE} <b>Регистрация:</b> {joined_date_str}")
    profile_lines.append(f"{Emojis.COUNT} <b>Флудов запущено:</b> {floods_count}\n")
    
    # Информация о подписке
    if current_sub == 'forever':
        profile_lines.append(f"{Emojis.VIP} <b>Статус:</b> Навсегда")
        profile_lines.append(f"{Emojis.START} <b>Кулдаун:</b> Без кулдауна")
    elif current_sub == 'trial':
        if sub_until > int(time.time()):
            hours_left = (sub_until - int(time.time())) // 3600
            minutes_left = ((sub_until - int(time.time())) % 3600) // 60
            profile_lines.append(f"{Emojis.VIP} <b>Статус:</b> Триал (осталось {hours_left}ч {minutes_left}мин)")
        else:
            profile_lines.append(f"{Emojis.PROFILE} <b>Статус:</b> Триал истек")
        profile_lines.append(f"{Emojis.TIME} <b>Кулдаун:</b> 1 минута")
    elif current_sub in ['1day', '7days', '30days']:
        if sub_until > int(time.time()):
            days_left = (sub_until - int(time.time())) // 86400
            hours_left = ((sub_until - int(time.time())) % 86400) // 3600
            sub_names = {'1day': '1 день', '7days': '7 дней', '30days': '30 дней'}
            profile_lines.append(f"{Emojis.VIP} <b>Статус:</b> {sub_names[current_sub]} (осталось {days_left}д {hours_left}ч)")
        else:
            profile_lines.append(f"{Emojis.PROFILE} <b>Статус:</b> {sub_names[current_sub]} истекла")
        profile_lines.append(f"{Emojis.TIME} <b>Кулдаун:</b> 1 минута")
    else:
        profile_lines.append(f"{Emojis.PROFILE} <b>Статус:</b> Обычный")
        profile_lines.append(f"{Emojis.TIME} <b>Кулдаун:</b> 5 минут")
    
    # Следующий флуд
    if not can_flood:
        minutes = remaining // 60
        seconds = remaining % 60
        profile_lines.append(f"{Emojis.COOLDOWN} <b>Следующий флуд:</b> через {minutes} мин {seconds} сек")
    else:
        profile_lines.append(f"{Emojis.SUCCESS} <b>Следующий флуд:</b> Доступен")
    
    # Дополнительная информация
    if total_payments > 0:
        profile_lines.append(f"\n{Emojis.MONEY} <b>Всего потрачено:</b> ${total_payments:.2f}")
    
    if is_admin:
        profile_lines.append(f"\n{Emojis.ADMIN} <b>Администратор</b>")
    
    if free_trial_used:
        profile_lines.append(f"\n{Emojis.VIP} <b>Бесплатный триал:</b> Использован")
    
    profile_text = "\n".join(profile_lines)
    
    try:
        await callback.message.delete()
    except:
        pass
    
    try:
        # Отправляем картинку профиля с текстом
        photo = FSInputFile(PROFILE_IMAGE)
        await callback.message.answer_photo(
            photo=photo,
            caption=profile_text,
            reply_markup=get_profile_keyboard(current_sub != 'none'),
            parse_mode="HTML"
        )
    except TelegramBadRequest as e:
        error_text = str(e)
        print(f"Ошибка в профиле: {error_text}")
        
        if "DOCUMENT_INVALID" in error_text:
            # Если ошибка с эмодзи, отправляем без тегов
            clean_text = clean_emoji_text(profile_text)
            photo = FSInputFile(PROFILE_IMAGE)
            await callback.message.answer_photo(
                photo=photo,
                caption=f"⚠️ <b>Проблема с кастомными эмодзи</b>\n\n{clean_text}",
                reply_markup=get_profile_keyboard(current_sub != 'none'),
                parse_mode="HTML"
            )
        else:
            # Если другая ошибка
            await callback.message.answer(
                f"❌ <b>Ошибка:</b>\n{error_text}",
                reply_markup=get_back_to_main_keyboard(),
                parse_mode="HTML"
            )
    
    await callback.answer()

@router.callback_query(F.data == "back_to_profile")
async def back_to_profile(callback: CallbackQuery, state: FSMContext):
    await profile_command(callback, state)

@router.callback_query(F.data == "buy_vip")
async def buy_vip(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except:
        pass
    
    vip_text = (
        f"{Emojis.VIP} <b>Выберите VIP подписку:</b>\n\n"
        f"<b>VIP преимущества:</b>\n"
        f"{Emojis.TIME} • Кулдаун 1 минута вместо 5\n"
        f"{Emojis.START} • Увеличенная скорость\n"
        f"{Emojis.SUPPORT} • Приоритетная поддержка\n\n"
        f"{Emojis.VIP} <b>Forever VIP:</b>\n"
        f"{Emojis.START} • Без кулдауна вообще\n"
        f"{Emojis.START} • Максимальная скорость\n"
        f"{Emojis.VIP} • Эксклюзивный доступ"
    )
    
    # Отправляем картинку VIP
    try:
        photo = FSInputFile(VIP_IMAGE)
        await callback.message.answer_photo(
            photo=photo,
            caption=vip_text,
            reply_markup=get_vip_keyboard(),
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Ошибка отправки VIP картинки: {e}")
        # Если ошибка с картинкой, отправляем без неё
        await callback.message.answer(
            vip_text,
            reply_markup=get_vip_keyboard(),
            parse_mode="HTML"
        )
    await callback.answer()

@router.callback_query(F.data.startswith("buy_"))
async def process_buy(callback: CallbackQuery):
    sub_type = callback.data.replace("buy_", "")
    user_id = callback.from_user.id
    
    sub_names = {
        '1day': '1 день',
        '7days': '7 дней',
        '30days': '30 дней',
        'forever': 'Навсегда'
    }
    
    result = await create_payment(user_id, sub_type)
    
    try:
        await callback.message.delete()
    except:
        pass
    
    if result['success']:
        payment_text = (
            f"{Emojis.CRYPTO} <b>Оплата подписки {sub_names[sub_type]}</b>\n\n"
            f"{Emojis.MONEY} <b>Сумма:</b> ${result['amount']} {result['currency']}\n\n"
            f"Нажмите кнопку ниже для оплаты через CryptoBot"
        )
        
        # Отправляем картинку VIP
        try:
            photo = FSInputFile(VIP_IMAGE)
            await callback.message.answer_photo(
                photo=photo,
                caption=payment_text,
                reply_markup=get_payment_keyboard(result['pay_url']),
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"Ошибка отправки VIP картинки: {e}")
            await callback.message.answer(
                payment_text,
                reply_markup=get_payment_keyboard(result['pay_url']),
                parse_mode="HTML"
            )
    else:
        error_text = f"{Emojis.ERROR} <b>Ошибка создания платежа</b>\n\n{result['error']}"
        
        await callback.message.answer(
            error_text,
            reply_markup=get_back_to_main_keyboard(),
            parse_mode="HTML"
        )
    
    await callback.answer()
