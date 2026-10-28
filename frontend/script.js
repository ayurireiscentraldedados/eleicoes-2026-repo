// Helper para remover acentos na busca
function removeAccents(str) {
    return (str || '').normalize("NFD").replace(/[\u0300-\u036f]/g, "");
}

const partyInfo = {
    '13': { sigla: 'PT', nome: 'Lula', color: '#cc0000' },
    '22': { sigla: 'PL', nome: 'Flávio Bolsonaro', color: '#003399' },
    'default': { sigla: 'Outros', color: '#888888' }
};

// Mapa Leaflet otimizado para 60 FPS
const map = L.map('map', {
    zoomControl: false,
    preferCanvas: true,
    updateWhenZooming: false,
    updateWhenIdle: true,
    wheelDebounceTime: 40,
    tap: true
}).setView([-5.3, -39.3], 7);

L.control.zoom({ position: 'topright' }).addTo(map);

// Panes customizados para manter a ordem de camadas:
// 1. boundariesPane (240): traçados de municípios e bairros (fundo)
// 2. bgLabelsPane (280): nomes dos municípios e bairros em cinza (no fundo)
// 3. overlayPane (400): bolinhas das escolas e locais de votação (frente)
const boundariesPane = map.createPane('boundariesPane');
boundariesPane.style.zIndex = 240;
boundariesPane.style.pointerEvents = 'none';

const bgLabelsPane = map.createPane('bgLabelsPane');
bgLabelsPane.style.zIndex = 280;
bgLabelsPane.style.pointerEvents = 'none';

// Renderers dedicados (GPU acelerados via Canvas):
const boundariesRenderer = L.svg({ pane: 'boundariesPane' });
const pointsCanvasRenderer = L.canvas({ 
    pane: 'overlayPane',
    padding: 0.5,
    tolerance: 10
});

function updateZoomClasses() {
    const z = Math.round(map.getZoom());
    const mapEl = document.getElementById('map');
    if (!mapEl) return;
    mapEl.className = mapEl.className.replace(/\bzoom-\d+\b/g, '').trim();
    mapEl.classList.add(`zoom-${z}`);
}
map.on('zoom', updateZoomClasses);
updateZoomClasses();

// Previne propagação de clique na sidebar e bottom sheet
const sidebar = document.querySelector('.sidebar');
if (sidebar) {
    L.DomEvent.disableClickPropagation(sidebar);
    L.DomEvent.disableScrollPropagation(sidebar);
}

// Abrir/fechar gaveta no mobile
const sidebarHeader = document.getElementById('sidebar-header');
if (sidebarHeader && sidebar) {
    sidebarHeader.addEventListener('click', (e) => {
        if (e.target.closest('.search-container') || 
            e.target.closest('.turno-selector') || 
            e.target.closest('.filter-chips-container') ||
            e.target.closest('.state-summary-card')) return;
        if (window.innerWidth <= 768) {
            sidebar.classList.toggle('open');
        }
    });
}

// Base de Mapa Clean
L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
    attribution: 'Tiles &copy; Esri &mdash; Central de dados O POVO+',
    maxZoom: 16
}).addTo(map);

const tooltip = document.getElementById('custom-tooltip');
let selectedLayer = null;
let selectedLatLng = null;
let pulseLayer = null;
let currentTurno = '2turno'; // Padrão: 2º Turno
let currentFilter = 'all'; // all, lula, bolso

// Efeito radar no local clicado
function showPulseEffect(latlng, color) {
    removePulseEffect();
    const icon = L.divIcon({
        className: 'radar-pulse-container',
        html: `
            <div class="radar-pulse">
                <div class="radar-wave wave-1" style="--wave-color: ${color};"></div>
                <div class="radar-wave wave-2" style="--wave-color: ${color};"></div>
                <div class="radar-wave wave-3" style="--wave-color: ${color};"></div>
                <div class="radar-core" style="background-color: ${color};"></div>
            </div>
        `,
        iconSize: [60, 60],
        iconAnchor: [30, 30]
    });
    pulseLayer = L.marker(latlng, { icon: icon, interactive: false, zIndexOffset: 9999 }).addTo(map);
}

function removePulseEffect() {
    if (pulseLayer) {
        map.removeLayer(pulseLayer);
        pulseLayer = null;
    }
}

// Fecha popup e desmarca ponto
function clearSelection() {
    if (tooltip) tooltip.classList.add('hidden');
    removePulseEffect();
    if (selectedLayer && geojsonLayer) {
        geojsonLayer.resetStyle(selectedLayer);
    }
    selectedLayer = null;
    selectedLatLng = null;
}

// Clicar no mapa fora dos pontos fecha o popup
map.on('click', () => {
    clearSelection();
});

// Fechar com tecla ESC
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        clearSelection();
        const helpModal = document.getElementById('help-modal');
        if (helpModal) helpModal.classList.add('hidden');
        if (typeof dismissFsPrompt === 'function') dismissFsPrompt();
    }
});

// Eventos de clique dentro do tooltip (Botão X)
if (tooltip) {
    tooltip.addEventListener('click', (e) => {
        if (e.target.closest('.tt-close-btn') || e.target.closest('.mobile-sheet-handle')) {
            clearSelection();
            e.stopPropagation();
            return;
        }
        e.stopPropagation();
    });
    tooltip.addEventListener('touchstart', (e) => {
        if (e.target.closest('.tt-close-btn') || e.target.closest('.mobile-sheet-handle')) {
            clearSelection();
            e.stopPropagation();
            return;
        }
        e.stopPropagation();
    }, { passive: true });
}

