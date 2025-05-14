import sys
import os

sys.path.append(os.path.dirname(__file__))
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from services.proxy_manager import ProxyManager
from fastapi.responses import HTMLResponse
from fastapi import WebSocket
from services.youtube import router as youtube_router


import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

CONCURRENCY_LIMIT = 100


app = FastAPI()
app.include_router(youtube_router)


templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Главнаая страница
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    proxies = ProxyManager.load_proxies()
    proxy_count = len(proxies) 
    proxies_text = "\n".join(proxies)   # превращаем список в одну строку
    return templates.TemplateResponse("index.html", {"request": request, "proxies": proxies_text, "proxy_count": proxy_count})


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

    proxies = ProxyManager.load_proxies()
    proxy_count = len(proxies) 
    proxies_text = "\n".join(proxies) 

    await websocket.send_json({
        "proxy_count": proxy_count,
        "proxies_text": proxies_text
    })


# Парсинг прокси
@app.websocket("/ws/parse_proxies")
async def websocket_parse_proxies(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket connection established for parsing proxies")
    # Получаем данные от клиента
    data = await websocket.receive_json()
    count_proxe_find = int(data.get("countproxy"))
    type_proxy_find = data.get("typeproxyfind")

    proxies = list(ProxyManager.find_proxy(type_proxy_find, count_proxe_find))
    print(f'Всего - {len(proxies)} шт')
    new_proxy = list(set(proxies)) # Оставляем только уникальные
    print(f'Уникальных - {len(new_proxy)} шт')
    await websocket.send_json({
        "proxies": new_proxy
    })
    ProxyManager.save_proxies(new_proxy)




@app.websocket("/ws/check_proxies")
async def websocket_check_proxies(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_json()

        print(f'Получены данные: {data}')

        # Если это не "stop", значит это параметры для запуска
        test_site = data.get("site", "https://httpbin.org/ip")
        timeout = int(data.get("intTimeout", 10))
        concurrency = int(data.get("concurrencyLimit", 100))
        type_proxy = data.get("typeproxy", "http")
        live_limit = int(data.get("liveLimit", 1))
        proxyLimit = int(data.get("proxyLimit"))
        


        proxies = ProxyManager.load_proxies() if proxyLimit == 0 else ProxyManager.load_proxies()[:proxyLimit]

        print(f'Ищем {live_limit} прокси, среди {len(proxies)} штук')

        print(f'Все данные получены. Проверяем {len(proxies)} прокси...')
        await ProxyManager.check_proxies_via_websocket(
            websocket=websocket,
            proxies=proxies,
            test_site=test_site,
            timeout=timeout,
            concurrency=concurrency,
            type_proxy=type_proxy,
            live_limit=live_limit
        )






@app.post("/clear")
async def clear_proxies():
    ProxyManager.clear_proxies()
    # return {"status": "cleared"}