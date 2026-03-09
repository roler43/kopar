from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from database import db
from keyboards import get_main_keyboard, get_subscription_keyboard
from config import CHANNEL_USERNAME, MENU_IMAGE, BOT_USERNAME, CHANNEL_LINK
from emojis import Emojis

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    first_name = message.from_user.first_name or ""
    username = message.from_user.username or ""
    last_name = message.from_user.last_name or ""
    
    # Получаем текущие данные пользователя
    user_data = db.get_user(user_id)
    
    if user_data:
        # Если пользователь существует, обновляем его имя (оно могло измениться)
        db.update_user_name(user_id, first_name)
    else:
        # Если пользователь новый, добавляем его
        db.add_user(user_id, username, first_name, last_name)
    
    await state.clear()
    
    # Проверяем наличие бота в ИМЕНИ (first_name)
    has_bot_in_name = first_name and BOT_USERNAME in first_name
    print(f"Проверка имени: {first_name}, содержит {BOT_USERNAME}: {has_bot_in_name}")
    
    # Проверяем подписку на канал
    try:
        chat_member = await message.bot.get_chat_member(
            chat_id=f"@{CHANNEL_USERNAME}",
            user_id=user_id
        )
        is_subscribed = chat_member.status not in ['left', 'kicked']
        print(f"Подписка на канал: {is_subscribed}")
        
        if is_subscribed and has_bot_in_name:
            # Если выполнены оба условия - показываем главное меню
            photo = FSInputFile(MENU_IMAGE)
            await message.answer_photo(
                photo=photo,
                caption=f"{Emojis.MAIN} <b>Добро пожаловать, {first_name}!</b>\n\n"
                        f"{Emojis.SUCCESS} Вы подписаны на канал\n"
                        f"{Emojis.SUCCESS} <code>@{BOT_USERNAME}</code> в вашем имени\n\n"
                        f"{Emojis.VIP} <b>Вы получили 3 часа бесплатной подписки!</b>\n\n"
                        f"{Emojis.START} Выберите действие в меню:",
                reply_markup=get_main_keyboard(),
                parse_mode="HTML"
            )
        elif is_subscribed and not has_bot_in_name:
            # Подписан на канал, но нет бота в имени
            await message.answer(
                f"{Emojis.CHANNEL} <b>Добро пожаловать!</b>\n\n"
                f"{Emojis.SUCCESS} Вы подписаны на канал\n\n"
                f"{Emojis.ERROR} <b>Для получения доступа добавьте бота в имя:</b>\n"
                f"<code>@{BOT_USERNAME}</code> (нажмите чтобы скопировать)\n\n"
                f"{Emojis.SETTINGS} <b>Как это сделать:</b>\n"
                f"1. Откройте настройки Telegram\n"
                f"2. Нажмите на своё имя\n"
                f"3. В поле «Имя» добавьте <code>@{BOT_USERNAME}</code> в начало или конец\n"
                f"4. Сохраните и нажмите /start\n\n"
                f"{Emojis.REPLY} Например: <code>@{BOT_USERNAME} Вадим</code> или <code>Вадим @{BOT_USERNAME}</code>",
                reply_markup=None,
                parse_mode="HTML"
            )
        elif not is_subscribed and has_bot_in_name:
            # Есть бот в имени, но нет подписки на канал
            await message.answer(
                f"{Emojis.CHANNEL} <b>Добро пожаловать!</b>\n\n"
                f"{Emojis.SUCCESS} <code>@{BOT_USERNAME}</code> в вашем имени\n\n"
                f"{Emojis.ERROR} <b>Для получения доступа подпишитесь на канал:</b>\n"
                f"{CHANNEL_LINK}\n\n"
                f"{Emojis.REPLY} После подписки нажмите кнопку ниже:",
                reply_markup=get_subscription_keyboard(),
                parse_mode="HTML"
            )
        else:
            # Нет ни одного условия
            await message.answer(
                f"{Emojis.CHANNEL} <b>Добро пожаловать!</b>\n\n"
                f"{Emojis.ERROR} <b>Для использования бота необходимо:</b>\n\n"
                f"{Emojis.CHANNEL} 1️⃣ Подписаться на канал:\n{CHANNEL_LINK}\n\n"
                f"{Emojis.PROFILE} 2️⃣ Добавить бота в имя:\n"
                f"<code>@{BOT_USERNAME}</code> (нажмите чтобы скопировать)\n\n"
                f"{Emojis.SETTINGS} <b>Как добавить в имя:</b>\n"
                f"• Настройки → Имя → добавить <code>@{BOT_USERNAME}</code>\n"
                f"• Например: <code>{BOT_USERNAME} Вадим</code>\n\n"
                f"{Emojis.START} После выполнения условий нажмите /start",
                reply_markup=None,
                parse_mode="HTML"
            )
    except Exception as e:
        print(f"Ошибка проверки: {e}")
        await message.answer(
            f"{Emojis.CHANNEL} <b>Добро пожаловать!</b>\n\n"
            f"{Emojis.ERROR} <b>Для использования бота необходимо:</b>\n\n"
            f"{Emojis.CHANNEL} 1️⃣ Подписаться на канал:\n{CHANNEL_LINK}\n\n"
            f"{Emojis.PROFILE} 2️⃣ Добавить бота в имя:\n"
            f"<code>@{BOT_USERNAME}</code> (нажмите чтобы скопировать)\n\n"
            f"{Emojis.SETTINGS} <b>Как добавить в имя:</b>\n"
            f"• Настройки → Имя → добавить <code>@{BOT_USERNAME}</code>\n"
            f"• Например: <code>{BOT_USERNAME} Вадим</code>\n\n"
            f"{Emojis.START} После выполнения условий нажмите /start",
            reply_markup=None,
            parse_mode="HTML"
        )

