function updateProgressBar(percent) {
    const container = document.getElementById('progress-container');
    const bar = document.getElementById('download-progress');
    const text = document.getElementById('progress-text');
  
    container.style.display = 'block';
    bar.style.width = percent + '%';
    bar.setAttribute('aria-valuenow', percent);
    text.textContent = percent + '%';
  
    if (percent >= 100) {
      setTimeout(() => container.style.display = 'none', 1000);
    }
  }
  