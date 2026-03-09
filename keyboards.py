from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import CHANNEL_LINK
from emojis import Emojis

def get_main_keyboard():
    """Главное меню с кастомными эмодзи"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Sn0s",
            callback_data="flood_menu",
            icon_custom_emoji_id=Emojis.FLOOD_ID
        ),
        InlineKeyboardButton(
            text="Профиль", 
            callback_data="profile",
            icon_custom_emoji_id=Emojis.PROFILE_ID
        ),
        width=2
    )
    builder.row(
        InlineKeyboardButton(
            text="Поддержка", 
            callback_data="support",
            icon_custom_emoji_id=Emojis.SUPPORT_ID
        ),
        InlineKeyboardButton(
            text="Канал", 
            url=CHANNEL_LINK,
            icon_custom_emoji_id=Emojis.CHANNEL_ID
        ),
        width=2
    )
    return builder.as_markup()

def get_subscription_keyboard():
    """Клавиатура для проверки подписки"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Подписаться на канал", 
            url=CHANNEL_LINK,
            icon_custom_emoji_id=Emojis.CHANNEL_ID
        ),
        width=1
    )
    builder.row(
        InlineKeyboardButton(
            text="Я подписался", 
            callback_data="check_sub",
            icon_custom_emoji_id=Emojis.SUCCESS_ID
        ),
        width=1
    )
    return builder.as_markup()

def get_snos_type_keyboard():
    """Клавиатура выбора типа сноса"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="По номеру телефона", 
            callback_data="snos_phone",
            icon_custom_emoji_id=Emojis.PHONE_ID
        ),
        width=1
    )
    builder.row(
        InlineKeyboardButton(
            text="По юзернейму", 
            callback_data="snos_username",
            icon_custom_emoji_id=Emojis.PROFILE_ID
        ),
        width=1
    )
    builder.row(
        InlineKeyboardButton(
            text="Назад", 
            callback_data="back_to_main",
            icon_custom_emoji_id=Emojis.BACK_ID
        ),
        width=1
    )
    return builder.as_markup()

def get_flood_confirm_keyboard():
    """Подтверждение флуда"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Да, запустить", 
            callback_data="flood_confirm",
            icon_custom_emoji_id=Emojis.START_ID
        ),
        InlineKeyboardButton(
            text="Нет, отмена", 
            callback_data="flood_cancel",
            icon_custom_emoji_id=Emojis.ERROR_ID
        ),
        width=2
    )
    return builder.as_markup()

def get_flood_stop_keyboard():
    """Кнопка остановки флуда"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="⏹ Остановить", 
            callback_data="flood_stop"
        ),
        width=1
    )
    return builder.as_markup()

def get_back_to_main_keyboard():
    """Кнопка назад в главное меню"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Назад", 
            callback_data="back_to_main",
            icon_custom_emoji_id=Emojis.BACK_ID
        ),
        width=1
    )
    return builder.as_markup()

def get_profile_keyboard(has_vip=False):
    """Клавиатура профиля"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Активировать промокод", 
            callback_data="activate_promo"
        ),
        width=1
    )
    if not has_vip:
        builder.row(
            InlineKeyboardButton(
                text="Купить VIP", 
                callback_data="buy_vip",
                icon_custom_emoji_id=Emojis.VIP_ID
            ),
            width=1
        )
    builder.row(
        InlineKeyboardButton(
            text="Назад", 
            callback_data="back_to_main",
            icon_custom_emoji_id=Emojis.BACK_ID
        ),
        width=1
    )
    return builder.as_markup()

def get_vip_keyboard():
    """Клавиатура покупки VIP"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="1 день - 0.10$", 
            callback_data="buy_1day",
            icon_custom_emoji_id=Emojis.VIP_ID
        ),
        InlineKeyboardButton(
            text="7 дней - 1.00$", 
            callback_data="buy_7days",
            icon_custom_emoji_id=Emojis.VIP_ID
        ),
        width=2
    )
    builder.row(
        InlineKeyboardButton(
            text="30 дней - 4.00$", 
            callback_data="buy_30days",
            icon_custom_emoji_id=Emojis.VIP_ID
        ),
        InlineKeyboardButton(
            text="Навсегда - 8.00$", 
            callback_data="buy_forever",
            icon_custom_emoji_id=Emojis.VIP_ID
        ),
        width=2
    )
    builder.row(
        InlineKeyboardButton(
            text="Назад", 
            callback_data="back_to_profile",
            icon_custom_emoji_id=Emojis.BACK_ID
        ),
        width=1
    )
    return builder.as_markup()

