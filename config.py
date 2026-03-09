# Telegram API для сессий (получи на my.telegram.org)
API_ID = 123456  # Замените на свой API ID
API_HASH = "your_api_hash_here"  # Замените на свой API Hash


BOT_TOKEN = "8645912199:AAFOsXUnbwAdsgQkw-bAcKxSS17pekUr1HY"

# CryptoPay токен (получи у @CryptoBot)
CRYPTO_TOKEN = "325700:AALNFUIWSG7u3zlAnmZwu6KcYrVXiZw6wWF"

# ID администраторов (можно добавить несколько через запятую)
ADMIN_IDS = [6945488830, 2046759833]  # Замени на свои Telegram ID

# Имя бота для проверки в нике
BOT_USERNAME = "vexorsesiabot"  # Без @

# Канал для подписки
CHANNEL_USERNAME = "channel_Milana_star"
CHANNEL_LINK = "https://t.me/channel_Milana_star"

# Настройки флуда
FLOOD_DURATION = 600  # 10 минут в секундах
FLOOD_COOLDOWN = 300  # 5 минут кулдауна для обычных пользователей
VIP_FLOOD_COOLDOWN = 60  # 1 минута кулдауна для VIP
NO_COOLDOWN = 0  # Без кулдауна для Forever VIP

# Настройки подписок (цены в USD)
PRICES = {
    '1day': 0.10,    # 10 центов
    '7days': 1.00,   # 1 доллар
    '30days': 4.00,  # 4 доллара
    'forever': 8.00  # 8 долларов навсегда
}

# Длительность подписок в днях
SUBSCRIPTION_DURATION = {
    '1day': 1,
    '7days': 7,
    '30days': 30,
    'forever': 36500  # ~100 лет
}

# Бесплатная подписка за выполнение условий (в часах)
FREE_TRIAL_HOURS = 3

# Файлы с прокси
PROXIES_FILE = "data/proxies.txt"
WORKING_PROXIES_FILE = "data/working_proxies.txt"
BAD_PROXIES_FILE = "data/bad_proxies.txt"

# База данных
DB_FILE = "data/users.db"

# Настройки прокси
USE_PROXY = True

# Пути к картинкам
MENU_IMAGE = "menu.png"
SNOS_IMAGE = "snos.png"
PROFILE_IMAGE = "profile.png"
SUPPORT_IMAGE = "support.png"
VIP_IMAGE = "vip.png"
PROMO_IMAGE = "promo.png"  # Добавьте картинку для промокодов
