import asyncio
import aiohttp
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
    
    # @staticmethod
    # def write_proxy(proxies):
    #     try:
    #         with open(ProxyManager.proxy_file, "a+") as f:
    #             for proxy in proxies:
    #                 f.write(f"{proxy}\n")
    #     except Exception as e:
    #         print(f"Ошибка при сохранении прокси: {e}")

    @staticmethod
    def save_proxies(proxies):
        try:
            with open(ProxyManager.proxy_file, "w") as f:
                for proxy in proxies:
                    f.write(f"{proxy}\n")
        except Exception as e:
            print(f"Ошибка при сохранении прокси: {e}")

    



    # # асинхронный чекер прокси
    # @staticmethod
    # async def check_proxy(session: aiohttp.ClientSession, proxy: str, timeout=5) -> bool:
    #     try:
    #         print(f"Проверка прокси: {proxy}")  # Добавим логирование
    #         parts = proxy.split(":")
    #         if len(parts) == 2:
    #             ip, port = parts
    #             login, password = None, None
    #         elif len(parts) == 4:
    #             ip, port, login, password = parts
    #         else:
    #             return False

    #         if login and password:
    #             proxy_auth = f"{login}:{password}@"
    #         else:
    #             proxy_auth = ""

    #         if proxy.lower().startswith("socks5h://") or proxy.lower().startswith("socks5://"):
    #             scheme = "socks5"
    #             proxy_url = f"{scheme}://{proxy_auth}{ip}:{port}"
    #         else:
    #             scheme = "http"
    #             proxy_url = f"http://{proxy_auth}{ip}:{port}"

    #         async with session.get(
    #             "http://www.google.com",
    #             proxy=proxy_url,
    #             timeout=aiohttp.ClientTimeout(total=timeout)
    #         ) as response:
    #             return response.ok
    #     except Exception as e:
    #         print(f"Ошибка при проверке прокси {proxy}: {str(e)}")
    #         return False

    # @staticmethod
    # async def check_many_proxies(proxies: List[str], max_concurrent=100) -> Dict[str, bool]:
    #     results = {}
    #     connector = aiohttp.TCPConnector(limit=max_concurrent)
    #     async with aiohttp.ClientSession(connector=connector) as session:
    #         # Исправлено: передаем session и proxy для каждого вызова
    #         tasks = [ProxyManager.check_proxy(session, proxy) for proxy in proxies]
    #         results_list = await asyncio.gather(*tasks)
    #         results = dict(zip(proxies, results_list))
    #     return results









    # @staticmethod
    # async def check_proxy(proxy: str, timeout=5) -> bool:
    #     try:
    #         parts = proxy.split(":")
    #         if len(parts) == 2:
    #             ip, port = parts
    #             login, password = None, None
    #         elif len(parts) == 4:
    #             ip, port, login, password = parts
    #         else:
    #             return False

    #         if login and password:
    #             proxy_auth = f"{login}:{password}@"
    #         else:
    #             proxy_auth = ""

    #         if proxy.lower().startswith("socks5h://") or proxy.lower().startswith("socks5://"):
    #             scheme = "socks5h"
    #             proxy_url = f"{scheme}://{proxy_auth}{ip}:{port}"
    #         else:
    #             scheme = "http"
    #             proxy_url = f"http://{proxy_auth}{ip}:{port}"

    #         proxies = {
    #             "http": proxy_url,
    #             "https": proxy_url,
    #         }

    #         response = requests.get("http://www.google.com", proxies=proxies, timeout=timeout)
    #         return response.ok
    #     except Exception:
    #         return False

 

    