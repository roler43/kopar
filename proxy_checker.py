import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from config import PROXIES_FILE, WORKING_PROXIES_FILE, BAD_PROXIES_FILE

def load_proxies():
    try:
        with open(PROXIES_FILE, 'r', encoding='utf-8') as f:
            proxies = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        return proxies
    except FileNotFoundError:
        return []

def save_proxies(working, bad):
    with open(WORKING_PROXIES_FILE, 'w', encoding='utf-8') as f:
        f.write("# Рабочие прокси\n")
        for proxy in working:
            f.write(f"{proxy}\n")
    
    with open(BAD_PROXIES_FILE, 'w', encoding='utf-8') as f:
        f.write("# Нерабочие прокси\n")
        for proxy in bad:
            f.write(f"{proxy}\n")

def check_proxy(proxy):
    proxies = {
        'http': f'http://{proxy}',
        'https': f'http://{proxy}'
    }
    try:
        response = requests.get('http://httpbin.org/ip', proxies=proxies, timeout=10)
        if response.status_code == 200:
            return proxy, True
    except:
        pass
    return proxy, False

def check_all_proxies():
    proxies = load_proxies()
    if not proxies:
        return [], []
    
    working = []
    bad = []
    
    with ThreadPoolExecutor(max_workers=50) as executor:
        future_to_proxy = {executor.submit(check_proxy, proxy): proxy for proxy in proxies}
        for future in as_completed(future_to_proxy):
            proxy, is_working = future.result()
            if is_working:
                working.append(proxy)
            else:
                bad.append(proxy)
    
    save_proxies(working, bad)
    return working, bad
