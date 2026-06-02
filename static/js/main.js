function showError(msg) {
    const box = document.getElementById('error-box');
    if (!box) return;
    box.textContent = '⚠️ ' + msg;
    box.style.display = 'block';
}

function hideError() {
    const box = document.getElementById('error-box');
    if (box) box.style.display = 'none';
}

function showLoader(show) {
    const loader = document.getElementById('loader');
    if (loader) loader.style.display = show ? 'flex' : 'none';
}
