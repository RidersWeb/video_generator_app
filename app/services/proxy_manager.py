import asyncio
import aiohttp
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


    # @staticmethod
    # async def check_proxy_fast(session, proxy, timeout=10):
    #     try:
    #         # Пытаемся подключиться к Google через прокси
    #         async with session.get(
    #             # "https://www.google.com",
    #             'https://httpbin.org/ip',
    #             proxy=f'http://{proxy}',
    #             timeout=aiohttp.ClientTimeout(total=timeout)
    #         ) as response:
    #             # Если статус ответа 200 (OK), значит прокси рабочий
    #             if response.status == 200:
    #                 return True
    #             else:
    #                 return False
    #     except Exception:  # Если ошибка (нет соединения, таймаут и т. д.)
    #         return False



    @staticmethod
    async def check_proxy_type(session, proxy, timeout=10, test_site="httpbin"):
        # Выбираем тестовый URL
        test_url = "https://www.google.com" if test_site == "google" else "https://httpbin.org/ip"
        
        # Пробуем все типы прокси
        for proxy_type in ["http", "https", "socks5"]:
            try:
                async with session.get(
                    test_url,
                    proxy=f"{proxy_type}://{proxy}",
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    if response.status == 200:
                        return proxy_type  # Возвращаем тип работающего прокси
            except:
                continue
        
        return None  # Прокси не рабочий ни в одном типе


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

 

    