import json, os, yt_dlp, time
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from fastapi import FastAPI, Request, APIRouter, Query
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.responses import FileResponse

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl, validator, constr

from fake_useragent import UserAgent


from uuid import uuid4
from pathlib import Path


proxy = ""

ua = UserAgent()
headers = {
    'User-Agent': ua.chrome  # или ua.random, если хочешь рандомно из всех браузеров
}

DOWNLOAD_FOLDER = "app/downloads"
Path(DOWNLOAD_FOLDER).mkdir(exist_ok=True)

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")
router.mount("/static", StaticFiles(directory="app/static"), name="static")


# 👇 Модель для получения JSON с клиента
class VideoRequest(BaseModel):
    video_id: str

# 👇 POST-запрос, который принимает JSON
@router.post("/youtube/embed", response_class=HTMLResponse)
async def embed_youtube(request: Request, data: VideoRequest):
    print('Данные получены' + data.video_id)
    video_id = data.video_id
    url = f"https://www.youtube.com/watch?v={video_id}"
    info = extract_video_info(url)

    formats = info.get("formats")
    
    print('Отпровляем данные обратно на клиента')
    return templates.TemplateResponse("youtube.html", {
        "request": request,
        "video_id": video_id,
        "title": info.get("title"),
        "subscriber_count": info.get("uploader_subscriber_count"),
        "uploader": info.get("uploader"),
        "uploader_url": info.get("uploader_url"),
        "like_count": info.get("like_count"),
        "dislike_count": info.get("dislike_count"),
        "view_count": info.get("view_count"),
        "comment_count": info.get("comment_count"),
        "thumbnail": info.get("thumbnail"),
        "webpage_url": info.get("webpage_url"),
        "duration": info.get("duration"),
        "description": info.get("description"),
        "upload_date": info.get("upload_date"),
        # "video_url": video_url,
        # "audio_url": audio_url
    })



@router.get("/youtube/download")
async def download_youtube(
    video_url: str,
    media_type: str = "video",
    retry: int = 3  # Количество попыток переподключения
):
    ydl_opts = {
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(title)s.%(ext)s",
        "retries": retry,
        "fragment_retries": retry,
        "skip_unavailable_fragments": True,
        "http_chunk_size": 1048576 * 5,  # 5MB chunks вместо 1MB
        "concurrent_fragment_downloads": 4,  # Параллельная загрузка фрагментов
        "retries": 10,
        "fragment_retries": 10,
        "extractor_args": {
            "youtube": {
                "skip": ["hls", "dash"]  # Пропускаем сложные форматы
            }
        },
        "proxy": proxy,  # если нужен
        "http_headers": headers,   # Укажите ваш прокси
        "socket_timeout": 30,
        "noprogress": True
    }

    if media_type == "audio":
        ydl_opts.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
            }],
        })
    else:
        ydl_opts.update({
            "format": "bestvideo[height<=720]+bestaudio/best",
        })

    try:
        for attempt in range(retry):
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(video_url, download=True)
                    filename = ydl.prepare_filename(info)
                    
                    if media_type == "audio":
                        filename = filename.split('.')[0] + '.mp3'

                    if not os.path.exists(filename):
                        continue  # Повторяем попытку

                    return FileResponse(
                        filename,
                        media_type="audio/mpeg" if media_type == "audio" else "video/mp4",
                        filename=os.path.basename(filename)
                    )

            except (yt_dlp.utils.DownloadError, ConnectionError) as e:
                if attempt == retry - 1:
                    raise
                time.sleep(5)  # Ждем перед повторной попыткой

        raise HTTPException(400, "Не удалось скачать после нескольких попыток")

    except Exception as e:
        raise HTTPException(400, detail=f"Ошибка: {str(e)}")



# 👇 Функция для получения данных через yt_dlp
def extract_video_info(url: str) -> dict:
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "extract_flat": False,
        "proxy": proxy,  # если нужен
        "http_headers": headers,  # ← добавляем User-Agent
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info


def download_media(url: str, media_type: str = "video"):
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
    }

    if media_type == "audio":
        ydl_opts.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
            "outtmpl": "%(title)s.%(ext)s",
        })
    else:  # video
        ydl_opts.update({
            "format": "bestvideo+bestaudio/best",
            "outtmpl": "%(title)s.%(ext)s",
        })

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            if media_type == "audio":
                filename = filename.rsplit(".", 1)[0] + ".mp3"
            
            return filename
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/download")
async def download(url: str, media_type: str = "video"):
    try:
        filename = download_media(url, media_type)
        return {"status": "success", "filename": filename}
    except Exception as e:
        return {"status": "error", "message": str(e)}