import sys
import os
import asyncio
import aiohttp
from aiohttp_socks import ProxyConnector
sys.path.append(os.path.dirname(__file__))
from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from services.proxy_manager import ProxyManager
from fastapi.responses import HTMLResponse
from starlette.websockets import WebSocketState
from fastapi import WebSocket, WebSocketDisconnect
from fake_useragent import UserAgent


import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

CONCURRENCY_LIMIT = 100


app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Главнаая страница
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    proxies = ProxyManager.load_proxies()
    proxy_count = len(proxies) 
    proxies_text = "\n".join(proxies)   # превращаем список в одну строку
    return templates.TemplateResponse("index.html", {"request": request, "proxies": proxies_text, "proxy_count": proxy_count})

# Парсинг прокси
@app.websocket("/ws/parse_proxies")
async def websocket_parse_proxies(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket connection established for parsing proxies")
    # Получаем данные от клиента
    data = await websocket.receive_json()
    count_proxe_find = int(data.get("countproxy"))
    type_proxy_find = data.get("typeproxyfind")

    new_proxy = list(ProxyManager.find_proxy(type_proxy_find, count_proxe_find))
    await websocket.send_json({
        "proxies": new_proxy
    })
    ProxyManager.save_proxies(new_proxy)


@app.websocket("/ws/save_proxies")
async def save_proxys(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket connection established for checking proxies")
    # Получаем данные от клиента
    data = await websocket.receive_json()
    proxies = data.get("proxies")
    list(proxies)
    print(type(proxies))
    ProxyManager.save_proxies(proxies)
    # Проверяем прокси
    # alive, dead = ProxyManager.filter_alive_proxies(proxies)
    # Отправляем ответ клиенту
    proxies = ProxyManager.load_proxies()
    proxy_count = len(proxies) 
    proxies_text = "\n".join(proxies) 

    await websocket.send_json({
        "proxy_count": proxy_count,
        "proxies_text": proxies_text
    })

@app.websocket("/ws/check_proxies")
async def websocket_check_proxies(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket connection established")
    


    # Получаем данные от клиента
    data = await websocket.receive_json()

    proxies = ProxyManager.load_proxies()
    test_site = data.get("site")
    int_timeout = int(data.get("intTimeout"))
    concurrency_limit = int(data.get("concurrencyLimit"))
    type_proxy_check = data.get("typeproxy")
    proxies = proxies[:1000]
    total = len(proxies)
    print(f"Total proxies to check: {total} using site: {test_site}, timeout: {int_timeout}s, and concurrency limit: {concurrency_limit}")

    print('Все данные получены начинаем проверять')    
    semaphore = asyncio.Semaphore(concurrency_limit)

    async def check_proxy(proxy):
        ua = UserAgent()
        headers = {
            "User-Agent": ua.random
        }
        async with semaphore:
            parts = proxy.strip().split(":")
            if len(parts) == 2:
                ip, port = parts
                auth = False
            elif len(parts) == 4:
                ip, port, user, password = parts
                auth = True
            else:
                # print(f"❌ Неверный формат прокси: {proxy}")
                return proxy, None, False

            for proxy_type in type_proxy_check:  # Перебираем все выбранные типы
                try:
                    if auth:
                        proxy_url = f"{proxy_type}://{user}:{password}@{ip}:{port}"
                    else:
                        proxy_url = f"{proxy_type}://{ip}:{port}"

                    connector = ProxyConnector.from_url(proxy_url)

                    async with aiohttp.ClientSession(
                        connector=connector,
                        timeout=aiohttp.ClientTimeout(total=int_timeout)
                    ) as session:
                        async with session.get(test_site, headers=headers) as resp:
                            if resp.status == 200:
                                proxy = proxy_url
                                print(f'✅ Прокся {proxy} работает - {headers}')
                                return proxy, proxy_type, True

                except Exception as e:
                    # Не печатаем ошибку для каждой попытки — только если все неудачные
                    continue
            proxyEr = proxy_url
            print(f'❌ Прокся {proxyEr} не работает - {headers}')
            return proxyEr, None, False


    tasks = [check_proxy(proxy) for proxy in proxies]
    good = 0
    bad = 0
    good_proxies = []

    for i, future in enumerate(asyncio.as_completed(tasks)):
        proxy, proxy_type, is_working = await future
        current = i + 1

        if is_working:
            good += 1
            good_proxies.append(proxy)
            await websocket.send_json({
                "status": "alive",
                "type": proxy_type,
                "proxy": proxy,
                "current": current,
                "total": total,
                "good": good,
                "checked": good + bad,
                "bad": bad
            })
        else:
            bad += 1
            await websocket.send_json({
                "status": "dead",
                "proxy": proxy,
                "current": current,
                "total": total,
                "good": good,
                "checked": good + bad,
                "bad": bad
            })

    await websocket.send_json({
        "action": "complete",
        "total": total,
        "good": good,
        "bad": bad,
        "checked": good + bad,
        "good_proxies": good_proxies
    })


@app.post("/clear")
async def clear_proxies():
    ProxyManager.clear_proxies()
    # return {"status": "cleared"}