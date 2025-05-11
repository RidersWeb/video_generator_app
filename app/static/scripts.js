// Спарсить прокси с сайтов
document.getElementById('StartParsing').addEventListener('click', function () {
    const CountProxy = document.getElementById('CountProxy').value;
    const TypeProxyFind = document.getElementById('TypeProxyFind').value.toLowerCase();
    const proxyList = document.getElementById('proxyInput');

    proxyList.value = '';

    const ws = new WebSocket(`ws://${location.host}/ws/parse_proxies`);
    ws.onopen = function () {
        ws.send(JSON.stringify({
            countproxy: CountProxy,
            typeproxy: TypeProxyFind
        }));
    };
    ws.onmessage = function (event) {
        const data = JSON.parse(event.data);
        const proxyList = document.getElementById('proxyInput');
        const nowproxy = document.getElementById('nowproxy');
        nowproxy.innerText = `Сейчас в файле ${data.proxies.length} прокси`;
        console.log(data.proxies);
        
        document.getElementById('progressContainer').style.display = 'block';
        // Добавляем прокси в список с подсветкой
        proxyList.value = data.proxies.join('\n');
        // proxyList.value += data.proxies + '\n';
    };
});

//  Кнопка сохранения через websocket
document.getElementById('saveproxy').addEventListener('click', function () {
    // Получаем список прокси из поля ввода
    const proxyList = document.getElementById('proxyInput').value.split('\n');
    const ws = new WebSocket(`ws://${location.host}/ws/save_proxies`);
    ws.onopen = function () {
        ws.send(JSON.stringify({
            proxies: proxyList
        }));
    };
    ws.onmessage = function (event) {
        const data = JSON.parse(event.data);
        const spanElement = document.getElementById('nowproxy');
        spanElement.style.transition = 'opacity 0.3s';
        spanElement.style.opacity = 0;
        setTimeout(() => {
            spanElement.textContent = `Сейчас в файле ${data.proxy_count} прокси`;
            spanElement.style.opacity = 1;
        }, 300);
    };
});


document.getElementById('checkProxies').addEventListener('click', function () {
    const proxyList = document.getElementById('proxyList');
    proxyList.innerHTML = '';  // Очищаем список прокси
    const testSite = document.getElementById('testSite').value.toLowerCase();
    const intTimeout = document.getElementById('intTimeout').value;
    const concurrencyLimit = document.getElementById('concurrencyLimit').value;
    document.getElementById('progressContainer').style.display = 'block';
    const TypeProxyCheck = Array.from(document.getElementById('TypeProxyCheck').selectedOptions).map(option => option.value.toLowerCase());


    const ws = new WebSocket(`ws://${location.host}/ws/check_proxies`);
    
    ws.onopen = function () {
        ws.send(JSON.stringify({
            site: testSite,
            typeproxy: TypeProxyCheck,
            intTimeout: intTimeout,
            concurrencyLimit: concurrencyLimit
        }));
    };

    ws.onmessage = function (event) {
        const data = JSON.parse(event.data)

        // Пропускаем сообщения без proxy
        if (!data.proxy) return;  // ⚠️ Важно: не добавляем, если proxy не
        // Обновляем прогресс
        let percent = Math.floor((data.current / data.total) * 100);
        document.getElementById('progressBar').style.width = percent + '%';
        document.getElementById('progressBar').innerText = percent + '%';
        // Обновляем счетчики
        document.getElementById('checkedCount').innerText = data.checked;
        document.getElementById('totalCount').innerText = data.total;
        document.getElementById('goodCount').innerText = data.good;
        document.getElementById('badCount').innerText = data.bad;
        // Добавляем прокси в список с подсветкой
        // const proxyList = document.getElementById('proxyList');
        
        const listItem = document.createElement('li');
        if (data.status === 'alive') {
            const listItem = document.createElement('li');
            listItem.className = 'list-group-item list-group-item-success'; // Живой
            listItem.textContent = `${data.proxy} (Живой)`;
            proxyList.appendChild(listItem);
        }
        // listItem.className = 'list-group-item ' + (data.status === 'alive' ? 'list-group-item-success' : 'list-group-item-danger');
        // listItem.textContent = `${data.proxy} (${data.status === 'alive' ? 'Живой' : 'Мёртвый'})`;
        // proxyList.appendChild(listItem);
    }
    ws.onclose = function (event) {
        console.log("Проверка завершена!");
    }
});


// Обработчики для табов (вынесено из вложенности)
const tabButtons = document.querySelectorAll('button[data-bs-toggle="tab"]');
tabButtons.forEach(button => {
    button.addEventListener('click', function () {
        localStorage.setItem('activeTab', this.getAttribute('data-bs-target'));
    });
});
// Восстановление активного таба
const activeTab = localStorage.getItem('activeTab');
if (activeTab) {
    const tabTriggerEl = document.querySelector(`button[data-bs-target="${activeTab}"]`);
    if (tabTriggerEl && tabTriggerEl.getAttribute('data-bs-target') === activeTab) {
        const tab = new bootstrap.Tab(tabTriggerEl);
        tab.show();
    };
};

// Обработчик для списка меню для проверки типа прокси

$(document).ready(function () {
  $('#TypeProxyCheck').select2({
    placeholder: "Выберите типы прокси",
    allowClear: true,
    width: '100%',
    closeOnSelect: false // Не закрывать dropdown после выбора
  });

window.selectAll = function () {
  $('#TypeProxyCheck').val(['http', 'socks4', 'socks5']).trigger('change');
};
}); // Закрывающая скобка для $(document).ready


// Скачивание видео
// function downloadVideo() {
//     const videoLink = document.getElementById('videoLink').value;
//     if (videoLink) {
//         alert(`Скачивание видео по ссылке: ${videoLink}`);
//         // Твоя логика для скачивания видео
//     } else {
//         alert('Введите ссылку на видео!');
//     }
// }