@router.callback_query(F.data == "check_sub")
async def check_subscription(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = db.get_user(user_id)
    
    # Получаем актуальное имя из Telegram
    try:
        user = await callback.bot.get_chat(user_id)
        current_first_name = user.first_name or ""
        
        # Обновляем имя в базе
        db.update_user_name(user_id, current_first_name)
    except:
        current_first_name = user_data[2] if user_data else ""
    
    print(f"Проверка подписки: имя={current_first_name}")
    
    try:
        chat_member = await callback.bot.get_chat_member(
            chat_id=f"@{CHANNEL_USERNAME}",
            user_id=user_id
        )
        
        is_subscribed = chat_member.status not in ['left', 'kicked']
        has_bot_in_name = current_first_name and BOT_USERNAME in current_first_name
        
        print(f"Результат: подписка={is_subscribed}, бот в имени={has_bot_in_name}")
        
        if is_subscribed:
            # Если подписался на канал
            if has_bot_in_name:
                # Если ещё и бот в имени есть - всё хорошо
                try:
                    await callback.message.delete()
                except:
                    pass
                
                photo = FSInputFile(MENU_IMAGE)
                await callback.message.answer_photo(
                    photo=photo,
                    caption=f"{Emojis.SUCCESS} <b>Все условия выполнены!</b>\n\n"
                            f"{Emojis.VIP} Вы получили 3 часа бесплатной подписки!\n\n"
                            f"{Emojis.START} Добро пожаловать в главное меню.",
                    reply_markup=get_main_keyboard(),
                    parse_mode="HTML"
                )
            else:
                # Подписался, но бота в имени нет
                await callback.message.edit_text(
                    f"{Emojis.CHANNEL} <b>Подписка подтверждена!</b>\n\n"
                    f"{Emojis.SUCCESS} Вы подписаны на канал\n\n"
                    f"{Emojis.ERROR} <b>Осталось добавить бота в имя:</b>\n"
                    f"<code>@{BOT_USERNAME}</code> (нажмите чтобы скопировать)\n\n"
                    f"{Emojis.SETTINGS} <b>Как это сделать:</b>\n"
                    f"1. Откройте настройки Telegram\n"
                    f"2. Нажмите на своё имя\n"
                    f"3. В поле «Имя» добавьте <code>@{BOT_USERNAME}</code>\n"
                    f"4. Сохраните и нажмите /start\n\n"
                    f"{Emojis.REPLY} Например: <code>{BOT_USERNAME} Вадим</code>",
                    parse_mode="HTML"
                )
        else:
            # Не подписался на канал
            await callback.answer(
                f"{Emojis.ERROR} Вы не подписаны на канал!",
                show_alert=True
            )
    except Exception as e:
        print(f"Ошибка при проверке: {e}")
        await callback.answer(
            f"{Emojis.ERROR} Ошибка при проверке подписки!",
            show_alert=True
        )
    
    await callback.answer()

@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id
    user_data = db.get_user(user_id)
    first_name = user_data[2] if user_data else "Пользователь"
    
    try:
        await callback.message.delete()
    except:
        pass
    
    photo = FSInputFile(MENU_IMAGE)
    await callback.message.answer_photo(
        photo=photo,
        caption=f"{Emojis.MAIN} <b>Главное меню</b>\n\n"
                f"Выберите действие:",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )
    
    # Важно! Отвечаем на callback
    await callback.answer()
