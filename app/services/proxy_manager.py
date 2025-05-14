import asyncio
import aiohttp 
import requests
import re, os
from fastapi.responses import RedirectResponse
from datetime import datetime
from typing import List, Dict
from fake_useragent import UserAgent
from aiohttp_socks import ProxyConnector


PROXY_TYPES = ['http://', 'https://' 'socks4://', 'socks5://']
URL = "http://httpbin.org/ip"
TIMEOUT = 20
CONCURRENCY_LIMIT = 100

data_dir = "app/data/"
proxy_file = f"{data_dir}proxy.txt"

# Регулярное выражение для поиска прокси
proxy_pattern_old = r'(?:socks5|https|http)://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}'
proxy_pattern = r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}'

proxy_url = ["https://github.com/monosans/proxy-list/blob/main/proxies/all.txt",
             "https://github.com/proxifly/free-proxy-list/blob/main/proxies/all/data.txt",
             "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/socks5.txt",
             "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/http.txt",
             "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/https.txt"]

class ProxyManager:

    stop_flag = False  # Флаг для остановки процесса

    @staticmethod
    def stop():
        ProxyManager.stop_flag = True

    @staticmethod
    def reset():
        ProxyManager.stop_flag = False
    
    @staticmethod
    def save_proxies(proxies):
        try:
            with open(proxy_file, "w") as f:
                for proxy in proxies:
                    f.write(f"{proxy}\n")
        except Exception as e:
            print(f"Ошибка при сохранении прокси: {e}")
        finally:
            return RedirectResponse(url="/", status_code=303)
    

    @staticmethod
    def load_proxies():   
        try:
            with open(proxy_file, "r") as f:
                proxies = [line.strip() for line in f if line.strip()]
            return proxies
        except FileNotFoundError:
            return []

            
    @staticmethod
    # принимает site, type_proxy_find, count_proxe_find и возвращает список прокси
    def find_proxy(type_proxy_find, count_proxe_find, proxy_url=proxy_url, proxy_pattern=proxy_pattern):
        all_proxy = []
        for url in proxy_url:
            try:
                response = requests.get(url, timeout=20)
                proxies = re.findall(proxy_pattern, response.text)
                for proxy  in proxies:
                    all_proxy.append(proxy) 
            except Exception as e:
                return []
        # ProxyManager.save_proxies(all_proxy)
        return all_proxy




    @staticmethod
    async def check_proxy(proxy, test_site, timeout, type_proxy, semaphore):
        async with semaphore:
            if ProxyManager.stop_flag:
                return proxy, None, False, None

            types_to_try = []

            if type_proxy == "all":
                types_to_try = ["http", "https", "socks5"]
            else:
                types_to_try = [type_proxy]

            parts = proxy.strip().split(":")
            if len(parts) == 2:
                ip, port = parts
                auth = None
            elif len(parts) == 4:
                ip, port, user, password = parts
                auth = (user, password)
            else:
                print(f"❌ Неверный формат: {proxy}")
                return proxy, None, False, None

            for proxy_type in types_to_try:
                try:
                    if auth:
                        proxy_url = f"{proxy_type}://{auth[0]}:{auth[1]}@{ip}:{port}"
                    else:
                        proxy_url = f"{proxy_type}://{ip}:{port}"

                    connector = ProxyConnector.from_url(proxy_url)

                    ua = UserAgent()
                    user_agent = ua.random
                    headers = {"User-Agent": user_agent}

                    async with aiohttp.ClientSession(
                        connector=connector,
                        timeout=aiohttp.ClientTimeout(total=timeout),
                        headers=headers
                    ) as session:
                        async with session.get(test_site) as resp:
                            if resp.status == 200:
                                print(f"✅ Прокси работает: {proxy_url} - {user_agent}")
                                return proxy_url, proxy_type, True, user_agent

                except Exception as e:
                    # Просто переходим к следующему типу
                    continue

            # Если ни один тип не сработал
            print(f"❌ Прокси не работает: {proxy_type}://{proxy}")
            return proxy, None, False, None


    @staticmethod
    async def check_proxies_via_websocket(websocket, proxies, test_site, timeout, concurrency, type_proxy, live_limit):

        semaphore = asyncio.Semaphore(concurrency)
        total = len(proxies)
        good = 0
        bad = 0
        good_proxies = []

        tasks = [
            ProxyManager.check_proxy(proxy, test_site, timeout, type_proxy, semaphore)
            for proxy in proxies
        ]
        for i, future in enumerate(asyncio.as_completed(tasks)):

            proxy_url, proxy_type, is_alive, user_agent = await future
            current = i + 1

            if is_alive:
                good += 1
                good_proxies.append(proxy_url)
                await websocket.send_json({
                    "status": "alive",
                    "type": proxy_type,
                    "proxy": proxy_url,
                    "user_agent": user_agent,
                    "current": current,
                    "total": total,
                    "good": good,
                    "bad": bad,
                    "checked": good + bad,
                })
            # 🛑 Остановить, если достигли лимита
            else:
                bad += 1
                await websocket.send_json({
                    "status": "dead",
                    "proxy": proxy_url,
                    "current": current,
                    "total": total,
                    "good": good,
                    "bad": bad,
                    "checked": good + bad,
                })

        await websocket.send_json({
            "action": "complete",
            "total": total,
            "good": good,
            "bad": bad,
            "checked": good + bad,
            "good_proxies": good_proxies,
        })
        if good_proxies:
            filename = f"{data_dir}{type_proxy}.proxy.txt"
            with open(filename, "w") as f:
                for p in good_proxies:
                    f.write(p + "\n")
            print(f"✅ Сохранено {len(good_proxies)} живых прокси в {filename}")








   
    @staticmethod
    def clear_proxies():
        """Очищает файл с прокси"""
        with open(proxy_file, "w") as f:
            f.write("")  # Открываем файл в режиме записи, что автоматически очищает его