// Raio visual das bolinhas de acordo com votos e zoom
function getRadius(votos, zoom) {
    if (!votos || votos === 0) return 2.0;
    const zoomFactor = Math.pow(1.25, zoom - 7);
    return Math.max(2.0, Math.sqrt(votos) * 0.045 * zoomFactor); 
}

// Estilização do ponto no mapa
function pointToLayer(feature, latlng) {
    const props = feature.properties;
    let cor = partyInfo['default'].color;
    
    if (currentTurno === 'variacao') {
        const diff = props.comp ? props.comp.diff : (props.diff || {});
        if (diff.quem_cresceu === 'LULA') {
            cor = '#cc0000';
        } else if (diff.quem_cresceu === 'FLAVIO BOLSONARO') {
            cor = '#003399';
        } else {
            cor = '#888888';
        }
    } else {
        const venc = String(props.Vencedor_Nome || '').toUpperCase();
        if (venc.includes('LULA')) {
            cor = '#cc0000';
        } else if (venc.includes('BOLSONARO') || venc.includes('FLAVIO') || venc.includes('FLÁVIO')) {
            cor = '#003399';
        } else if (props.Candidatos && props.Candidatos.length > 0) {
            let n = props.Candidatos[0].Numero;
            if (n === 13) cor = '#cc0000';
            else if (n === 22) cor = '#003399';
        }
    }
    
    let op = 0.6;
    let fillOp = 0.85;
    
    // Verifica se há filtro ativo
    if (currentFilter !== 'all') {
        let match = false;
        if (currentTurno === 'variacao') {
            const diff = (props.comp && props.comp.diff) ? props.comp.diff : {};
            if (currentFilter === 'lula' && diff.quem_cresceu === 'LULA') match = true;
            if (currentFilter === 'bolso' && diff.quem_cresceu === 'FLAVIO BOLSONARO') match = true;
        } else {
            const venc = String(props.Vencedor_Nome || '').toUpperCase();
            if (currentFilter === 'lula' && venc.includes('LULA')) match = true;
            if (currentFilter === 'bolso' && (venc.includes('BOLSONARO') || venc.includes('FLAVIO'))) match = true;
        }
        if (!match) {
            op = 0.05;
            fillOp = 0.08;
        }
    }
    
    return L.circleMarker(latlng, {
        renderer: pointsCanvasRenderer,
        radius: getRadius(props.Total_Validos, map.getZoom()),
        fillColor: cor,
        color: '#ffffff',
        weight: 0.5,
        opacity: op,
        fillOpacity: fillOp
    });
}

let cachedTooltipWidth = 420;
let cachedTooltipHeight = 300;

// Posicionamento inteligente: No desktop ancora acima/abaixo com espaço; no mobile é bottom sheet
function updateTooltipPosition(e) {
    if (window.innerWidth <= 768) {
        // No celular, a folha é fixa no fundo (CSS bottom: 0), não calcula top/left
        return;
    }
    
    if (e && e.latlng) {
        selectedLatLng = e.latlng;
    }
    
    let x, y;
    if (selectedLatLng && map) {
        const pt = map.latLngToContainerPoint(selectedLatLng);
        x = pt.x;
        y = pt.y;
    } else if (e && e.originalEvent) {
        const oe = e.originalEvent;
        x = oe.clientX !== undefined ? oe.clientX : oe.pageX;
        y = oe.clientY !== undefined ? oe.clientY : oe.pageY;
    }
    
    if (x === undefined || y === undefined || isNaN(x) || isNaN(y)) {
        x = (window.innerWidth + 340) / 2;
        y = window.innerHeight / 2;
    }
    
    const tw = cachedTooltipWidth;
    const th = cachedTooltipHeight;
    
    // Bounds horizontais (evita sobrepor a sidebar de 340px na esquerda)
    const minLeft = 360 + (tw / 2);
    const maxRight = window.innerWidth - 20 - (tw / 2);
    
    if (x > maxRight) x = maxRight;
    if (x < minLeft) x = minLeft;
    
    // Bounds verticais: tenta posicionar ACIMA da bolinha com folga
    let finalTop = y - th - 18;
    if (finalTop < 20) {
        // Se bater no topo, posiciona ABAIXO da bolinha com folga
        finalTop = y + 24;
        if (finalTop + th > window.innerHeight - 20) {
            finalTop = Math.max(20, (window.innerHeight - th) / 2);
        }
    }
    
    tooltip.style.left = Math.round(x) + 'px';
    tooltip.style.top = Math.round(finalTop) + 'px';
}

let moveRafId = null;
map.on('move', () => {
    if (selectedLatLng && tooltip && !tooltip.classList.contains('hidden') && window.innerWidth > 768) {
        if (!moveRafId) {
            moveRafId = requestAnimationFrame(() => {
                updateTooltipPosition({ latlng: selectedLatLng });
                moveRafId = null;
            });
        }
    }
});


// Calcula o centro exato da tela para posicionar o marcador na coordenada desejada (precisão de pixel)
function getCameraCenterForMarker(latlng, targetZoom) {
    const isMobile = window.innerWidth <= 768;
    const viewW = window.innerWidth;
    const viewH = window.innerHeight;
    
    // No celular: 28% da altura da tela (visível acima do bottom sheet)
    // No desktop: 60% da altura da tela (com margem de sobra para o popup acima da bolinha)
    const targetY = isMobile ? (viewH * 0.28) : (viewH * 0.60);
    const targetX = isMobile ? (viewW / 2) : Math.max(viewW * 0.58, (viewW + 360) / 2);
    
    const deltaX = targetX - (viewW / 2);
    const deltaY = targetY - (viewH / 2);
    
    // Projeção matemática precisa no zoom de destino
    const markerWorldPixel = map.project(latlng, targetZoom);
    const centerWorldPixel = markerWorldPixel.subtract([deltaX, deltaY]);
    
    return map.unproject(centerWorldPixel, targetZoom);
}

