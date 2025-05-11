import asyncio
import aiohttp 
import requests
import re, os
from fastapi.responses import RedirectResponse
from datetime import datetime
from typing import List, Dict


PROXY_TYPES = ['http://', 'https://' 'socks4://', 'socks5://']
URL = "http://httpbin.org/ip"
TIMEOUT = 20
CONCURRENCY_LIMIT = 100

proxy_file = "app/data/proxy.txt"

# Регулярное выражение для поиска прокси
proxy_pattern_old = r'(?:socks5|https|http)://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}'
proxy_pattern = r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}'

proxy_url = ["https://github.com/monosans/proxy-list/blob/main/proxies/all.txt",
             "https://github.com/proxifly/free-proxy-list/blob/main/proxies/all/data.txt",
             "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/socks5.txt",
             "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/http.txt",
             "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/https.txt"]

class ProxyManager:
    stop_checking = False  # Флаг остановки чекера
    
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
    async def test_proxy(session, proxy, test_site, timeout, proxy_type_list):
        print(f"Получили {proxy} прокси для проверки")
        ip, port, *auth = proxy.split(':')
        for proxy_type in proxy_type_list:
            if auth:
                username, password = auth
                proxy_url = f"{proxy_type}://{username}:{password}@{ip}:{port}"
                print(f"Это {proxy_url} c авторизации")
            else:
                proxy_url = f"{proxy_type}://{ip}:{port}"
                print(f"Это {proxy_url} без авторизации")
            try:

                async with session.get(test_site, proxy = proxy_url, timeout=timeout) as response:
                    # print(proxy_url)
                    if response.status == 200:
                        print(f"{proxy_type}{ip}:{port} - {response.status}")
                        return f"{proxy_type}{ip}:{port} - {response.status}"
            except:
                continue
        print(f"{proxy_type}{ip}:{port} - не работает")
        return None

    @staticmethod
    async def check_proxies(proxies: list, test_site: str, timeout: int, concurrency_limit: int, proxy_type_list: list):
        print('Запускаем проверку прокси...')
        good_proxies = []
        semaphore = asyncio.Semaphore(concurrency_limit)
        
        async with aiohttp.ClientSession() as session:
            async def limited_check(proxy):
                async with semaphore:
                    print(f'Передаем прокси {proxy} в проверку')
                    result = await ProxyManager.test_proxy(session, proxy, test_site, timeout, proxy_type_list)
                    print(f'This - {result}')
                    if result:
                        good_proxies.append(result)

            tasks = [limited_check(proxy) for proxy in proxies]
            await asyncio.gather(*tasks)

        return good_proxies


    @staticmethod
    def clear_proxies():
        """Очищает файл с прокси"""
        with open(proxy_file, "w") as f:
            f.write("")  # Открываем файл в режиме записи, что автоматически очищает его
