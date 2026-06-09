const SAMPLE_CONTRACT = `UMOWA NAJMU LOKALU MIESZKALNEGO

zawarta w dniu 1 czerwca 2026 roku w Warszawie pomiędzy:

Wynajmującym: Jan Kowalski, zamieszkały ul. Lipowa 5, 00-001 Warszawa
Najemcą: Anna Nowak, zamieszkała ul. Różana 3, 00-002 Warszawa

§ 1. PRZEDMIOT UMOWY
Wynajmujący oddaje Najemcy do używania lokal mieszkalny położony przy ul. Kwiatowa 10/4, 00-003 Warszawa, o powierzchni 45 m².

§ 2. CZAS TRWANIA UMOWY
Umowa zostaje zawarta na czas nieokreślony, począwszy od dnia 1 lipca 2026 roku.

§ 3. CZYNSZ I OPŁATY
1. Najemca zobowiązuje się płacić miesięczny czynsz w wysokości 2.500 złotych płatny z góry do 10 dnia każdego miesiąca.
2. Wynajmujący może jednostronnie podwyższyć czynsz w dowolnym momencie bez zachowania okresu wypowiedzenia.
3. Opłaty za media (prąd, gaz, woda) ponosi Najemca.

§ 4. KAUCJA
Najemca wpłaca kaucję zabezpieczającą w wysokości 10.000 złotych (czteromiesięczny czynsz). Kaucja zostanie zwrócona w ciągu 3 miesięcy od opróżnienia lokalu po potrąceniu wszelkich należności.

§ 5. WYPOWIEDZENIE UMOWY
1. Najemca może wypowiedzieć umowę z zachowaniem 3-miesięcznego okresu wypowiedzenia.
2. Wynajmujący może wypowiedzieć umowę w trybie natychmiastowym bez podania przyczyny.

§ 6. OBOWIĄZKI NAJEMCY
1. Najemca zobowiązuje się utrzymywać lokal w należytym stanie.
2. Wszelkie naprawy i remonty, nawet wynikające ze zwykłego zużycia, obciążają Najemcę.
3. Zakaz posiadania zwierząt domowych pod karą umowną 500 zł za każdy stwierdzony przypadek.
4. Zakaz palenia tytoniu pod karą umowną 1.000 zł.
5. Zakaz podnajmowania lokalu lub jego części.

§ 7. PODPISY
Wynajmujący: ___________________    Najemca: ___________________`;

// --- TABS ---
let activeTab = 'paste';

document.querySelectorAll('.input-tab').forEach(tab => {
    tab.addEventListener('click', () => {
        activeTab = tab.dataset.tab;
        document.querySelectorAll('.input-tab').forEach(t => t.classList.remove('input-tab--active'));
        tab.classList.add('input-tab--active');
        document.getElementById('tab-paste').style.display = activeTab === 'paste' ? '' : 'none';
        document.getElementById('tab-upload').style.display = activeTab === 'upload' ? '' : 'none';
    });
});

// --- DOCUMENT UPLOAD ---
const docInput = document.getElementById('doc-input');
const docZone = document.getElementById('doc-upload-zone');
const docStatus = document.getElementById('doc-status');

docZone.addEventListener('click', () => docInput.click());
docZone.addEventListener('dragover', e => { e.preventDefault(); docZone.classList.add('drag-over'); });
docZone.addEventListener('dragleave', () => docZone.classList.remove('drag-over'));
docZone.addEventListener('drop', e => {
    e.preventDefault();
    docZone.classList.remove('drag-over');
    if (e.dataTransfer.files[0]) handleDocFile(e.dataTransfer.files[0]);
});
docInput.addEventListener('change', () => {
    if (docInput.files[0]) handleDocFile(docInput.files[0]);
});

