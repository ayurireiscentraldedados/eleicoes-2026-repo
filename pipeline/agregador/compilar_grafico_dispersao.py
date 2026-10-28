import os
import json
import shutil

# Carregar o JSON dos dados com Votos Válidos
json_path = r'c:\Users\RED.AyuriReis\Downloads\Apurador_real\dados_grafico_dispersao.json'
with open(json_path, 'r', encoding='utf-8') as f:
    estados_data = json.load(f)

json_str = json.dumps(estados_data, ensure_ascii=False)

html_content = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Análise de Dispersão: Pesquisas vs. Média Ponderada vs. Urnas (Votos Válidos)</title>
  <meta name="description" content="Gráfico interativo de dispersão temporal adaptado para a metodologia oficial de votos válidos (TSE), comparando pesquisas de institutos, linha de média móvel ponderada e o resultado das urnas para governador no 1º turno.">
  
  <!-- Google Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@500;600;700;800&display=swap" rel="stylesheet">
  
  <!-- Apache ECharts CDN -->
  <script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>

  <style>
    :root {{
      --bg-main: #090d16;
      --bg-card: rgba(19, 27, 44, 0.75);
      --bg-card-hover: rgba(28, 40, 65, 0.85);
      --border-subtle: rgba(255, 255, 255, 0.08);
      --border-focus: #38bdf8;
      --text-title: #f8fafc;
      --text-body: #94a3b8;
      --text-muted: #64748b;
      --accent-cyan: #38bdf8;
      --accent-purple: #a855f7;
      --accent-gold: #fbbf24;
      --accent-green: #34d399;
      --accent-red: #f87171;
      --radius-lg: 16px;
      --radius-md: 10px;
      --radius-sm: 6px;
      --shadow-glow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
      --transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }}

    * {{
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }}

    body {{
      background: var(--bg-main);
      background-image: 
        radial-gradient(circle at 15% 15%, rgba(56, 189, 248, 0.08) 0%, transparent 40%),
        radial-gradient(circle at 85% 20%, rgba(168, 85, 247, 0.08) 0%, transparent 40%),
        radial-gradient(circle at 50% 80%, rgba(52, 211, 153, 0.05) 0%, transparent 50%);
      color: var(--text-body);
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      min-height: 100vh;
      padding: 24px 20px 48px;
      line-height: 1.5;
    }}

    .container {{
      max-width: 1440px;
      margin: 0 auto;
    }}

    /* Header */
    header {{
      display: flex;
      flex-direction: column;
      gap: 8px;
      margin-bottom: 24px;
    }}

    .badge-pill {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: rgba(56, 189, 248, 0.12);
      border: 1px solid rgba(56, 189, 248, 0.25);
      color: var(--accent-cyan);
      padding: 4px 12px;
      border-radius: 9999px;
      font-size: 0.78rem;
      font-weight: 600;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      width: fit-content;
    }}

    .badge-pill.validos-pill {{
      background: rgba(52, 211, 153, 0.15);
      border-color: rgba(52, 211, 153, 0.35);
      color: #34d399;
    }}

    h1 {{
      font-family: 'Outfit', sans-serif;
      font-size: 2.2rem;
      font-weight: 700;
      color: var(--text-title);
      letter-spacing: -0.02em;
      line-height: 1.2;
    }}

    h1 span {{
      background: linear-gradient(135deg, #38bdf8 0%, #a855f7 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}

    .subtitle {{
      color: var(--text-muted);
      font-size: 0.95rem;
      max-width: 950px;
    }}

    /* Control Panel */
    .controls-panel {{
      background: var(--bg-card);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-lg);
      padding: 20px 24px;
      margin-bottom: 20px;
      box-shadow: var(--shadow-glow);
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }}

    .control-group {{
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }}

    .control-label {{
      font-size: 0.85rem;
      font-weight: 600;
      color: var(--text-title);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}

    select.custom-select {{
      background: #111827;
      border: 1px solid rgba(255, 255, 255, 0.15);
      color: #f8fafc;
      font-family: 'Outfit', sans-serif;
      font-size: 1rem;
      font-weight: 600;
      padding: 10px 36px 10px 14px;
      border-radius: var(--radius-md);
      cursor: pointer;
      outline: none;
      transition: var(--transition);
      appearance: none;
      background-image: url("data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22292.4%22%20height%3D%22292.4%22%3E%3Cpath%20fill%3D%22%2338bdf8%22%20d%3D%22M287%2069.4a17.6%2017.6%200%200%200-13-5.4H18.4c-5%200-9.3%201.8-12.9%205.4A17.6%2017.6%200%200%200%200%2082.2c0%205%201.8%209.3%205.4%2012.9l128%20127.9c3.6%203.6%207.8%205.4%2012.8%205.4s9.2-1.8%2012.8-5.4L287%2095c3.5-3.5%205.4-7.8%205.4-12.8%200-5-1.9-9.2-5.5-12.8z%22%2F%3E%3C%2Fsvg%3E");
      background-repeat: no-repeat;
      background-position: right 14px top 50%;
      background-size: 10px auto;
    }}

    select.custom-select:hover, select.custom-select:focus {{
      border-color: var(--accent-cyan);
      box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.2);
    }}

    /* Toggle segmented buttons */
    .segmented-control {{
      display: inline-flex;
      background: #0f172a;
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 4px;
      gap: 2px;
    }}

    .segmented-btn {{
      background: transparent;
      border: none;
      color: var(--text-muted);
      font-size: 0.85rem;
      font-weight: 500;
      padding: 8px 14px;
      border-radius: var(--radius-sm);
      cursor: pointer;
      transition: var(--transition);
      display: flex;
      align-items: center;
      gap: 6px;
    }}

    .segmented-btn:hover {{
      color: var(--text-title);
    }}

    .segmented-btn.active {{
      background: rgba(52, 211, 153, 0.2);
      color: #34d399;
      font-weight: 700;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
    }}

    .filter-actions {{
      display: flex;
      gap: 8px;
    }}

    .btn-action {{
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--border-subtle);
      color: var(--text-body);
      font-size: 0.8rem;
      font-weight: 600;
      padding: 7px 12px;
      border-radius: var(--radius-sm);
      cursor: pointer;
      transition: var(--transition);
    }}

    .btn-action:hover {{
      background: rgba(255, 255, 255, 0.12);
      color: var(--text-title);
    }}

    /* Candidate Chips Bar */
    .candidates-bar {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 20px;
      align-items: center;
    }}

    .candidate-chip {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 6px 12px;
      border-radius: 9999px;
      font-size: 0.82rem;
      font-weight: 500;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--border-subtle);
      color: var(--text-body);
      cursor: pointer;
      user-select: none;
      transition: var(--transition);
    }}

    .candidate-chip:hover {{
      background: rgba(255, 255, 255, 0.08);
      transform: translateY(-1px);
    }}

    .candidate-chip.active {{
      background: rgba(255, 255, 255, 0.1);
      border-color: currentColor;
      color: var(--text-title);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }}

    .candidate-chip .chip-dot {{
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background-color: currentColor;
    }}

    .candidate-chip .chip-name {{
      font-weight: 600;
    }}

    .candidate-chip .chip-value {{
      font-size: 0.75rem;
      opacity: 0.9;
      background: rgba(0, 0, 0, 0.35);
      padding: 1px 6px;
      border-radius: 999px;
      font-family: 'Outfit', sans-serif;
      font-weight: 700;
    }}

    /* Stats Grid */
    .stats-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
      margin-bottom: 20px;
    }}

    .stat-card {{
      background: var(--bg-card);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-lg);
      padding: 18px 20px;
      box-shadow: var(--shadow-glow);
      transition: var(--transition);
    }}

    .stat-card:hover {{
      border-color: rgba(255, 255, 255, 0.15);
      background: var(--bg-card-hover);
    }}

    .stat-title {{
      font-size: 0.76rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-muted);
      margin-bottom: 6px;
      display: flex;
      align-items: center;
      gap: 6px;
    }}

    .stat-value {{
      font-family: 'Outfit', sans-serif;
      font-size: 1.6rem;
      font-weight: 700;
      color: var(--text-title);
      line-height: 1.2;
    }}

    .stat-desc {{
      font-size: 0.78rem;
      color: var(--text-muted);
      margin-top: 4px;
    }}

    /* Chart Card */
    .chart-card {{
      background: var(--bg-card);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-lg);
      padding: 24px;
      box-shadow: var(--shadow-glow);
      margin-bottom: 24px;
      position: relative;
    }}

    .chart-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
      flex-wrap: wrap;
      gap: 12px;
    }}

    .chart-title-area h2 {{
      font-family: 'Outfit', sans-serif;
      font-size: 1.3rem;
      font-weight: 700;
      color: var(--text-title);
    }}

    .chart-title-area p {{
      font-size: 0.85rem;
      color: var(--text-muted);
    }}

    .chart-legend-visual {{
      display: flex;
      align-items: center;
      gap: 16px;
      font-size: 0.82rem;
      background: rgba(0, 0, 0, 0.3);
      padding: 6px 14px;
      border-radius: 9999px;
      border: 1px solid var(--border-subtle);
      flex-wrap: wrap;
    }}

    .legend-item {{
      display: flex;
      align-items: center;
      gap: 6px;
      color: var(--text-body);
    }}

    .legend-icon-dot {{
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: #38bdf8;
      display: inline-block;
    }}

    .legend-icon-line {{
      width: 18px;
      height: 3px;
      border-radius: 2px;
      background: #38bdf8;
      display: inline-block;
    }}

    .legend-icon-urn {{
      width: 14px;
      height: 14px;
      border-radius: 50%;
      background: #fbbf24;
      border: 2px solid #ffffff;
      box-shadow: 0 0 8px #fbbf24;
      display: inline-block;
    }}

    #main-chart {{
      width: 100%;
      height: 580px;
    }}

    /* Table Section */
    .table-card {{
      background: var(--bg-card);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-lg);
      padding: 24px;
      box-shadow: var(--shadow-glow);
    }}

    .table-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
      flex-wrap: wrap;
      gap: 12px;
    }}

    .table-header h2 {{
      font-family: 'Outfit', sans-serif;
      font-size: 1.25rem;
      font-weight: 700;
      color: var(--text-title);
    }}

    .table-responsive {{
      overflow-x: auto;
    }}

    table.custom-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.9rem;
      text-align: left;
    }}

    table.custom-table th {{
      background: rgba(15, 23, 42, 0.7);
      padding: 12px 14px;
      font-weight: 600;
      color: var(--text-title);
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      white-space: nowrap;
    }}

    table.custom-table td {{
      padding: 14px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
      color: var(--text-body);
      white-space: nowrap;
    }}

    table.custom-table tr:hover td {{
      background: rgba(255, 255, 255, 0.03);
    }}

    .badge-diff {{
      display: inline-block;
      padding: 3px 8px;
      border-radius: 6px;
      font-weight: 700;
      font-size: 0.8rem;
      font-family: 'Outfit', sans-serif;
    }}

    .badge-diff.positive {{
      background: rgba(52, 211, 153, 0.15);
      color: #34d399;
      border: 1px solid rgba(52, 211, 153, 0.3);
    }}

    .badge-diff.negative {{
      background: rgba(248, 113, 113, 0.15);
      color: #f87171;
      border: 1px solid rgba(248, 113, 113, 0.3);
    }}

    .badge-diff.neutral {{
      background: rgba(148, 163, 184, 0.15);
      color: #94a3b8;
    }}

    .candidate-cell {{
      display: flex;
      align-items: center;
      gap: 10px;
    }}

    .cand-color-bar {{
      width: 4px;
      height: 24px;
      border-radius: 2px;
    }}

    /* Tooltip styling */
    .echarts-tooltip-custom {{
      font-family: 'Inter', sans-serif;
      padding: 10px 14px;
      line-height: 1.4;
    }}

    @media (max-width: 900px) {{
      h1 {{ font-size: 1.7rem; }}
      .controls-panel {{ flex-direction: column; align-items: stretch; }}
      .control-group {{ flex-direction: column; align-items: stretch; }}
      #main-chart {{ height: 450px; }}
    }}
  </style>
