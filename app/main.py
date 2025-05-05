import sys
import os
import asyncio
import aiohttp
sys.path.append(os.path.dirname(__file__))
from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from services.proxy_manager import ProxyManager
from fastapi.responses import HTMLResponse
from starlette.websockets import WebSocketState
from fastapi import WebSocket, WebSocketDisconnect

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

CONCURRENCY_LIMIT = 100
PROXY_TYPES = ['http', 'socks4', 'socks5']
TIMEOUT = 20

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    proxies = ProxyManager.load_proxies()
    proxy_count = len(proxies) 
    proxies_text = "\n".join(proxies)   # превращаем список в одну строку
    return templates.TemplateResponse("index.html", {"request": request, "proxies": proxies_text, "proxy_count": proxy_count})

# @app.post("/check-proxies", response_class=HTMLResponse)
# async def check_proxies(
#     request: Request,
#     test_site: str = Form(...),
#     proxy_types: list = Form(...),
#     timeout: int = Form(...),
#     proxies: str = Form(...)):
#     print(f"Received form data: {proxies}")


@app.websocket("/ws/check_proxies")
async def websocket_check_proxies(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket connection established")

    # Получаем начальные данные от клиента
    # init_data = await websocket.receive_json()
    # print(f"Received initial data: {init_data}")


    # Получаем настройки от клиента
    # init_data = await websocket.receive_json()
    # settings = init_data['settings']
    # proxies = init_data['proxies']
    # print(f"Settings: {settings}")
    # Настройки проверки
    # CONCURRENCY_LIMIT = settings.get('concurrencyLimit', 100)
    # print(f"CONCURRENCY_LIMIT: {CONCURRENCY_LIMIT}")
    # TIMEOUT = settings.get('timeout', 5)
    # print(f"TIMEOUT: {TIMEOUT}")
    # PROXY_TYPES = settings.get('proxyTypes', ['http'])
    # print(f"PROXY_TYPES: {PROXY_TYPES}")

    test_site = websocket.query_params.get("site")

    proxies = ProxyManager.load_proxies()
    total = len(proxies)
    
    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)

    def _get_url(test_site):
        sites = {
            "google": "https://www.google.com",
            "httpbin": "https://httpbin.org/ip",
            "yandex": "https://yandex.ru",
        }
        return sites.get(test_site)
        
    async with aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(force_close=True, limit=0),
        timeout=aiohttp.ClientTimeout(total=10)
    ) as session:
        
        async def check_proxy(proxy):
            async with semaphore:
                try:
                    # Обработка прокси с авторизацией (новый код)
                    if proxy.count(':') >= 3:  # Формат ip:port:login:pass
                        ip_port, login, password = proxy.rsplit(':', 2)
                        proxy_auth = f"{login}:{password}@"
                    else:
                        ip_port = proxy
                        proxy_auth = ""
                    
                    for proxy_type in PROXY_TYPES:
                        try:
                            async with session.get(
                                _get_url(test_site),
                                # Модифицированная строка прокси:
                                # 
                                proxy=f"http://{proxy_auth}{ip_port}",
                                timeout=TIMEOUT
                            ) as resp:
                                if resp.status == 200:
                                    return proxy, proxy_type, True
                        except:
                            continue
                    return proxy, None, False
                except Exception:
                    return proxy, None, False

        tasks = [check_proxy(proxy) for proxy in proxies]
        good = 0
        bad = 0
        checked = 0
        good_proxies = []
        
        for i, future in enumerate(asyncio.as_completed(tasks)):
            proxy, proxy_type, is_working = await future
            current = i + 1
            
            if is_working:
                good += 1
                # Сохраняем в оригинальном формате (с авторизацией если была)
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
        "checked": checked,
        "good_proxies": good_proxies
        
    })

    ProxyManager.save_proxies(good_proxies)
    ProxyManager.load_proxies()




async def check_proxy(session, proxy, test_site):
    """Вспомогательная функция для проверки одного прокси"""
    proxy_type = await ProxyManager.check_proxy_type(session, proxy, test_site=test_site)
    is_working = proxy_type is not None
    return (proxy_type, proxy, is_working) if is_working else (None, proxy, False)



@app.post("/save_proxies")
async def save_proxies(request: Request, proxies: str = Form(...), use_proxy: str = Form(None)):
    proxies_list = [line.strip() for line in proxies.split("\n") if line.strip()]
    ProxyManager.save_proxies(proxies_list)
    return RedirectResponse("/", status_code=303)


@app.post("/clear_proxies")
async def clear_proxies(request: Request):
    ProxyManager.clear_proxies()
    return RedirectResponse("/", status_code=303)



# @app.post("/handle_proxies")
# async def handle_proxies(request: Request, proxies: str = Form(...), action: str = Form(...)):
#     proxies_list = [line.strip() for line in proxies.split("\n") if line.strip()]
#     if action == "save":
#         proxies_list = [line.strip() for line in proxies.split("\n") if line.strip()]
#         ProxyManager.save_proxies(proxies_list)
#     elif action == "check":
#         proxies = ProxyManager.load_proxies()
#         alive, dead = ProxyManager.filter_alive_proxies(proxies)
#         ProxyManager.save_proxies(alive)
#         stats = {"alive": len(alive), "dead": len(dead)}
#         proxies_text = "\n".join(alive)
#         ProxyManager.save_proxies(alive)  # например, сохраняем только живые прокси
#         return templates.TemplateResponse("index.html", {
#             "request": request,
#             "proxies": proxies_text,
#             "stats": stats,
#             "success": "Проверка завершена!"
#         })
        
#     return RedirectResponse("/", status_code=303)