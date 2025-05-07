import asyncio
import aiohttp
import requests
import re
from fastapi.responses import RedirectResponse
from datetime import datetime
from typing import List, Dict

# import re
# import httpx
# import requests

class ProxyManager:

    proxy_file = "app/data/proxy.txt"
    stop_checking = False  # Флаг остановки чекера
    

    @staticmethod
    def load_proxies():
        try:
            with open(ProxyManager.proxy_file, "r") as f:
                proxies = [line.strip() for line in f if line.strip()]
            return proxies
        except FileNotFoundError:
            return []

            
    @staticmethod
    # принимает site, type_proxy_find, count_proxe_find и возвращает список прокси
    def find_proxy(type_proxy_find, count_proxe_find):
        proxy_url = "https://github.com/monosans/proxy-list/blob/main/proxies/all.txt"
        
        try:
            response = requests.get(proxy_url)
            response.raise_for_status()  # Проверяем на ошибки HTTP
            # print(response.text)
            
            # Регулярное выражение для поиска прокси
            proxy_pattern = r'(?:socks5|socks4|http)://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}'
            
            # Находим все совпадения
            proxies = re.findall(proxy_pattern, response.text)
            print(type_proxy_find)
            print(count_proxe_find)
            proxies = [proxy for proxy in proxies if proxy.split("://")[0] == type_proxy_find]
            # print(proxies)
            return proxies
        
        except Exception as e:
            print(f"Ошибка при получении прокси: {e}")
            return []
           


    @staticmethod
    def clear_proxies():
        open(ProxyManager.proxy_file, "w").close()


    @staticmethod
    async def filter_alive_proxies(proxies):
        alive = []
        dead = []

        for proxy in proxies:
            if ProxyManager.stop_checking:
                break  # Если нажали "Стоп", выйти из проверки

            if await ProxyManager.check_proxy(proxy):
                alive.append(proxy)
            else:
                dead.append(proxy)
        return alive, dead
    
    @staticmethod
    def save_proxies(proxies):
        try:
            with open(ProxyManager.proxy_file, "w") as f:
                for proxy in proxies:
                    f.write(f"{proxy}\n")
        except Exception as e:
            print(f"Ошибка при сохранении прокси: {e}")