</head>
<body>

<div class="container">
  
  <!-- Header -->
  <header>
    <div style="display:flex; gap:8px; align-items:center; flex-wrap:wrap;">
      <div class="badge-pill validos-pill">
        <span>✅ Metodologia Adaptada: Votos Válidos (TSE)</span>
      </div>
      <div class="badge-pill">
        <span>🇧🇷 1º Turno Governadores</span>
      </div>
    </div>
    <h1>Agregador de Pesquisas <span>× Urnas Oficiais</span></h1>
    <p class="subtitle">
      Todas as pesquisas individuais dos institutos foram <strong>recalculadas para a metodologia oficial de votos válidos</strong> (excluindo brancos, nulos e indecisos do denominador). Compare a trajetória da <strong>Média Móvel Ponderada</strong> (linha contínua) com as <strong>pesquisas</strong> (bolinhas de dispersão) e a confirmação das <strong>Urnas no dia da eleição (bolinha de destaque)</strong>.
    </p>
  </header>

  <!-- Controls Panel -->
  <div class="controls-panel">
    <div class="control-group">
      <span class="control-label">Estado:</span>
      <select id="state-select" class="custom-select" aria-label="Selecione o Estado">
        <!-- Preenchido via JS -->
      </select>
    </div>

    <div class="control-group">
      <span class="control-label">Metodologia:</span>
      <div class="segmented-control" role="group" aria-label="Métrica de comparação das pesquisas e urnas">
        <button id="metric-valid-btn" class="segmented-btn active" onclick="switchMetric('pct_validos')">
          <span>🗳️ Votos Válidos</span>
          <span style="font-size:0.7rem; opacity:0.85;">(Critério Oficial TSE)</span>
        </button>
        <button id="metric-total-btn" class="segmented-btn" onclick="switchMetric('pct_total')">
          <span>📊 Votos Totais</span>
          <span style="font-size:0.7rem; opacity:0.85;">(Estimulada c/ Brancos/Nulos)</span>
        </button>
      </div>
    </div>

    <div class="filter-actions">
      <button class="btn-action" onclick="selectAllCandidates()">Todos os Candidatos</button>
      <button class="btn-action" onclick="selectTopCandidates(3)">Top 3 Disputa</button>
    </div>
  </div>

  <!-- Candidates Active Filter Bar -->
  <div class="candidates-bar" id="candidates-chips">
    <!-- Gerado dinamicamente -->
  </div>

  <!-- Stats Grid -->
  <div class="stats-grid">
    <div class="stat-card">
      <div class="stat-title">
        <span>📊 Total de Pesquisas</span>
      </div>
      <div class="stat-value" id="stat-total-polls">0</div>
      <div class="stat-desc" id="stat-institutes-desc">0 institutos analisados</div>
    </div>

    <div class="stat-card">
      <div class="stat-title">
        <span>🎯 Erro Médio (MAE)</span>
      </div>
      <div class="stat-value" id="stat-mae">0.0 p.p.</div>
      <div class="stat-desc" id="stat-mae-desc">Diferença em Votos Válidos</div>
    </div>

    <div class="stat-card">
      <div class="stat-title">
        <span>❓ Indecisos na Véspera</span>
      </div>
      <div class="stat-value" id="stat-undecided">0.0%</div>
      <div class="stat-desc">Votos convertidos na véspera</div>
    </div>

    <div class="stat-card">
      <div class="stat-title">
        <span>🏆 Vencedor nas Urnas</span>
      </div>
      <div class="stat-value" id="stat-winner" style="font-size: 1.3rem;">-</div>
      <div class="stat-desc" id="stat-winner-pct">0% dos votos apurados</div>
    </div>
  </div>

  <!-- Main Chart Card -->
  <div class="chart-card">
    <div class="chart-header">
      <div class="chart-title-area">
        <h2 id="chart-main-title">Evolução Temporal em Votos Válidos e Resultado Final</h2>
        <p id="chart-main-subtitle">Todas as pesquisas projetadas em 100% de votos válidos para confronto direto com o resultado oficial do TSE</p>
      </div>

      <div class="chart-legend-visual">
        <div class="legend-item">
          <span class="legend-icon-dot"></span>
          <span>Pesquisa Individual</span>
        </div>
        <div class="legend-item">
          <span class="legend-icon-line"></span>
          <span>Média Ponderada</span>
        </div>
        <div class="legend-item">
          <span class="legend-icon-urn"></span>
          <span style="font-weight:700; color:#fbbf24;">Resultado da Urna (04/10)</span>
        </div>
      </div>
    </div>

    <div id="main-chart"></div>
  </div>

  <!-- Comparison Audit Table -->
  <div class="table-card">
    <div class="table-header">
      <h2 id="table-main-title">Tabela de Auditoria em Votos Válidos: Véspera vs. Urnas Oficiais</h2>
      <span style="font-size:0.8rem; color:var(--text-muted);">Soma dos votos válidos = 100%</span>
    </div>
    <div class="table-responsive">
      <table class="custom-table" id="audit-table">
        <thead>
          <tr>
            <th>Candidato</th>
            <th>Partido</th>
            <th>Situação</th>
            <th id="table-th-media">Média Véspera (Válidos)</th>
            <th id="table-th-urna">Resultado Urna (Válidos)</th>
            <th id="table-th-diff">Diferença (Urna - Média)</th>
            <th>Votos Absolutos</th>
            <th>Pesquisas Registradas</th>
          </tr>
        </thead>
        <tbody id="audit-tbody">
          <!-- Preenchido via JS -->
        </tbody>
      </table>
    </div>
  </div>

