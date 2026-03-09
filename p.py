#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import asyncio
import random
import string
from telethon import TelegramClient
from telethon.tl.functions.channels import CreateChannelRequest
from telethon.tl.functions.messages import CreateChatRequest
from telethon.errors import FloodWaitError
import time

# Настройки (можно вынести в config.py)
API_ID = 123456  # Замените на свой API ID
API_HASH = "your_api_hash_here"  # Замените на свой API Hash

# Количество каналов и чатов для создания
CHANNELS_COUNT = 5
CHATS_COUNT = 5

# Папка с сессиями
SESSIONS_DIR = "sessions"

# Слова для генерации названий
ADJECTIVES = [
    "Awesome", "Beautiful", "Cool", "Dark", "Epic", "Fantastic", "Golden", "Happy",
    "Incredible", "Joyful", "Kind", "Legendary", "Magical", "Nice", "Orange", "Purple",
    "Quantum", "Royal", "Super", "Turbo", "Ultra", "Vibrant", "Wild", "Xtra", "Young", "Zesty"
]

NOUNS = [
    "Animals", "Bots", "Cats", "Dogs", "Eagles", "Foxes", "Games", "Hawks",
    "Insects", "Jaguars", "Koalas", "Lions", "Monkeys", "Nights", "Owls",
    "Pandas", "Quails", "Rabbits", "Snakes", "Tigers", "Unicorns", "Vipers",
    "Wolves", "Xerus", "Yaks", "Zebras"
]

def random_string(length=8):
    """Генерация случайной строки"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def random_username():
    """Генерация случайного юзернейма"""
    return f"test_{random_string(10)}"

def random_title():
    """Генерация случайного названия"""
    adj = random.choice(ADJECTIVES)
    noun = random.choice(NOUNS)
    num = random.randint(1, 999)
    return f"{adj} {noun} {num}"

def find_sessions():
    """Поиск всех сессий в директории sessions"""
    session_files = []
    
    if not os.path.exists(SESSIONS_DIR):
        os.makedirs(SESSIONS_DIR)
        print(f"📁 Создана папка {SESSIONS_DIR}")
        return []
    
    for file in os.listdir(SESSIONS_DIR):
        if file.endswith('.session'):
            session_path = os.path.join(SESSIONS_DIR, file[:-8])  # Убираем .session
            session_files.append(session_path)
    
    return session_files

async def create_channel(client, session_name):
    """Создание канала"""
    title = random_title()
    username = random_username()
    
    try:
        result = await client(CreateChannelRequest(
            title=title,
            about=f"Test channel created by script - {random_string(10)}",
            megagroup=False  # False для канала, True для супергруппы
        ))
        
        # Пытаемся установить юзернейм
        try:
            from telethon.tl.functions.channels import UpdateUsernameRequest
            await client(UpdateUsernameRequest(result.chats[0], username))
            username_set = f"@{username}"
        except:
            username_set = "❌ Не удалось установить username"
        
        print(f"  ✅ Канал: {title} | {username_set}")
        return True, title, username_set
    except FloodWaitError as e:
        print(f"  ⏳ Flood wait {e.seconds} секунд")
        await asyncio.sleep(e.seconds)
        return False, None, None
    except Exception as e:
        print(f"  ❌ Ошибка создания канала: {e}")
        return False, None, None

async def create_chat(client, session_name):
    """Создание чата (группы)"""
    title = random_title()
    
    try:
        # Создаем чат с собой
        me = await client.get_me()
        result = await client(CreateChatRequest(
            users=[me],
            title=title
        ))
        
        print(f"  ✅ Чат: {title}")
        return True, title
    except FloodWaitError as e:
        print(f"  ⏳ Flood wait {e.seconds} секунд")
        await asyncio.sleep(e.seconds)
        return False, None
    except Exception as e:
        print(f"  ❌ Ошибка создания чата: {e}")
        return False, None

async def process_session(session_path):
    """Обработка одной сессии"""
    session_name = os.path.basename(session_path)
    print(f"\n{'='*60}")
    print(f"📱 Сессия: {session_name}")
    print(f"{'='*60}")
    
    client = TelegramClient(session_path, API_ID, API_HASH)
    
    try:
        await client.connect()
        
        if not await client.is_user_authorized():
            print(f"❌ Сессия {session_name} не авторизована")
            return
        
        me = await client.get_me()
        print(f"👤 Владелец: {me.first_name} (@{me.username})" if me.username else f"👤 Владелец: {me.first_name}")
        
        # Создаем каналы
        print(f"\n📢 Создание {CHANNELS_COUNT} каналов...")
        channels_created = 0
        for i in range(CHANNELS_COUNT):
            print(f"  {i+1}. ", end="")
            success, title, username = await create_channel(client, session_name)
            if success:
                channels_created += 1
            await asyncio.sleep(2)  # Задержка между созданием
        
        # Создаем чаты
        print(f"\n💬 Создание {CHATS_COUNT} чатов...")
        chats_created = 0
        for i in range(CHATS_COUNT):
            print(f"  {i+1}. ", end="")
            success, title = await create_chat(client, session_name)
            if success:
                chats_created += 1
            await asyncio.sleep(2)  # Задержка между созданием
        
        print(f"\n📊 Итоги для сессии {session_name}:")
        print(f"  ✅ Каналов создано: {channels_created}/{CHANNELS_COUNT}")
        print(f"  ✅ Чатов создано: {chats_created}/{CHATS_COUNT}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        await client.disconnect()

async def main():
    print("="*60)
    print("🚀 СКРИПТ СОЗДАНИЯ ТЕСТОВЫХ КАНАЛОВ И ЧАТОВ")
    print("="*60)
    print(f"\n📊 Настройки:")
    print(f"  • Каналов на сессию: {CHANNELS_COUNT}")
    print(f"  • Чатов на сессию: {CHATS_COUNT}")
    print(f"  • Папка сессий: {SESSIONS_DIR}/")
    
    # Поиск сессий
    sessions = find_sessions()
    
    if not sessions:
        print(f"\n❌ Нет файлов сессий в папке {SESSIONS_DIR}/")
        print(f"\n📌 Инструкция:")
        print(f"  1. Положите .session файлы в папку {SESSIONS_DIR}/")
        print(f"  2. Убедитесь что в config.py указаны правильные API_ID и API_HASH")
        print(f"  3. Запустите скрипт снова")
        return
    
    print(f"\n🔍 Найдено сессий: {len(sessions)}")
    
    # Подтверждение
    print(f"\n⚠️ Будет создано:")
    total_channels = len(sessions) * CHANNELS_COUNT
    total_chats = len(sessions) * CHATS_COUNT
    print(f"  • Каналов: {total_channels}")
    print(f"  • Чатов: {total_chats}")
    print(f"  • Всего: {total_channels + total_chats}")
    
    response = input("\nПродолжить? (y/n): ").lower()
    if response != 'y':
        print("❌ Отменено")
        return
    
    # Обработка каждой сессии
    start_time = time.time()
    
    for session_path in sessions:
        await process_session(session_path)
        await asyncio.sleep(5)  # Задержка между сессиями
    
    elapsed_time = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"✅ ГОТОВО! Время выполнения: {elapsed_time:.1f} секунд")
    print(f"{'='*60}")

if __name__ == "__main__":
    asyncio.run(main())
