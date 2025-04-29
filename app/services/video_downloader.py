import yt_dlp
import os
from typing import Optional
from app.services.proxy_manager import ProxyManager


class VideoDownloader:
    def __init__(self, use_proxy: bool = False, download_path: str = "downloads"):
        self.download_path = download_path
        self.use_proxy = use_proxy
        os.makedirs(self.download_path, exist_ok=True)

    def download_video(self, url: str) -> str:
        proxy = ProxyManager.get_random_proxy() if self.use_proxy else None

        ydl_opts = {
            "outtmpl": os.path.join(self.download_path, "%(title)s.%(ext)s"),
            "proxy": f"http://{proxy}" if proxy else None,
            "nocheckcertificate": True,
            "quiet": False,
            "noplaylist": True,
            "skip_download": False,
            "merge_output_format": "mp4",
            "postprocessors": [
                {
                    "key": "FFmpegVideoConvertor",
                    "preferedformat": "mp4",
                }
            ],
            "cookiefile": None,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_filename = ydl.prepare_filename(info)
            return video_filename