</div>

<!-- Dados JSON Incorporados -->
<script id="dados-agregador" type="application/json">
{json_str}
</script>

<script>
  // Paleta de cores vibrantes para candidatos
  const COLOR_PALETTE = [
    '#38bdf8', // Cyan
    '#ef4444', // Vermelho (PT, etc)
    '#3b82f6', // Azul (PSDB, etc)
    '#10b981', // Verde esmeralda (PL/MDB)
    '#f59e0b', // Âmbar (PDT, etc)
    '#a855f7', // Roxo (União Brasil)
    '#ec4899', // Rosa (PSD/outros)
    '#14b8a6', // Teal
    '#f97316', // Laranja
    '#6366f1', // Indigo
    '#84cc16', // Lima
    '#94a3b8'  // Cinza (Brancos/Nulos/Indecisos)
  ];

  // Carregar dados
  const RAW_DATA = JSON.parse(document.getElementById('dados-agregador').textContent);
  const STATES = Object.keys(RAW_DATA).sort();

  let currentState = STATES.includes('Ceará') ? 'Ceará' : STATES[0];
  let currentMetric = 'pct_validos'; // PADRÃO: VOTOS VÁLIDOS!
  let activeCandidates = new Set();
  let myChart = null;

  document.addEventListener('DOMContentLoaded', () => {{
    initSelect();
    initChart();
    loadState(currentState);

    window.addEventListener('resize', () => {{
      if (myChart) myChart.resize();
    }});
  }});

  function initSelect() {{
    const select = document.getElementById('state-select');
    select.innerHTML = '';
    STATES.forEach(st => {{
      const opt = document.createElement('option');
      opt.value = st;
      opt.textContent = st;
      if (st === currentState) opt.selected = true;
      select.appendChild(opt);
    }});

    select.addEventListener('change', (e) => {{
      currentState = e.target.value;
      loadState(currentState);
    }});
  }}

  function initChart() {{
    const chartDom = document.getElementById('main-chart');
    myChart = echarts.init(chartDom, 'dark', {{
      renderer: 'canvas'
    }});
  }}

  function switchMetric(metric) {{
    currentMetric = metric;
    document.getElementById('metric-valid-btn').classList.toggle('active', metric === 'pct_validos');
    document.getElementById('metric-total-btn').classList.toggle('active', metric === 'pct_total');
    
    if (metric === 'pct_validos') {{
      document.getElementById('table-th-media').textContent = 'Média Véspera (Válidos)';
      document.getElementById('table-th-urna').textContent = 'Resultado Urna (Válidos)';
      document.getElementById('table-main-title').textContent = 'Tabela de Auditoria em Votos Válidos: Véspera vs. Urnas Oficiais';
      document.getElementById('stat-mae-desc').textContent = 'Diferença em Votos Válidos';
      document.getElementById('chart-main-subtitle').textContent = 'Todas as pesquisas projetadas em 100% de votos válidos para confronto direto com o TSE';
    }} else {{
      document.getElementById('table-th-media').textContent = 'Média Véspera (Total)';
      document.getElementById('table-th-urna').textContent = 'Resultado Urna (% Total Apurado)';
      document.getElementById('table-main-title').textContent = 'Tabela de Auditoria: Votos Totais com Brancos e Nulos';
      document.getElementById('stat-mae-desc').textContent = 'Diferença em Votos Totais';
      document.getElementById('chart-main-subtitle').textContent = 'Intenções de voto estimuladas tradicionais com brancos, nulos e indecisos';
    }}

    const stData = RAW_DATA[currentState];
    // Em votos válidos, seleciona apenas candidatos válidos por padrão
    if (metric === 'pct_validos') {{
      activeCandidates = new Set(stData.candidatos_lista.filter(c => !c.includes('Indeciso') && !c.includes('Branco')));
    }} else {{
      activeCandidates = new Set(stData.candidatos_lista);
    }}

    updateStats(stData);
    renderChips(stData);
    renderChart();
    renderTable();
  }}

  function loadState(stateName) {{
    const stData = RAW_DATA[stateName];
    if (!stData) return;

    if (currentMetric === 'pct_validos') {{
      activeCandidates = new Set(stData.candidatos_lista.filter(c => !c.includes('Indeciso') && !c.includes('Branco')));
    }} else {{
      activeCandidates = new Set(stData.candidatos_lista);
    }}

    updateStats(stData);
    renderChips(stData);
    renderChart();
    renderTable();
  }}

  function updateStats(stData) {{
    document.getElementById('stat-total-polls').textContent = stData.total_pesquisas_datas;
    document.getElementById('stat-institutes-desc').textContent = `${{stData.institutos.length}} institutos (${{stData.institutos.slice(0, 3).join(', ')}}${{stData.institutos.length > 3 ? '...' : ''}})`;

    const indecisos = stData.candidatos['Indecisos / Não sabe'];
    const ultIndecisos = indecisos && indecisos.ultima_media_total !== null ? indecisos.ultima_media_total : 0;
    document.getElementById('stat-undecided').textContent = `${{ultIndecisos.toFixed(1)}}%`;

    let winner = null;
    let maxPct = -1;
    let errors = [];

    stData.candidatos_lista.forEach(candName => {{
      const cand = stData.candidatos[candName];
      if (cand.resultado_urna && cand.resultado_urna.pct_validos > maxPct && candName !== 'Branco/Nulo') {{
        maxPct = cand.resultado_urna.pct_validos;
        winner = cand;
      }}
      if (cand.resultado_urna) {{
        const targetPct = currentMetric === 'pct_validos' ? cand.resultado_urna.pct_validos : cand.resultado_urna.pct_total;
        const mediaVal = currentMetric === 'pct_validos' ? cand.ultima_media_validos : cand.ultima_media_total;
        if (targetPct > 0 && mediaVal !== null) {{
          errors.push(Math.abs(targetPct - mediaVal));
        }}
      }}
    }});

    if (winner) {{
      document.getElementById('stat-winner').textContent = winner.nome;
      const pctDisplay = currentMetric === 'pct_validos' ? winner.resultado_urna.pct_validos : winner.resultado_urna.pct_total;
      document.getElementById('stat-winner-pct').textContent = `${{pctDisplay.toFixed(2)}}% ${{currentMetric === 'pct_validos' ? 'válidos' : 'total'}} • ${{winner.resultado_urna.partido || ''}}`;
    }} else {{
      document.getElementById('stat-winner').textContent = '-';
      document.getElementById('stat-winner-pct').textContent = '';
    }}

    const mae = errors.length > 0 ? (errors.reduce((a, b) => a + b, 0) / errors.length).toFixed(2) : '0.00';
    document.getElementById('stat-mae').textContent = `${{mae}} p.p.`;
    document.getElementById('chart-main-title').textContent = `${{stData.estado}}: Evolução Temporal em ${{currentMetric === 'pct_validos' ? 'Votos Válidos' : 'Votos Totais'}}`;
  }}

  function getCandidateColor(candName, index) {{
    if (candName.includes('Branco') || candName.includes('Nulo')) return '#94a3b8';
    if (candName.includes('Indeciso')) return '#64748b';
    return COLOR_PALETTE[index % COLOR_PALETTE.length];
  }}

  function renderChips(stData) {{
    const container = document.getElementById('candidates-chips');
    container.innerHTML = '';

    stData.candidatos_lista.forEach((candName, idx) => {{
      const cand = stData.candidatos[candName];
      
      // Se estiver em votos válidos, esconde opções de branco/nulo/indeciso se não tiverem valor válido
      if (currentMetric === 'pct_validos' && (!cand.is_valid_cand || candName.includes('Indeciso') || candName.includes('Branco'))) {{
        return;
      }}

      const color = getCandidateColor(candName, idx);
      const isActive = activeCandidates.has(candName);

      const chip = document.createElement('div');
      chip.className = `candidate-chip ${{isActive ? 'active' : ''}}`;
      chip.style.color = color;
      
      const dot = document.createElement('span');
      dot.className = 'chip-dot';

      const nameSpan = document.createElement('span');
      nameSpan.className = 'chip-name';
      nameSpan.textContent = candName;

      chip.appendChild(dot);
      chip.appendChild(nameSpan);

      if (cand.resultado_urna) {{
        const targetPct = currentMetric === 'pct_validos' ? cand.resultado_urna.pct_validos : cand.resultado_urna.pct_total;
        const valSpan = document.createElement('span');
        valSpan.className = 'chip-value';
        valSpan.textContent = `${{targetPct.toFixed(1)}}%`;
        chip.appendChild(valSpan);
      }}

      chip.addEventListener('click', () => {{
        if (activeCandidates.has(candName)) {{
          if (activeCandidates.size > 1) {{
            activeCandidates.delete(candName);
          }}
        }} else {{
          activeCandidates.add(candName);
        }}
        chip.classList.toggle('active', activeCandidates.has(candName));
        renderChart();
      }});

      container.appendChild(chip);
    }});
  }}

  function selectAllCandidates() {{
    const stData = RAW_DATA[currentState];
    if (currentMetric === 'pct_validos') {{
      activeCandidates = new Set(stData.candidatos_lista.filter(c => !c.includes('Indeciso') && !c.includes('Branco')));
    }} else {{
      activeCandidates = new Set(stData.candidatos_lista);
    }}
    renderChips(stData);
    renderChart();
  }}

  function selectTopCandidates(n) {{
    const stData = RAW_DATA[currentState];
    const top = stData.candidatos_lista.filter(c => !c.includes('Indeciso') && !c.includes('Branco')).slice(0, n);
    activeCandidates = new Set(top);
    renderChips(stData);
    renderChart();
  }}

  function renderChart() {{
    if (!myChart) return;

    const stData = RAW_DATA[currentState];
    const series = [];

    stData.candidatos_lista.forEach((candName, idx) => {{
      if (!activeCandidates.has(candName)) return;

      const cand = stData.candidatos[candName];
      const color = getCandidateColor(candName, idx);

      // 1. Linha da Média Ponderada
      if (cand.media_ponderada && cand.media_ponderada.length > 0) {{
        const linePoints = cand.media_ponderada.map(p => {{
          const yVal = currentMetric === 'pct_validos' ? p.valor_validos : p.valor;
          return [p.data, yVal];
        }});
        
        series.push({{
          name: candName,
          type: 'line',
          smooth: true,
          showSymbol: false,
          data: linePoints,
          lineStyle: {{
            width: 3.5,
            color: color,
            shadowColor: color,
            shadowBlur: 6
          }},
          itemStyle: {{ color: color }},
          z: 3
        }});
      }}

      // 2. Bolinhas de Dispersão das Pesquisas Individuais (Adaptadas para Válidos)
      if (cand.pesquisas && cand.pesquisas.length > 0) {{
        const scatterData = cand.pesquisas.map(p => {{
          const yVal = currentMetric === 'pct_validos' ? p.valor_validos : p.valor;
          return {{
            value: [p.data, yVal],
            instituto: p.instituto,
            data_str: p.data_str,
            partido: p.partido,
            candidato: candName,
            color: color,
            valor_original: p.valor,
            valor_validos: p.valor_validos
          }};
        }});

        series.push({{
          name: `${{candName}} (Pesquisas)`,
          type: 'scatter',
          symbolSize: 8,
          data: scatterData,
          itemStyle: {{
            color: color,
            opacity: 0.68,
            borderColor: 'rgba(255, 255, 255, 0.45)',
            borderWidth: 1
          }},
          z: 2
        }});
      }}

      // 3. Bolinha de Destaque Oficial das Urnas (04/10/2026)
      if (cand.resultado_urna) {{
        const urnaPct = currentMetric === 'pct_validos' ? cand.resultado_urna.pct_validos : cand.resultado_urna.pct_total;
        
        series.push({{
          name: `${{candName}} (Urnas)`,
          type: 'scatter',
          symbol: 'circle',
          symbolSize: 18,
          data: [{{
            value: [cand.resultado_urna.data, urnaPct],
            urna_info: cand.resultado_urna,
            candidato: candName,
            color: color
          }}],
          itemStyle: {{
            color: color,
            borderColor: '#fbbf24',
            borderWidth: 3.5,
            shadowColor: '#fbbf24',
            shadowBlur: 16
          }},
          z: 10
        }});
      }}
    }});

    const metricUnit = currentMetric === 'pct_validos' ? '% dos votos válidos' : '% total';

    const option = {{
      backgroundColor: 'transparent',
      animationDuration: 600,
      tooltip: {{
        trigger: 'item',
        backgroundColor: 'rgba(15, 23, 42, 0.95)',
        borderColor: 'rgba(255, 255, 255, 0.15)',
        borderWidth: 1,
        textStyle: {{ color: '#f8fafc', fontSize: 13 }},
        formatter: function(params) {{
          // Ponto de destaque das Urnas
          if (params.data && params.data.urna_info) {{
            const info = params.data.urna_info;
            const candName = params.data.candidato;
            const targetPct = currentMetric === 'pct_validos' ? info.pct_validos : info.pct_total;
            const metricLabel = currentMetric === 'pct_validos' ? 'Votos Válidos (TSE Oficial)' : '% Total Apurado';
            
            const stCand = stData.candidatos[candName];
            let diffHtml = '';
            if (stCand) {{
              const ultMedia = currentMetric === 'pct_validos' ? stCand.ultima_media_validos : stCand.ultima_media_total;
              if (ultMedia !== null) {{
                const diff = targetPct - ultMedia;
                const sign = diff >= 0 ? '+' : '';
                const diffClass = diff >= 0 ? '#34d399' : '#f87171';
                diffHtml = `<div style="margin-top:6px; padding-top:6px; border-top:1px dashed rgba(255,255,255,0.15); font-size:12px;">
                  Média Ponderada Véspera: <strong>${{ultMedia.toFixed(2)}}%</strong><br>
                  Desvio Urna vs. Média: <strong style="color:${{diffClass}}">${{sign}}${{diff.toFixed(2)}} p.p.</strong>
                </div>`;
              }}
            }}

            return `<div class="echarts-tooltip-custom">
              <div style="display:flex; align-items:center; gap:6px; margin-bottom:4px;">
                <span style="background:#fbbf24; color:#0f172a; padding:2px 6px; border-radius:4px; font-weight:800; font-size:11px;">🗳️ URNA OFICIAL</span>
                <span style="color:#94a3b8; font-size:12px;">04/10/2026</span>
              </div>
              <div style="font-weight:700; font-size:15px; color:${{params.data.color}}">${{candName}} ${{info.partido ? `(${{info.partido}})` : ''}}</div>
              <div style="font-size:18px; font-weight:800; color:#f8fafc; margin:4px 0;">${{targetPct.toFixed(2)}}% <span style="font-size:11px; font-weight:500; color:#34d399;">${{metricLabel}}</span></div>
              <div style="color:#94a3b8; font-size:12px;">Total de Votos: <strong style="color:#f8fafc;">${{info.votos.toLocaleString('pt-BR')}}</strong></div>
              ${{diffHtml}}
            </div>`;
          }}

          // Pesquisa Individual
          if (params.data && params.data.instituto) {{
            const p = params.data;
            const extraEstimulada = currentMetric === 'pct_validos' 
              ? `<div style="font-size:11px; color:#94a3b8; margin-top:2px;">(Estimulada c/ brancos/nulos: ${{p.valor_original.toFixed(2)}}%)</div>`
              : '';

            return `<div class="echarts-tooltip-custom">
              <div style="display:flex; align-items:center; gap:6px; margin-bottom:4px;">
                <span style="background:rgba(56,189,248,0.2); color:#38bdf8; padding:2px 6px; border-radius:4px; font-weight:600; font-size:11px;">🏢 ${{p.instituto}}</span>
                <span style="color:#94a3b8; font-size:12px;">${{p.data_str}}</span>
              </div>
              <div style="font-weight:700; font-size:14px; color:${{p.color}}">${{p.candidato}}</div>
              <div style="font-size:16px; font-weight:800; color:#f8fafc; margin-top:2px;">${{params.data.value[1].toFixed(2)}}% <span style="font-size:11px; font-weight:400; color:#34d399;">${{currentMetric === 'pct_validos' ? 'válidos' : 'total'}}</span></div>
              ${{extraEstimulada}}
            </div>`;
          }}

          // Linha da Média Ponderada
          if (params.seriesType === 'line') {{
            return `<div class="echarts-tooltip-custom">
              <div style="color:#94a3b8; font-size:11px; text-transform:uppercase;">📈 Média Móvel Ponderada (${{currentMetric === 'pct_validos' ? 'Válidos' : 'Total'}})</div>
              <div style="font-weight:700; font-size:14px; color:${{params.color}}">${{params.seriesName}}</div>
              <div style="font-size:16px; font-weight:800; color:#f8fafc; margin-top:2px;">${{params.data[1].toFixed(2)}}%</div>
              <div style="color:#94a3b8; font-size:11px;">Data: ${{params.data[0]}}</div>
            </div>`;
          }}

          return '';
        }}
      }},
      grid: {{
        left: '2%',
        right: '4%',
        bottom: '15%',
        top: '6%',
        containLabel: true
      }},
      xAxis: {{
        type: 'time',
        boundaryGap: ['2%', '4%'],
        axisLine: {{ lineStyle: {{ color: 'rgba(255, 255, 255, 0.15)' }} }},
        splitLine: {{ lineStyle: {{ color: 'rgba(255, 255, 255, 0.05)' }} }},
        axisLabel: {{
          color: '#94a3b8',
          formatter: '{{dd}}/{{MM}}'
        }}
      }},
      yAxis: {{
        type: 'value',
        axisLine: {{ lineStyle: {{ color: 'rgba(255, 255, 255, 0.15)' }} }},
        splitLine: {{ lineStyle: {{ color: 'rgba(255, 255, 255, 0.06)' }} }},
        axisLabel: {{
          color: '#94a3b8',
          formatter: '{{value}}%'
        }}
      }},
      dataZoom: [
        {{
          type: 'slider',
          show: true,
          xAxisIndex: [0],
          start: 0,
          end: 100,
          bottom: 12,
          height: 24,
          borderColor: 'transparent',
          backgroundColor: 'rgba(15, 23, 42, 0.6)',
          fillerColor: 'rgba(52, 211, 153, 0.2)',
          handleStyle: {{
            color: '#34d399',
            borderColor: '#ffffff',
            borderWidth: 1
          }},
          textStyle: {{ color: '#94a3b8' }}
        }},
        {{
          type: 'inside',
          xAxisIndex: [0]
        }}
      ],
      series: series
    }};

    myChart.setOption(option, true);
  }}

  function renderTable() {{
    const stData = RAW_DATA[currentState];
    const tbody = document.getElementById('audit-tbody');
    tbody.innerHTML = '';

    stData.candidatos_lista.forEach((candName, idx) => {{
      const cand = stData.candidatos[candName];
      
      // Ocultar da tabela opções não válidas quando em modo válidos
      if (currentMetric === 'pct_validos' && (!cand.is_valid_cand || candName.includes('Indeciso') || candName.includes('Branco'))) {{
        return;
      }}

      const color = getCandidateColor(candName, idx);
      const tr = document.createElement('tr');

      // 1. Candidato
      const tdCand = document.createElement('td');
      tdCand.innerHTML = `
        <div class="candidate-cell">
          <div class="cand-color-bar" style="background:${{color}}"></div>
          <div>
            <div style="font-weight:600; color:#f8fafc;">${{candName}}</div>
          </div>
        </div>
      `;

      // 2. Partido
      const tdPart = document.createElement('td');
      tdPart.textContent = cand.resultado_urna && cand.resultado_urna.partido ? cand.resultado_urna.partido : '-';

      // 3. Situação
      const tdSit = document.createElement('td');
      const sit = cand.resultado_urna && cand.resultado_urna.situacao ? cand.resultado_urna.situacao : '-';
      tdSit.innerHTML = sit === 'Eleito' 
        ? `<span style="color:#34d399; font-weight:700;">👑 Eleito</span>`
        : `<span style="color:#94a3b8;">${{sit}}</span>`;

      // 4. Média Ponderada
      const tdMedia = document.createElement('td');
      const ultMedia = currentMetric === 'pct_validos' ? cand.ultima_media_validos : cand.ultima_media_total;
      tdMedia.textContent = ultMedia !== null ? `${{ultMedia.toFixed(2)}}%` : '-';
      tdMedia.style.fontFamily = "'Outfit', sans-serif";
      tdMedia.style.fontWeight = '600';

      // 5. Resultado Urna
      const tdUrna = document.createElement('td');
      let targetPct = null;
      if (cand.resultado_urna) {{
        targetPct = currentMetric === 'pct_validos' ? cand.resultado_urna.pct_validos : cand.resultado_urna.pct_total;
        tdUrna.textContent = `${{targetPct.toFixed(2)}}%`;
      }} else {{
        tdUrna.textContent = '-';
      }}
      tdUrna.style.fontFamily = "'Outfit', sans-serif";
      tdUrna.style.fontWeight = '700';
      tdUrna.style.color = '#fbbf24';

      // 6. Diferença
      const tdDiff = document.createElement('td');
      if (targetPct !== null && ultMedia !== null) {{
        const diff = targetPct - ultMedia;
        const sign = diff > 0 ? '+' : '';
        const diffClass = Math.abs(diff) < 0.5 ? 'neutral' : (diff > 0 ? 'positive' : 'negative');
        tdDiff.innerHTML = `<span class="badge-diff ${{diffClass}}">${{sign}}${{diff.toFixed(2)}} p.p.</span>`;
      }} else {{
        tdDiff.textContent = '-';
      }}

      // 7. Votos Absolutos
      const tdVotos = document.createElement('td');
      tdVotos.textContent = cand.resultado_urna && cand.resultado_urna.votos 
        ? cand.resultado_urna.votos.toLocaleString('pt-BR') 
        : '-';

      // 8. Qtd Pesquisas
      const tdQtd = document.createElement('td');
      tdQtd.textContent = `${{cand.qtd_pesquisas}} pesquisas`;

      tr.appendChild(tdCand);
      tr.appendChild(tdPart);
      tr.appendChild(tdSit);
      tr.appendChild(tdMedia);
      tr.appendChild(tdUrna);
      tr.appendChild(tdDiff);
      tr.appendChild(tdVotos);
      tr.appendChild(tdQtd);

      tbody.appendChild(tr);
    }});
  }}
</script>

</body>
</html>
'''

output_html_scratch = r'C:\Users\RED.AyuriReis\.gemini\antigravity-ide\scratch\nexo_map\grafico_dispersao_governadores.html'
with open(output_html_scratch, 'w', encoding='utf-8') as f:
    f.write(html_content)

output_html_apurador = r'c:\Users\RED.AyuriReis\Downloads\Apurador_real\grafico_dispersao_governadores.html'
shutil.copy2(output_html_scratch, output_html_apurador)

print(f"Página HTML atualizada com metodologia de VOTOS VÁLIDOS:")
print(f"1. {output_html_scratch}")
print(f"2. {output_html_apurador}")
