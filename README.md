# 🗳️ Cobertura Eleitoral Ceará & Brasil — Central de Dados O POVO

[![Live Demo](https://img.shields.io/badge/Demo%20Online-mapa--ceara--presidente-brightgreen?style=for-the-badge&logo=google-chrome)](https://mapa-ceara-presidente.web.app)
[![Data Journalism](https://img.shields.io/badge/Jornalismo%20de%20Dados-O%20POVO-orange?style=for-the-badge)](https://opovo.com.br)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)](https://python.org)
[![Leaflet](https://img.shields.io/badge/Leaflet-1.9.4-199900?style=for-the-badge&logo=leaflet)](https://leafletjs.com)
[![Open Data](https://img.shields.io/badge/Dados%20Abertos-TSE%20Oficial-red?style=for-the-badge)](https://dadosabertos.tse.jus.br/)

Repositório oficial dos pipelines de engenharia de dados, modelos de agregação de pesquisas, análises espaciais urna a urna e aplicação web interativa desenvolvidos para a **Central de Dados do Grupo O POVO** na cobertura das Eleições Presidenciais e Estaduais de 2026.

---

## 📌 Visão Geral do Projeto

Esta cobertura combinou **Engenharia de Dados**, **Jornalismo Investigativo Guiado por Dados** e **Visualização Web de Alta Performance (60 FPS)** em três momentos cruciais do ciclo eleitoral:

1. **Pré-Eleição (Agregador de Pesquisas):** Modelo de ponderação e análise de tendências de institutos de pesquisa eleitoral, com gráficos de dispersão e cruzamento posterior de acurácia contra o resultado das urnas.
2. **Apuração em Tempo Real (Urna a Urna):** Pipelines assíncronos de ingestão direta da API oficial de divulgação do Tribunal Superior Eleitoral (TSE), com monitoramento de totalizações nacionais, estaduais e do exterior.
3. **Mapeamento de Microdados no Ceará (6.647 Locais de Votação):** Mapeamento geográfico interativo de cada escola, colégio e seção eleitoral em todos os 184 municípios cearenses, com comparativo direto do 1º para o 2º Turno, cálculo de saldo em pontos percentuais (pp) e identificação de viradas históricas.

---

## 🗺️ Aplicação Web Interativa

> **Acesse a aplicação em produção:** [mapa-ceara-presidente.web.app](https://mapa-ceara-presidente.web.app)

* **Performance Extrema:** Renderização via **HTML5 Canvas API** integrada ao Leaflet.js, permitindo renderizar mais de 6.600 pontos com raio dinâmico e sem travamento de DOM (mantendo taxa constante de 60 FPS).
* **Busca Instantânea em Memória:** Normalização de strings e indexação sem acentos de todos os colégios, permitindo busca em tempo real em menos de 10 milissegundos.
* **UX Adaptativa:** Bottom sheet inteligente no mobile com suporte a Tela Cheia nativa e popups detalhados com foto dos candidatos, barras percentuais e saldo de votos.

---

## 📁 Estrutura do Repositório

```text
eleicoes-2026-repo/
├── frontend/                     # Aplicação Web do Mapa Interativo
│   ├── index.html                # Estrutura semântica, cards de resumo e modais
│   ├── style.css                 # Design responsivo, tipografia O POVO e temas
│   ├── script.js                 # Lógica do mapa Leaflet Canvas, busca e transições
│   ├── lula.jpg / flavio.jpg     # Imagens dos candidatos para os cards
│   ├── mapa_presidente_1turno.geojson  # Microdados de 6.647 locais (1º Turno)
│   ├── mapa_presidente_2turno.geojson  # Microdados de 6.647 locais (2º Turno)
│   ├── fortaleza_bairros.geojson       # Delimitação vetorial dos bairros de Fortaleza
│   └── ce_municipios.geojson           # Delimitação dos 184 municípios cearenses
│
├── pipeline/                     # Pipelines de Extração, Transformação e Carga (ETL)
│   ├── agregador/                # Agregador de pesquisas e comparativo com urnas
│   │   ├── analisar_governadores_pesquisas.py
│   │   ├── comparar_pesquisas_urnas.py
│   │   ├── compilar_grafico_dispersao.py
│   │   └── grafico_dispersao_plotly.py
│   ├── apuracao_tse/             # Ingestão em tempo real da API do TSE
│   │   ├── coletor_api_2turno.py
│   │   ├── coletor_presidente_municipios_2turno.py
│   │   ├── coletor_presidente_exterior_2turno.py
│   │   └── banco_apuracao.py
│   └── espacial_ceara/           # Cruzamento geográfico e análises de locais
│       ├── gerar_csv_viradas.py
│       ├── extrair_dados_relatorio.py
│       ├── compilar_pdf_direto.py
│       └── cria_mapas_pres.py
│
├── data/                         # Bases de Dados Abertas Consolidadas
│   ├── dados_secoes_ceara_presidente_1Te2T.csv           # 6.647 locais completos
│   ├── 71_locais_votacao_virada_ceara_presidente_2026.csv # As 71 escolas de virada
│   ├── comparativo_agregador_pesquisas_x_urnas.csv       # Validação das pesquisas
│   └── acuracia_agregador_por_estado.csv                 # Resumo por UF
│
└── reports/                      # Relatórios Editoriais Prontos
    ├── Relatorio_Eleicoes_Ceara_2026_Locais_de_Votacao_OPOVO.pdf # Memo editorial
    └── relatorio_eleicoes_ceara_direto.html
```

---

## 🔍 Destaques e Pautas Reveladas pelos Dados

A partir do cruzamento dos microdados de todas as urnas do Ceará, a equipe levantou pautas exclusivas:

* **Os 71 Locais da Virada:** Em todo o Ceará, exatamente 71 colégios eleitorais mudaram de vencedor entre os turnos — em todos eles, Flávio Bolsonaro liderava no 1º Turno e Lula virou no 2º Turno.
* **O Epicentro da Polarização:** Identificação das escolas de Fortaleza onde a disputa se deu voto a voto (como o Colégio Ari de Sá na Aldeota e o Christus Dionísio Torres), registrando diferenças mínimas em colégios com mais de 4 mil eleitores.
* **Dinâmica do Crescimento de Votos Novos:**
  * Lula: ampliou a votação em **+480.861 votos** (+5,64 pontos percentuais).
  * Flávio Bolsonaro: cresceu **+62.628 votos** (-0,20 pp na fatia proporcional válida).

---

## 🚀 Como Executar Localmente

### 1. Clonar o Repositório
```bash
git clone https://github.com/ayurireiscentraldedados/eleicoes-2026-repo.git
cd eleicoes-2026-repo
```

### 2. Rodar a Aplicação Web do Mapa
O frontend é 100% estático e compatível com qualquer servidor web HTTP simples:

```bash
# Opção A: Usando Python
python -m http.server 8080 -d frontend

# Opção B: Usando Node (npx)
npx serve frontend
```
Abra [http://localhost:8080](http://localhost:8080) no navegador.

### 3. Rodar os Scripts de Análise (Pipelines)
Recomenda-se criar um ambiente virtual Python:

```bash
python -m venv .venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate
pip install pandas numpy requests plotly reportlab
```

Para extrair os dados e gerar o relatório editorial em PDF:
```bash
python pipeline/espacial_ceara/compilar_pdf_direto.py
```

---

## ⚖️ Licença e Uso dos Dados

* **Código:** Licença MIT — livre para uso, estudo e reprodução com a devida citação.
* **Dados Oficiais:** Dados brutos originados do Tribunal Superior Eleitoral (TSE).
* **Desenvolvido por:** **Ayuri Reis** — *Central de Dados / O POVO*