// Seleção unificada de escola (funciona idêntico no clique e na busca)
function selectSchool(feature, layer, latlng) {
    if (selectedLayer && geojsonLayer) {
        geojsonLayer.resetStyle(selectedLayer);
    }
    selectedLayer = layer;
    selectedLatLng = latlng;
    
    if (layer && typeof layer.setStyle === 'function') {
        layer.setStyle({ weight: 3, color: '#111', opacity: 1, fillOpacity: 1 });
    }
    
    let cor = '#cc0000';
    const props = feature.properties || {};
    if (currentTurno === 'variacao') {
        const diff = (props.comp && props.comp.diff) ? props.comp.diff : {};
        cor = diff.quem_cresceu === 'FLAVIO BOLSONARO' ? '#003399' : '#cc0000';
    } else {
        const venc = String(props.Vencedor_Nome || '').toUpperCase();
        cor = (venc.includes('BOLSONARO') || venc.includes('FLAVIO') || venc.includes('FLÁVIO')) ? '#003399' : '#cc0000';
    }
    showPulseEffect(latlng, cor);
    
    const targetZoom = Math.max(map.getZoom(), 14);
    const newCenter = getCameraCenterForMarker(latlng, targetZoom);
    
    map.flyTo(newCenter, targetZoom, { duration: 0.65, easeLinearity: 0.25 });
    
    let opened = false;
    const openPopup = () => {
        if (opened) return;
        opened = true;
        updateTooltip(feature, { latlng: latlng });
    };
    
    map.once('moveend', openPopup);
    setTimeout(openPopup, 700);
}

function onEachFeature(feature, layer) {
    layer.on({
        click: function(e) {
            L.DomEvent.stopPropagation(e);
            if (e.originalEvent) e.originalEvent.stopPropagation();
            const latlng = e.latlng || layer.getLatLng();
            selectSchool(feature, layer, latlng);
        }
    });
}