async function handleDocFile(file) {
    const allowedExts = ['.pdf', '.docx', '.doc', '.txt'];
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!allowedExts.includes(ext)) {
        setDocStatus('error', 'Nieobsługiwany format. Akceptowane: PDF, DOCX, TXT');
        return;
    }
    setDocStatus('loading', 'Wyodrębnianie tekstu z dokumentu...');
    const formData = new FormData();
    formData.append('file', file);
    try {
        const res = await fetch('/api/upload-contract', { method: 'POST', body: formData });
        const data = await res.json();
        if (!res.ok) { setDocStatus('error', data.error || 'Błąd serwera'); return; }
        document.querySelector('[data-tab="paste"]').click();
        document.getElementById('contract-text').value = data.text;
        setDocStatus('ok', `Wczytano: ${file.name} (${data.chars.toLocaleString()} znaków)`);
        docStatus.style.display = 'flex';
    } catch (e) {
        setDocStatus('error', 'Błąd połączenia: ' + e.message);
    }
}

function setDocStatus(type, msg) {
    docStatus.className = `doc-status doc-status--${type}`;
    docStatus.textContent = msg;
    docStatus.style.display = 'flex';
}

// --- SAMPLE & ANALYZE ---
document.getElementById('load-sample').addEventListener('click', () => {
    document.querySelector('[data-tab="paste"]').click();
    document.getElementById('contract-text').value = SAMPLE_CONTRACT;
});

document.getElementById('analyze-btn').addEventListener('click', async () => {
    const text = document.getElementById('contract-text').value.trim();
    if (!text) { showError('Wklej tekst umowy lub wgraj dokument.'); return; }
    if (text.length < 100) { showError('Tekst umowy jest zbyt krótki.'); return; }

    hideError();
    showLoader(true);
    document.getElementById('results-panel').style.display = 'none';
    document.getElementById('analyze-btn').disabled = true;

    try {
        const res = await fetch('/api/analyze-contract', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ contract_text: text }),
        });
        const data = await res.json();
        if (!res.ok) { showError(data.error || 'Błąd serwera'); return; }
        renderResults(data);
        document.getElementById('results-panel').style.display = 'block';
        document.getElementById('results-panel').scrollIntoView({ behavior: 'smooth' });
    } catch (e) {
        showError('Błąd połączenia z serwerem: ' + e.message);
    } finally {
        showLoader(false);
        document.getElementById('analyze-btn').disabled = false;
    }
});

function renderResults(data) {
    const { clauses, questions_for_landlord, overall_recommendation, risk_summary } = data;

    document.getElementById('risk-summary').innerHTML = `
        <strong>Podsumowanie:</strong>
        <span class="risk-badge risk-badge--ok">OK: ${risk_summary.ok || 0}</span>
        <span class="risk-badge risk-badge--warning">Podejrzane: ${risk_summary.warning || 0}</span>
        <span class="risk-badge risk-badge--illegal">Niezgodne z prawem: ${risk_summary.illegal || 0}</span>
    `;

    document.getElementById('overall-rec').innerHTML =
        `<h4>Rekomendacja AI:</h4><p>${escHtml(overall_recommendation)}</p>`;

    const statusMap = {
        ok: ['OK', 'ok'],
        warning: ['Podejrzana', 'warning'],
        illegal: ['Niezgodna z prawem', 'illegal'],
    };
    document.getElementById('clauses-body').innerHTML = clauses.map(c => {
        const [label, cls] = statusMap[c.status] || ['Nieznany', 'warning'];
        return `<tr>
            <td><span class="status-chip status-chip--${cls}">${label}</span></td>
            <td><span class="clause-type-badge">${escHtml(c.clause_type)}</span><br>${escHtml(c.content)}</td>
            <td>${escHtml(c.justification)}</td>
            <td><small>${escHtml(c.legal_basis || '—')}</small></td>
            <td><small>${escHtml(c.recommendation)}</small></td>
        </tr>`;
    }).join('');

    document.getElementById('questions-section').innerHTML = `
        <h3>Pytania do właściciela</h3>
        <ul class="questions-list">
            ${questions_for_landlord.map((q, i) => `
                <li class="question-item">
                    <span class="question-num">${i + 1}.</span>
                    <span>${escHtml(q)}</span>
                </li>`).join('')}
        </ul>`;
}

function escHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
