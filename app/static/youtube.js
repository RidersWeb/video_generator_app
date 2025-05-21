// // // youtube.js
// const input = document.getElementById('videoLink');

// input.addEventListener('keydown', async function(e) {
//     if (e.key === 'Enter') {
//         console.log(input)
//         await loadYouTubePage(input);
//     }
// });

async function loadYouTubePage(input) {
    const videoId = extractYouTubeId(input.value);
    
    if (!videoId) {
        alert("Пожалуйста, введите корректную ссылку на YouTube");
        return;
    }
    showLoader();
    try {
        const response = await fetch('/youtube/embed', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ video_id: videoId})
        });
        if (!response.ok) throw new Error("Ошибка загрузки видео");
        
        const html = await response.text();
        console.log('Данные получили...')
        document.getElementById('youtbehome').innerHTML = html;
        
        // После загрузки HTML показываем видео-контейнер
        const videoContainer = document.querySelector('.ratio.ratio-16x9');
        if (videoContainer) {
            videoContainer.style.display = 'block';
        }
    hideLoader();
    } catch (error) {
        console.error("Ошибка:", error);
        alert("Не удалось загрузить видео");
    }
}

function extractYouTubeId(url) {
    const regExp = /^.*(youtu\.be\/|youtube\.com\/(?:shorts\/|embed\/|v\/|watch\?v=|watch\?.+&v=))([^#&?]*).*/;
    const match = url.match(regExp);
    return (match && match[2].length === 11) ? match[2] : null;
}

function showLoader() {
    document.getElementById("loader").style.display = "flex";
    document.getElementById("youtbehome").style.display = "none";
}

function hideLoader() {
    document.getElementById("loader").style.display = "none";
    document.getElementById("youtbehome").style.display = "block";
}







async function downloadMedia(url, mediaType) {
    if (!url) {
        alert("Введите URL видео!");
        return;
    }

    const progressContainer = document.getElementById('progress-container');
    const progressBar = document.getElementById('download-progress');
    const progressText = document.getElementById('progress-text');

    progressContainer.style.display = 'block';
    progressBar.value = 0;
    progressText.textContent = '0%';

    try {
        const response = await fetch(`/youtube/download?video_url=${encodeURIComponent(url)}&media_type=${mediaType}`);
        
        if (!response.ok) {
            throw new Error(await response.text());
        }

        // Получаем размер файла из заголовков
        const contentLength = response.headers.get('content-length');
        let loaded = 0;
        
        const reader = response.body.getReader();
        const chunks = [];
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            chunks.push(value);
            loaded += value.length;
            
            // Обновляем прогресс
            if (contentLength) {
                const percent = Math.round((loaded / contentLength) * 100);
                progressBar.value = percent;
                progressText.textContent = `${percent}%`;
            }
        }
        
        // Создаем файл
        const blob = new Blob(chunks);
        const downloadUrl = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = `video.${mediaType === 'audio' ? 'mp3' : 'mp4'}`;
        a.click();
        
    } catch (e) {
        alert(`Ошибка: ${e.message}`);
    } finally {
        progressContainer.style.display = 'none';
    }
}
