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

document.getElementById('load-sample').addEventListener('click', () => {
    document.getElementById('contract-text').value = SAMPLE_CONTRACT;
});

document.getElementById('analyze-btn').addEventListener('click', async () => {
    const text = document.getElementById('contract-text').value.trim();
    if (!text) { showError('Wklej tekst umowy przed analizą.'); return; }
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

    // Risk summary
    const summaryEl = document.getElementById('risk-summary');
    summaryEl.innerHTML = `
        <strong>Podsumowanie:</strong>
        <span class="risk-badge risk-badge--ok">✅ OK: ${risk_summary.ok || 0}</span>
        <span class="risk-badge risk-badge--warning">⚠️ Podejrzane: ${risk_summary.warning || 0}</span>
        <span class="risk-badge risk-badge--illegal">❌ Niezgodne z prawem: ${risk_summary.illegal || 0}</span>
    `;

    // Overall recommendation
    const recEl = document.getElementById('overall-rec');
    recEl.innerHTML = `<h4>Rekomendacja AI:</h4><p>${escHtml(overall_recommendation)}</p>`;

    // Clauses table
    const tbody = document.getElementById('clauses-body');
    tbody.innerHTML = clauses.map(c => {
        const statusMap = { ok: ['✅ OK', 'ok'], warning: ['⚠️ Podejrzana', 'warning'], illegal: ['❌ Niezgodna', 'illegal'] };
        const [label, cls] = statusMap[c.status] || ['? Nieznany', 'warning'];
        return `<tr>
            <td><span class="status-chip status-chip--${cls}">${label}</span></td>
            <td>
                <span class="clause-type-badge">${escHtml(c.clause_type)}</span><br>
                ${escHtml(c.content)}
            </td>
            <td>${escHtml(c.justification)}</td>
            <td><small>${escHtml(c.legal_basis || '—')}</small></td>
            <td><small>${escHtml(c.recommendation)}</small></td>
        </tr>`;
    }).join('');

    // Questions
    const qEl = document.getElementById('questions-section');
    qEl.innerHTML = `
        <h3>❓ Pytania do właściciela</h3>
        <ul class="questions-list">
            ${questions_for_landlord.map((q, i) => `
                <li class="question-item">
                    <span class="question-num">${i + 1}.</span>
                    <span>${escHtml(q)}</span>
                </li>
            `).join('')}
        </ul>
    `;
}

function escHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