def get_payment_keyboard(pay_url: str):
    """Клавиатура для оплаты"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Оплатить", 
            url=pay_url,
            icon_custom_emoji_id=Emojis.CRYPTO_ID
        ),
        width=1
    )
    builder.row(
        InlineKeyboardButton(
            text="Проверить оплату", 
            callback_data="check_payment",
            icon_custom_emoji_id=Emojis.SUCCESS_ID
        ),
        InlineKeyboardButton(
            text="Отмена", 
            callback_data="back_to_profile",
            icon_custom_emoji_id=Emojis.ERROR_ID
        ),
        width=2
    )
    return builder.as_markup()

def get_admin_keyboard():
    """Админ-панель"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Статистика", 
            callback_data="admin_stats",
            icon_custom_emoji_id=Emojis.STATS_ID
        ),
        InlineKeyboardButton(
            text="Управление подписками", 
            callback_data="admin_manage_subscriptions",
            icon_custom_emoji_id=Emojis.VIP_ID
        ),
        width=2
    )
    builder.row(
        InlineKeyboardButton(
            text="Промокоды",
            callback_data="admin_promos",
            icon_custom_emoji_id=Emojis.TICKET_ID
        ),
        InlineKeyboardButton(
            text="Проверка сессий",
            callback_data="admin_check_sessions",
            icon_custom_emoji_id=Emojis.PROXY_ID
        ),
        width=2
    )
    builder.row(
        InlineKeyboardButton(
            text="Настройки прокси", 
            callback_data="admin_proxy_settings",
            icon_custom_emoji_id=Emojis.SETTINGS_ID
        ),
        InlineKeyboardButton(
            text="Проверить прокси", 
            callback_data="admin_check_proxies",
            icon_custom_emoji_id=Emojis.PROXY_ID
        ),
        width=2
    )
    builder.row(
        InlineKeyboardButton(
            text="Рассылка", 
            callback_data="admin_mailing",
            icon_custom_emoji_id=Emojis.MAIL_ID
        ),
        InlineKeyboardButton(
            text="Поддержка", 
            callback_data="admin_support",
            icon_custom_emoji_id=Emojis.SUPPORT_ID
        ),
        width=2
    )
    builder.row(
        InlineKeyboardButton(
            text="Назад", 
            callback_data="back_to_main",
            icon_custom_emoji_id=Emojis.BACK_ID
        ),
        width=1
    )
    return builder.as_markup()

def get_admin_subscription_keyboard():
    """Клавиатура управления подписками"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Выдать подписку", 
            callback_data="admin_give_subscription",
            icon_custom_emoji_id=Emojis.SUCCESS_ID
        ),
        width=1
    )
    builder.row(
        InlineKeyboardButton(
            text="Забрать подписку", 
            callback_data="admin_remove_subscription",
            icon_custom_emoji_id=Emojis.ERROR_ID
        ),
        width=1
    )
    builder.row(
        InlineKeyboardButton(
            text="Проверить подписку", 
            callback_data="admin_check_subscription",
            icon_custom_emoji_id=Emojis.STATS_ID
        ),
        width=1
    )
    builder.row(
        InlineKeyboardButton(
            text="Назад", 
            callback_data="back_to_admin",
            icon_custom_emoji_id=Emojis.BACK_ID
        ),
        width=1
    )
    return builder.as_markup()

def get_admin_promo_keyboard():
    """Клавиатура управления промокодами"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="➕ Создать промокод", 
            callback_data="admin_create_promo"
        ),
        width=1
    )
    builder.row(
        InlineKeyboardButton(
            text="📋 Список промокодов", 
            callback_data="admin_list_promos"
        ),
        width=1
    )
    builder.row(
        InlineKeyboardButton(
            text="Назад", 
            callback_data="back_to_admin",
            icon_custom_emoji_id=Emojis.BACK_ID
        ),
        width=1
    )
    return builder.as_markup()

def get_proxy_settings_keyboard():
    """Клавиатура настроек прокси"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Включить", 
            callback_data="proxy_on",
            icon_custom_emoji_id=Emojis.UNLOCK_ID
        ),
        InlineKeyboardButton(
            text="Отключить", 
            callback_data="proxy_off",
            icon_custom_emoji_id=Emojis.LOCK_ID
        ),
        width=2
    )
    builder.row(
        InlineKeyboardButton(
            text="Назад", 
            callback_data="back_to_admin",
            icon_custom_emoji_id=Emojis.BACK_ID
        ),
        width=1
    )
    return builder.as_markup()

def get_admin_support_keyboard(ticket_id: int):
    """Клавиатура для ответа на тикет"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Ответить", 
            callback_data=f"reply_ticket_{ticket_id}",
            icon_custom_emoji_id=Emojis.REPLY_ID
        ),
        width=1
    )
    builder.row(
        InlineKeyboardButton(
            text="Назад", 
            callback_data="admin_support",
            icon_custom_emoji_id=Emojis.BACK_ID
        ),
        width=1
    )
    return builder.as_markup()