function updateTooltip(feature, e) {
    const props = feature.properties;
    const comp = props.comp || {};
    const t1 = comp.t1 || { lula: 0, bolso: 0, total: 0, lula_pct: 0, bolso_pct: 0 };
    const t2 = comp.t2 || { lula: 0, bolso: 0, total: 0, lula_pct: 0, bolso_pct: 0 };
    const diff = comp.diff || { lula_votos: 0, bolso_votos: 0, lula_pct: 0, bolso_pct: 0, quem_cresceu: 'EMPATE', vantagem_pct: 0 };
    const activeData = (currentTurno === '1turno') ? t1 : t2;
    
    // Status Badge & Cor do Vencedor
    let badgeHtml = '';
    let corVencedor = '#cc0000';
    
    if (currentTurno === 'variacao') {
        if (diff.quem_cresceu === 'LULA') {
            corVencedor = '#cc0000';
            badgeHtml = `
                <div class="comp-badge comp-badge-pt">
                    <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor"><path d="M7 14l5-5 5 5z"/></svg>
                    <span>Lula teve maior crescimento (+${diff.vantagem_pct.toFixed(1).replace('.', ',')} pp)</span>
                </div>
            `;
        } else if (diff.quem_cresceu === 'FLAVIO BOLSONARO') {
            corVencedor = '#003399';
            badgeHtml = `
                <div class="comp-badge comp-badge-pl">
                    <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor"><path d="M7 14l5-5 5 5z"/></svg>
                    <span>Flávio Bolsonaro teve maior crescimento (+${diff.vantagem_pct.toFixed(1).replace('.', ',')} pp)</span>
                </div>
            `;
        } else {
            corVencedor = '#64748b';
            badgeHtml = `<div class="comp-badge comp-badge-empate"><span>Crescimento estável em ambos os turnos</span></div>`;
        }
    } else {
        const venc = String(props.Vencedor_Nome || '').toUpperCase();
        const difVotos = Math.abs((activeData.lula || 0) - (activeData.bolso || 0)) || Number(props.Diferenca || 0);
        const sufixoVotos = difVotos === 1 ? 'voto' : 'votos';

        if (venc.includes('LULA') || (activeData.lula > activeData.bolso)) {
            corVencedor = '#cc0000';
            badgeHtml = `
                <div class="comp-badge comp-badge-pt">
                    <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
                    <span>Lula ganhou neste local com diferença de ${Number(difVotos).toLocaleString('pt-BR')} ${sufixoVotos}</span>
                </div>
            `;
        } else if (venc.includes('BOLSONARO') || venc.includes('FLAVIO') || venc.includes('FLÁVIO') || (activeData.bolso > activeData.lula)) {
            corVencedor = '#003399';
            badgeHtml = `
                <div class="comp-badge comp-badge-pl">
                    <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
                    <span>Flávio Bolsonaro ganhou neste local com diferença de ${Number(difVotos).toLocaleString('pt-BR')} ${sufixoVotos}</span>
                </div>
            `;
        } else {
            corVencedor = '#64748b';
            badgeHtml = `<div class="comp-badge comp-badge-empate"><span>Empate exato de votos neste local</span></div>`;
        }
    }

    // Barras Visuais do Turno Ativo
    const lulaPct = activeData.lula_pct || 0;
    const bolsoPct = activeData.bolso_pct || 0;
    const lulaVotos = (activeData.lula || 0).toLocaleString('pt-BR');
    const bolsoVotos = (activeData.bolso || 0).toLocaleString('pt-BR');

    const barsHtml = `
        <div class="cand-bars-box">
            <div class="cand-bar-row">
                <img src="lula.jpg" class="cand-photo-thumb" onerror="this.src='https://ui-avatars.com/api/?name=Lula&background=cc0000&color=fff'" alt="Lula">
                <div class="cand-bar-body">
                    <div class="cand-bar-info">
                        <span class="cand-name-title">Lula <span class="cand-party-pill party-pt">PT</span></span>
                        <span class="cand-bar-val"><span class="cand-bar-votes">${lulaVotos} votos</span> <strong style="color: #cc0000;">${lulaPct.toFixed(1).replace('.', ',')}%</strong></span>
                    </div>
                    <div class="tt-bar-bg">
                        <div class="tt-bar-fill" style="width: ${lulaPct}%; background: #cc0000;"></div>
                    </div>
                </div>
            </div>
            <div class="cand-bar-row">
                <img src="flavio.jpg" class="cand-photo-thumb" onerror="this.src='https://ui-avatars.com/api/?name=Flavio+Bolsonaro&background=003399&color=fff'" alt="Flávio Bolsonaro">
                <div class="cand-bar-body">
                    <div class="cand-bar-info">
                        <span class="cand-name-title">Flávio Bolsonaro <span class="cand-party-pill party-pl">PL</span></span>
                        <span class="cand-bar-val"><span class="cand-bar-votes">${bolsoVotos} votos</span> <strong style="color: #003399;">${bolsoPct.toFixed(1).replace('.', ',')}%</strong></span>
                    </div>
                    <div class="tt-bar-bg">
                        <div class="tt-bar-fill" style="width: ${bolsoPct}%; background: #003399;"></div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Tabela Comparativa de 1º e 2º Turno (Lula x Flávio Bolsonaro)
    const compTableHtml = `
        <div class="comp-table-card">
            <table class="comp-table">
                <thead>
                    <tr>
                        <th>Candidato</th>
                        <th>1º Turno</th>
                        <th>2º Turno</th>
                        <th>Saldo</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>
                            <div class="cand-name-cell">
                                <span class="dot-indicator dot-pt"></span>
                                <span>Lula</span>
                            </div>
                        </td>
                        <td style="text-align: right;">
                            <strong>${t1.lula.toLocaleString('pt-BR')}</strong>
                            <div style="font-size: 0.70rem; color: #64748b;">${t1.lula_pct.toFixed(1).replace('.', ',')}%</div>
                        </td>
                        <td style="text-align: right;">
                            <strong>${t2.lula.toLocaleString('pt-BR')}</strong>
                            <div style="font-size: 0.70rem; color: #64748b;">${t2.lula_pct.toFixed(1).replace('.', ',')}%</div>
                        </td>
                        <td style="text-align: right;">
                            <span class="${diff.lula_votos >= 0 ? 'diff-plus' : 'diff-minus'}">
                                ${diff.lula_votos >= 0 ? '+' : ''}${diff.lula_votos.toLocaleString('pt-BR')}
                            </span>
                            <div style="font-size: 0.70rem; font-weight: 700;" class="${diff.lula_pct >= 0 ? 'diff-plus' : 'diff-minus'}">
                                (${diff.lula_pct >= 0 ? '+' : ''}${diff.lula_pct.toFixed(1).replace('.', ',')} pp)
                            </div>
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <div class="cand-name-cell">
                                <span class="dot-indicator dot-pl"></span>
                                <span>Flávio Bolsonaro</span>
                            </div>
                        </td>
                        <td style="text-align: right;">
                            <strong>${t1.bolso.toLocaleString('pt-BR')}</strong>
                            <div style="font-size: 0.70rem; color: #64748b;">${t1.bolso_pct.toFixed(1).replace('.', ',')}%</div>
                        </td>
                        <td style="text-align: right;">
                            <strong>${t2.bolso.toLocaleString('pt-BR')}</strong>
                            <div style="font-size: 0.70rem; color: #64748b;">${t2.bolso_pct.toFixed(1).replace('.', ',')}%</div>
                        </td>
                        <td style="text-align: right;">
                            <span class="${diff.bolso_votos >= 0 ? 'diff-plus' : 'diff-minus'}">
                                ${diff.bolso_votos >= 0 ? '+' : ''}${diff.bolso_votos.toLocaleString('pt-BR')}
                            </span>
                            <div style="font-size: 0.70rem; font-weight: 700;" class="${diff.bolso_pct >= 0 ? 'diff-plus' : 'diff-minus'}">
                                (${diff.bolso_pct >= 0 ? '+' : ''}${diff.bolso_pct.toFixed(1).replace('.', ',')} pp)
                            </div>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    `;

    let addressHtml = '';
    if (props.Endereco) {
        let bairro = props.Bairro ? ' - ' + props.Bairro : '';
        addressHtml = `<div class="tt-address">${props.Endereco}${bairro}</div>`;
    }

    tooltip.innerHTML = `
        <div class="op-tooltip" style="--venc-color: ${corVencedor};">
            <div class="mobile-sheet-handle"></div>
            <div class="tt-header">
                <div class="tt-header-text">
                    <h3 class="tt-title">${props.Local_Norm || props.Local}</h3>
                    <div class="tt-subtitle">${props.Municipio || props.Município || ''} (CE) &bull; Zona ${props.Zona}</div>
                </div>
                <button class="tt-close-btn" aria-label="Fechar" title="Fechar (ESC)">&times;</button>
            </div>
            ${addressHtml}
            ${badgeHtml}
            ${barsHtml}
            ${compTableHtml}
            <div class="tt-footer">
                <span>Votos válidos no local:</span>
                <span><strong>${Number(t2.total || props.Total_Validos).toLocaleString('pt-BR')}</strong> (2ºT) &bull; <strong>${Number(t1.total || 0).toLocaleString('pt-BR')}</strong> (1ºT)</span>
            </div>
        </div>
    `;

    tooltip.classList.remove('hidden');
    cachedTooltipWidth = tooltip.offsetWidth || 420;
    cachedTooltipHeight = tooltip.offsetHeight || 300;

    updateTooltipPosition(e);
}

// Totais Oficiais e Consolidados do Ceará (Fonte Oficial: TSE - 100% das urnas apuradas)
const CEARA_STATS = {
    '2turno': {
        label: '2º Turno',
        total: 5855602,
        cands: [
            { nome: 'Lula (PT)', votos: 4036124, pct: 68.93, cor: '#cc0000' },
            { nome: 'Flávio Bolsonaro (PL)', votos: 1819478, pct: 31.07, cor: '#003399' }
        ],
        vantagemText: 'Lula venceu no Ceará por 2.216.646 votos (+37,86 pp)'
    },
    '1turno': {
        label: '1º Turno',
        total: 5617796,
        cands: [
            { nome: 'Lula (PT)', votos: 3555263, pct: 63.29, cor: '#cc0000' },
            { nome: 'Flávio Bolsonaro (PL)', votos: 1756850, pct: 31.27, cor: '#003399' },
            { nome: 'Outros Candidatos', votos: 305683, pct: 5.44, cor: '#888888' }
        ],
        vantagemText: 'Lula liderou o 1º Turno no Ceará por 1.798.413 votos (+32,02 pp)'
    },
    'variacao': {
        label: 'Variação / Saldo',
        total: 237806, // Votos válidos adicionais no 2ºT
        cands: [
            { nome: 'Lula (PT)', diffVotos: '+480.861 votos', diffPct: '+5,64 pp', pct: 68.93, cor: '#cc0000' },
            { nome: 'Flávio Bolsonaro (PL)', diffVotos: '+62.628 votos', diffPct: '-0,20 pp', pct: 31.07, cor: '#003399' }
        ],
        vantagemText: 'Lula ampliou vantagem no CE (+480.861 votos novos)'
    }
};

function updateStateSummary(turno) {
    const data = CEARA_STATS[turno] || CEARA_STATS['2turno'];
    const badge = document.getElementById('summary-turno-label');
    const container = document.getElementById('summary-bars-content');
    
    if (badge) badge.textContent = data.label;
    if (!container) return;

    if (turno === 'variacao') {
        container.innerHTML = `
            <div style="font-size: 0.74rem; color: #166534; font-weight: 700; margin-bottom: 6px;">
                ${data.vantagemText}
            </div>
            <div style="display: flex; flex-direction: column; gap: 6px;">
                <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.80rem;">
                    <div style="display: flex; align-items: center; gap: 6px;">
                        <span class="legend-dot" style="background: #cc0000;"></span>
                        <strong>Lula (PT)</strong>
                    </div>
                    <div>
                        <strong style="color: #15803d;">+480.861</strong>
                        <span style="font-size: 0.72rem; color: #64748b; font-weight: 700;">(+5,64 pp)</span>
                    </div>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.80rem;">
                    <div style="display: flex; align-items: center; gap: 6px;">
                        <span class="legend-dot" style="background: #003399;"></span>
                        <strong>Flávio Bolsonaro (PL)</strong>
                    </div>
                    <div>
                        <strong style="color: #15803d;">+62.628</strong>
                        <span style="font-size: 0.72rem; color: #64748b; font-weight: 700;">(-0,20 pp)</span>
                    </div>
                </div>
            </div>
        `;
    } else {
        let html = '';
        data.cands.forEach(c => {
            html += `
                <div class="summary-cand-row">
                    <span class="summary-cand-name">
                        <span class="legend-dot" style="background: ${c.cor};"></span>
                        ${c.nome}
                    </span>
                    <span class="summary-cand-stats">
                        <span class="summary-cand-votes">${c.votos.toLocaleString('pt-BR')}</span>
                        <span style="color: ${c.cor};">${c.pct.toFixed(2).replace('.', ',')}%</span>
                    </span>
                </div>
                <div class="summary-bar-bg">
                    <div class="summary-bar-fill" style="width: ${c.pct}%; background: ${c.cor};"></div>
                </div>
            `;
        });
        container.innerHTML = html;
    }
}

// Atualiza rótulos dos filtros de acordo com o Turno
function updateFilterChipsUI(turno) {
    const chipAll = document.querySelector('.filter-chip[data-filter="all"]');
    const chipLula = document.querySelector('.filter-chip[data-filter="lula"]');
    const chipBolso = document.querySelector('.filter-chip[data-filter="bolso"]');
    
    if (chipAll) chipAll.textContent = 'Todos os locais';
    
    if (turno === 'variacao') {
        if (chipLula) chipLula.textContent = 'Onde Lula cresceu mais';
        if (chipBolso) chipBolso.textContent = 'Onde Flávio Bolsonaro cresceu mais';
    } else {
        if (chipLula) chipLula.textContent = 'Locais com vitória de Lula';
        if (chipBolso) chipBolso.textContent = 'Locais com vitória de Flávio Bolsonaro';
    }
}

let geojsonLayer;
let boundsLayer;
let bairrosLayer;
let allFeatures = [];
const cacheTurnos = {};
let currentLoadingStartTime = 0;

function showLoading(msg = 'Carregando mapa...') {
    const loading = document.getElementById('loading-overlay');
    const statusText = document.getElementById('loading-status-text');
    if (statusText) statusText.textContent = msg;
    if (loading) {
        loading.style.display = 'flex';
        loading.style.visibility = 'visible';
        loading.style.opacity = '1';
    }
    currentLoadingStartTime = Date.now();
}

function hideLoading(minDisplayMs = 350) {
    const loading = document.getElementById('loading-overlay');
    const elapsed = Date.now() - currentLoadingStartTime;
    const remaining = Math.max(0, minDisplayMs - elapsed);
    
    setTimeout(() => {
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                if (loading) {
                    loading.style.opacity = '0';
                    setTimeout(() => {
                        loading.style.display = 'none';
                        loading.style.visibility = 'hidden';
                        if (map) map.invalidateSize();
                    }, 300);
                }
            });
        });
    }, remaining);
}

showLoading('Carregando locais de votação do Ceará...');

// Carrega os 184 municípios do Ceará (fundo de referência)
fetch('ce_municipios.geojson?v=' + Date.now())
    .then(res => res.json())
    .then(data => {
        boundsLayer = L.geoJSON(data, {
            pane: 'boundariesPane',
            renderer: boundariesRenderer,
            style: { 
                color: '#888888', 
                weight: 0.8, 
                fill: false, 
                opacity: 0.65 
            },
            interactive: false,
            onEachFeature: function(feature, layer) {
                const props = feature.properties || {};
                const name = props.nome || props.NM_MUNICIPIO;
                if (name) {
                    if (props.center) {
                        layer.getCenter = function() {
                            return L.latLng(props.center[0], props.center[1]);
                        };
                    }
                    let extraClass = props.is_hub ? 'mun-hub' : 'mun-minor';
                    if (name.toLowerCase() === 'fortaleza') {
                        extraClass += ' mun-fortaleza';
                    }
                    layer.bindTooltip(name, {
                        permanent: true,
                        direction: 'center',
                        className: `municipio-label ${extraClass}`,
                        pane: 'bgLabelsPane',
                        interactive: false
                    });
                }
            }
        }).addTo(map);
        
        loadTurno('2turno'); // Inicia com o 2º Turno consolidado
        
        // Background prefetch do 1º Turno para alternância instantânea (0ms)
        setTimeout(() => {
            fetch('mapa_presidente_1turno.geojson?v=' + Date.now())
                .then(r => r.json())
                .then(d => { cacheTurnos['mapa_presidente_1turno.geojson'] = d; })
                .catch(() => {});
        }, 1200);
    })
    .catch(err => {
        console.error(err);
        loadTurno('2turno');
    });

// Carrega os 121 bairros de Fortaleza (aparecem com zoom)
fetch('fortaleza_bairros.geojson?v=' + Date.now())
    .then(res => res.json())
    .then(data => {
        bairrosLayer = L.geoJSON(data, {
            pane: 'boundariesPane',
            renderer: boundariesRenderer,
            style: {
                color: '#555555',
                weight: 1.0,
                dashArray: '3, 4',
                fill: false,
                opacity: 0.7
            },
            interactive: false,
            onEachFeature: function(feature, layer) {
                const props = feature.properties || {};
                if (props.Nome) {
                    if (props.center) {
                        layer.getCenter = function() {
                            return L.latLng(props.center[0], props.center[1]);
                        };
                    }
                    layer.bindTooltip(props.Nome, {
                        permanent: true,
                        direction: 'center',
                        className: 'bairro-label',
                        pane: 'bgLabelsPane',
                        interactive: false
                    });
                }
            }
        });
        updateBairrosVisibility();
    })
    .catch(err => console.error(err));

function updateBairrosVisibility() {
    if (!bairrosLayer) return;
    const zoom = map.getZoom();
    if (zoom >= 11) {
        if (!map.hasLayer(bairrosLayer)) {
            bairrosLayer.addTo(map);
            if (geojsonLayer) geojsonLayer.bringToFront();
        }
    } else {
        if (map.hasLayer(bairrosLayer)) {
            map.removeLayer(bairrosLayer);
        }
    }
}

function loadTurno(turno) {
    currentTurno = turno;
    clearSelection();
    
    // Atualiza Resumo e Chips
    updateStateSummary(turno);
    updateFilterChipsUI(turno);
    
    let labelTurno = (turno === '2turno') ? '2º Turno' : (turno === '1turno' ? '1º Turno' : 'Variação / Crescimento');
    let arquivoGeoJSON = (turno === '1turno') ? 'mapa_presidente_1turno.geojson' : 'mapa_presidente_2turno.geojson';
    
    const applyGeoJSON = (data) => {
        if (geojsonLayer) {
            map.removeLayer(geojsonLayer);
        }
        allFeatures = data.features;
        
        // Prepara índice rápido de busca em memória
        allFeatures.forEach(f => {
            const p = f.properties;
            f._searchIndex = removeAccents(`${p.Local_Norm || p.Local || ''} ${p.Municipio || ''} ${p.Bairro || ''} ${p.Endereco || ''}`).toLowerCase();
        });
        
        geojsonLayer = L.geoJSON(data, {
            pointToLayer: pointToLayer,
            onEachFeature: onEachFeature
        }).addTo(map);
        
        applyFilter(currentFilter);
        hideLoading(250);
    };

    if (cacheTurnos[arquivoGeoJSON]) {
        applyGeoJSON(cacheTurnos[arquivoGeoJSON]);
        return;
    }
    
    showLoading(`Carregando apuração para Presidente (${labelTurno})...`);
    
    let cacheBuster = Date.now();
    fetch(`${arquivoGeoJSON}?v=${cacheBuster}`)
        .then(res => res.json())
        .then(data => {
            cacheTurnos[arquivoGeoJSON] = data;
            applyGeoJSON(data);
        })
        .catch(err => {
            console.error(err);
            hideLoading(100);
        });
}

// Botões de Turno
document.querySelectorAll('.turno-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        document.querySelectorAll('.turno-btn').forEach(b => b.classList.remove('active'));
        this.classList.add('active');
        loadTurno(this.getAttribute('data-turno'));
    });
});

// Filtros Rápidos (Chips)
function applyFilter(filterType) {
    currentFilter = filterType;
    if (!geojsonLayer) return;
    
    geojsonLayer.eachLayer(layer => {
        const props = layer.feature.properties;
        let match = true;
        
        if (filterType !== 'all') {
            if (currentTurno === 'variacao') {
                const diff = (props.comp && props.comp.diff) ? props.comp.diff : {};
                if (filterType === 'lula' && diff.quem_cresceu !== 'LULA') match = false;
                if (filterType === 'bolso' && diff.quem_cresceu !== 'FLAVIO BOLSONARO') match = false;
            } else {
                const venc = String(props.Vencedor_Nome || '').toUpperCase();
                if (filterType === 'lula' && !venc.includes('LULA')) match = false;
                if (filterType === 'bolso' && !(venc.includes('BOLSONARO') || venc.includes('FLAVIO'))) match = false;
            }
        }
        
        if (match) {
            layer.setStyle({ opacity: 0.6, fillOpacity: 0.85 });
        } else {
            layer.setStyle({ opacity: 0.05, fillOpacity: 0.08 });
        }
    });
}

document.querySelectorAll('.filter-chip').forEach(chip => {
    chip.addEventListener('click', function() {
        document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
        this.classList.add('active');
        applyFilter(this.getAttribute('data-filter'));
    });
});

// Evento de zoom otimizado (só recalcula quando muda o número inteiro do zoom)
let lastZoomInt = Math.round(map.getZoom());
map.on('zoomend', function() {
    const currentZoom = Math.round(map.getZoom());
    updateZoomClasses();
    updateBairrosVisibility();
    if (!geojsonLayer || currentZoom === lastZoomInt) return;
    lastZoomInt = currentZoom;
    requestAnimationFrame(() => {
        geojsonLayer.eachLayer(function(layer) {
            const votos = layer.feature.properties.Total_Validos;
            layer.setRadius(getRadius(votos, currentZoom));
        });
    });
});

// Busca Inteligente com índice rápido
const searchInput = document.getElementById('search-input');
const searchResults = document.getElementById('search-results');
const searchClear = document.getElementById('search-clear');

function updateSearchClearBtn() {
    if (!searchClear) return;
    if (searchInput.value.trim().length > 0) {
        searchClear.classList.remove('hidden');
    } else {
        searchClear.classList.add('hidden');
    }
}

if (searchClear) {
    searchClear.addEventListener('click', () => {
        searchInput.value = '';
        searchResults.innerHTML = '';
        searchResults.classList.add('hidden');
        searchClear.classList.add('hidden');
        searchInput.focus();
    });
}

function selectSearchResult(f) {
    searchResults.classList.add('hidden');
    searchInput.value = f.properties.Local_Norm || f.properties.Local;
    updateSearchClearBtn();
    
    const coords = f.geometry.coordinates;
    const latlng = L.latLng(coords[1], coords[0]);
    
    if (window.innerWidth <= 768 && sidebar) {
        sidebar.classList.remove('open');
    }
    
    let targetLayer = null;
    if (geojsonLayer) {
        geojsonLayer.eachLayer(layer => {
            if (!targetLayer && layer.feature) {
                const lp = layer.feature.properties || {};
                const fp = f.properties || {};
                if (layer.feature === f || 
                    (lp.Local === fp.Local && lp.Zona === fp.Zona && lp.Municipio === fp.Municipio)) {
                    targetLayer = layer;
                }
            }
        });
    }
    
    selectSchool(f, targetLayer, latlng);
}

let searchDebounceTimer = null;
searchInput.addEventListener('input', function() {
    updateSearchClearBtn();
    clearTimeout(searchDebounceTimer);
    searchDebounceTimer = setTimeout(() => {
        const term = removeAccents(searchInput.value.toLowerCase().trim());
        searchResults.innerHTML = '';
        if (term.length < 3) {
            searchResults.classList.add('hidden');
            return;
        }
        
        const matches = allFeatures.filter(f => {
            return f._searchIndex && f._searchIndex.includes(term);
        }).slice(0, 10);
        
        if (matches.length > 0) {
            matches.forEach(f => {
                const li = document.createElement('li');
                let locString = f.properties.Municipio || '';
                if (f.properties.Bairro) locString += ` - ${f.properties.Bairro}`;
                
                li.innerHTML = `
                    <div style="font-weight: 700; color: #1e293b;">${f.properties.Local_Norm || f.properties.Local}</div>
                    <div style="font-size: 0.75rem; color: #64748b;">${locString}</div>
                `;
                li.addEventListener('click', () => selectSearchResult(f));
                searchResults.appendChild(li);
            });
            searchResults.classList.remove('hidden');
        } else {
            searchResults.classList.add('hidden');
        }
    }, 100);
});

searchInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') {
        const firstLi = searchResults.querySelector('li');
        if (firstLi) firstLi.click();
    }
});

document.addEventListener('click', (e) => {
    if (!e.target.closest('.search-container')) {
        searchResults.classList.add('hidden');
    }
});

// Botão Home (Visão Geral do Ceará)
const btnHome = document.getElementById('btn-home');
if (btnHome) {
    btnHome.addEventListener('click', () => {
        clearSelection();
        map.flyTo([-5.3, -39.3], 7, { duration: 0.75 });
    });
}

// Modal de Ajuda
const btnHelp = document.getElementById('btn-help');
const helpModal = document.getElementById('help-modal');
const closeHelp = document.getElementById('close-help');

if (btnHelp && helpModal) {
    btnHelp.addEventListener('click', () => {
        helpModal.classList.remove('hidden');
    });
}
if (closeHelp && helpModal) {
    closeHelp.addEventListener('click', () => {
        helpModal.classList.add('hidden');
    });
}
if (helpModal) {
    helpModal.addEventListener('click', (e) => {
        if (e.target === helpModal) {
            helpModal.classList.add('hidden');
        }
    });
}

// Controle de Tela Cheia (Fullscreen no Embed)
const btnFullscreen = document.getElementById('btn-fullscreen');
const iconFsEnter = document.getElementById('icon-fs-enter');
const iconFsExit = document.getElementById('icon-fs-exit');

function isFullscreenActive() {
    return !!(document.fullscreenElement || 
              document.webkitFullscreenElement || 
              document.mozFullScreenElement || 
              document.msFullscreenElement);
}

function updateFullscreenState() {
    const isFs = isFullscreenActive();
    if (iconFsEnter && iconFsExit && btnFullscreen) {
        if (isFs) {
            iconFsEnter.style.display = 'none';
            iconFsExit.style.display = 'block';
            btnFullscreen.setAttribute('title', 'Sair da tela cheia');
            btnFullscreen.classList.add('active-fs');
        } else {
            iconFsEnter.style.display = 'block';
            iconFsExit.style.display = 'none';
            btnFullscreen.setAttribute('title', 'Ver em tela cheia');
            btnFullscreen.classList.remove('active-fs');
        }
    }
    // Invalida tamanho do mapa para preencher a nova resolução imediatamente
    setTimeout(() => {
        if (map) map.invalidateSize();
    }, 120);
}

if (btnFullscreen) {
    btnFullscreen.addEventListener('click', () => {
        const docEl = document.documentElement;
        if (!isFullscreenActive()) {
            const reqFs = docEl.requestFullscreen || 
                          docEl.webkitRequestFullscreen || 
                          docEl.mozRequestFullScreen || 
                          docEl.msRequestFullscreen;
            if (reqFs) {
                reqFs.call(docEl).catch(err => {
                    console.warn('Fullscreen bloqueado ou sem permissao no iframe:', err);
                    window.open(window.location.href, '_blank');
                });
            } else {
                window.open(window.location.href, '_blank');
            }
        } else {
            const exitFs = document.exitFullscreen || 
                           document.webkitExitFullscreen || 
                           document.mozCancelFullScreen || 
                           document.msExitFullscreen;
            if (exitFs) {
                exitFs.call(document);
            }
        }
    });
}

document.addEventListener('fullscreenchange', updateFullscreenState);
document.addEventListener('webkitfullscreenchange', updateFullscreenState);
document.addEventListener('mozfullscreenchange', updateFullscreenState);
document.addEventListener('MSFullscreenChange', updateFullscreenState);

// Lógica do Modal de Recomendação de Tela Cheia
const fsPromptModal = document.getElementById('fullscreen-prompt-modal');
const fsPromptClose = document.getElementById('fs-prompt-close');
const fsPromptExpand = document.getElementById('fs-prompt-btn-expand');
const fsPromptDismiss = document.getElementById('fs-prompt-btn-dismiss');

function dismissFsPrompt() {
    if (fsPromptModal) {
        fsPromptModal.classList.add('hidden');
        try {
            sessionStorage.setItem('opovo_fs_prompt_seen', '1');
        } catch(e) {}
    }
}

if (fsPromptClose) fsPromptClose.addEventListener('click', dismissFsPrompt);
if (fsPromptDismiss) fsPromptDismiss.addEventListener('click', dismissFsPrompt);

if (fsPromptExpand) {
    fsPromptExpand.addEventListener('click', () => {
        dismissFsPrompt();
        if (btnFullscreen) {
            btnFullscreen.click();
        }
    });
}

if (fsPromptModal) {
    fsPromptModal.addEventListener('click', (e) => {
        if (e.target === fsPromptModal) {
            dismissFsPrompt();
        }
    });
}

// Dispara a recomendação de tela cheia após carregamento do mapa (se ainda não exibido na sessão)
function maybeShowFullscreenPrompt() {
    try {
        if (sessionStorage.getItem('opovo_fs_prompt_seen') === '1') return;
        if (isFullscreenActive()) return;
    } catch(e) {}
    
    setTimeout(() => {
        if (fsPromptModal && !isFullscreenActive()) {
            fsPromptModal.classList.remove('hidden');
        }
    }, 600);
}
