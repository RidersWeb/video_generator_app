import sys
import os
import asyncio
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


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    proxies = ProxyManager.load_proxies()  # загружаем из файла
    proxy_count = len(proxies) 
    proxies_text = "\n".join(proxies)   # превращаем список в одну строку 
    return templates.TemplateResponse("index.html", {"request": request, "proxies": proxies_text, "proxy_count": proxy_count})


@app.websocket("/ws/check_proxies")
async def websocket_check_proxies(websocket: WebSocket):
    # logger.debug("WebSocket соединение установлено")
    await websocket.accept()

    proxies = ProxyManager.load_proxies()
    total = len(proxies)
    good = 0
    bad = 0

    good_proxies = []  # Сюда будем добавлять живые прокси

    proxy_queue = asyncio.Queue()

    for proxy in proxies:
        await proxy_queue.put(proxy)

    async def safe_send_json(data):
        if websocket.application_state == WebSocketState.CONNECTED:
            try:
                await websocket.send_json(data)
            except Exception as e:
                print("Ошибка отправки JSON:", e)

    async def proxy_worker():
        nonlocal good, bad, good_proxies
        while not proxy_queue.empty():
            proxy = await proxy_queue.get()
            try:
                logging.debug(f"Проверка прокси: {proxy}")
                is_alive = await ProxyManager.check_proxy(proxy)
                if is_alive:
                    good += 1
                    status = "alive"
                    good_proxies.append(proxy)  # Добавляем живой прокси в список
                else:
                    bad += 1
                    status = "dead"

                await safe_send_json({
                    "proxy": proxy,
                    "status": status,
                    "good": good,
                    "bad": bad,
                    "current": good + bad,
                    "total": total
                })

            except Exception as e:
                print(f"Ошибка при проверке прокси {proxy}: {e}")
            finally:
                proxy_queue.task_done()

    async def keep_alive():
        try:
            while True:
                if websocket.application_state != WebSocketState.CONNECTED:
                    break
                await websocket.send_json({"type": "ping"})
                await asyncio.sleep(10)
        except WebSocketDisconnect:
            print("Клиент отключился.")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print("Ошибка в keep_alive:", e)

    async def run():
        ping_task = asyncio.create_task(keep_alive())

        workers = []
        for _ in range(100):  # 20 параллельных воркеров
            worker = asyncio.create_task(proxy_worker())
            workers.append(worker)

        try:
            await asyncio.gather(*workers)
        finally:
            ping_task.cancel()
            try:
                await ping_task
            except asyncio.CancelledError:
                pass

            # Сохраняем только живые прокси в файл
            ProxyManager.save_proxies(good_proxies)

            if websocket.application_state == WebSocketState.CONNECTED:
                await websocket.close()

    await run()




@app.post("/handle_proxies")
async def handle_proxies(request: Request, proxies: str = Form(...), action: str = Form(...)):
    proxies_list = [line.strip() for line in proxies.split("\n") if line.strip()]
    if action == "save":
        proxies_list = [line.strip() for line in proxies.split("\n") if line.strip()]
        ProxyManager.save_proxies(proxies_list)
    elif action == "check":
        proxies = ProxyManager.load_proxies()
        alive, dead = ProxyManager.filter_alive_proxies(proxies)
        ProxyManager.save_proxies(alive)
        stats = {"alive": len(alive), "dead": len(dead)}
        proxies_text = "\n".join(alive)
        ProxyManager.save_proxies(alive)  # например, сохраняем только живые прокси
        return templates.TemplateResponse("index.html", {
            "request": request,
            "proxies": proxies_text,
            "stats": stats,
            "success": "Проверка завершена!"
        })
        
    return RedirectResponse("/", status_code=303)



@app.post("/save_proxies")
async def save_proxies(request: Request, proxies: str = Form(...), use_proxy: str = Form(None)):
    proxies_list = [line.strip() for line in proxies.split("\n") if line.strip()]
    ProxyManager.save_proxies(proxies_list)
    return RedirectResponse("/", status_code=303)
    # return RedirectResponse("/", status_code=303)


@app.post("/clear_proxies")
async def clear_proxies(request: Request):
    ProxyManager.clear_proxies()
    return RedirectResponse("/", status_code=303)
