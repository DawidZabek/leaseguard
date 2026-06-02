let selectedFiles = [];

const photoInput = document.getElementById('photo-input');
const previewGrid = document.getElementById('photo-preview-grid');
const generateBtn = document.getElementById('generate-btn');
const photoCount = document.getElementById('photo-count');
const uploadZone = document.getElementById('upload-zone');

uploadZone.addEventListener('click', () => photoInput.click());

uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadZone.classList.add('drag-over');
});

uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('drag-over'));

uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.classList.remove('drag-over');
    addFiles(Array.from(e.dataTransfer.files));
});

photoInput.addEventListener('change', () => {
    addFiles(Array.from(photoInput.files));
    photoInput.value = '';
});

function addFiles(files) {
    const allowed = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp'];
    const valid = files.filter(f => allowed.includes(f.type));
    if (selectedFiles.length + valid.length > 10) {
        showError('Maksymalnie 10 zdjęć.');
        return;
    }
    selectedFiles = [...selectedFiles, ...valid];
    renderPreviews();
}

function renderPreviews() {
    previewGrid.innerHTML = '';
    selectedFiles.forEach((file, i) => {
        const url = URL.createObjectURL(file);
        const div = document.createElement('div');
        div.className = 'photo-thumb';
        div.innerHTML = `
            <img src="${url}" alt="${file.name}">
            <button class="photo-thumb-remove" data-i="${i}" title="Usuń">✕</button>
        `;
        previewGrid.appendChild(div);
    });

    previewGrid.querySelectorAll('.photo-thumb-remove').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            selectedFiles.splice(parseInt(btn.dataset.i), 1);
            renderPreviews();
        });
    });

    generateBtn.disabled = selectedFiles.length === 0;
    photoCount.textContent = selectedFiles.length > 0 ? `${selectedFiles.length} zdjęcie(a)` : '';
}

generateBtn.addEventListener('click', async () => {
    if (!selectedFiles.length) { showError('Wybierz przynajmniej jedno zdjęcie.'); return; }

    hideError();
    showLoader(true);
    document.getElementById('protocol-results').style.display = 'none';
    generateBtn.disabled = true;

    const formData = new FormData();
    selectedFiles.forEach(f => formData.append('photos', f));
    formData.append('address', document.getElementById('address').value.trim());

    try {
        const res = await fetch('/api/analyze-photos', {
            method: 'POST',
            body: formData,
        });
        const data = await res.json();

        if (!res.ok) { showError(data.error || 'Błąd serwera'); return; }

        renderProtocol(data);
        document.getElementById('protocol-results').style.display = 'block';
        document.getElementById('protocol-results').scrollIntoView({ behavior: 'smooth' });
    } catch (e) {
        showError('Błąd połączenia: ' + e.message);
    } finally {
        showLoader(false);
        generateBtn.disabled = selectedFiles.length === 0;
    }
});

function renderProtocol(data) {
    const { rooms, protocol_text, total_defects, property_address } = data;

    document.getElementById('defect-summary').innerHTML = `
        <div>
            <div class="defect-count">${total_defects}</div>
            <div>wykrytych usterek</div>
        </div>
        <div>
            <strong>${rooms.length}</strong> pomieszczeń przeanalizowanych
            ${property_address ? `<br><small>${escHtml(property_address)}</small>` : ''}
        </div>
    `;

    const grid = document.getElementById('rooms-grid');
    grid.innerHTML = rooms.map(r => {
        const condClass = r.general_condition.replace('ł', 'l').replace('ś', 's').replace('r', 'r');
        return `
        <div class="room-card">
            <div class="room-card-header">
                <span class="room-name">🏠 ${escHtml(r.room_name)}</span>
                <span class="condition-badge condition-badge--${r.general_condition}">${r.general_condition}</span>
            </div>
            <p style="font-size:.8rem;color:#64748b;margin-bottom:.75rem;">${escHtml(r.photo_description)}</p>
            ${r.defects.length > 0
                ? `<ul class="defects-list">${r.defects.map(d => `<li class="defect-item">⚠️ ${escHtml(d)}</li>`).join('')}</ul>`
                : `<p class="no-defects">✅ Brak usterek</p>`
            }
        </div>`;
    }).join('');

    document.getElementById('protocol-text').textContent = protocol_text;
}

document.getElementById('copy-protocol')?.addEventListener('click', () => {
    const text = document.getElementById('protocol-text').textContent;
    navigator.clipboard.writeText(text).then(() => {
        const btn = document.getElementById('copy-protocol');
        btn.textContent = '✅ Skopiowano';
        setTimeout(() => { btn.textContent = '📋 Kopiuj'; }, 2000);
    });
});

document.getElementById('print-protocol')?.addEventListener('click', () => {
    window.print();
});

function escHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
