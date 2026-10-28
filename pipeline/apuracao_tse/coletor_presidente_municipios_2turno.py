import os
import sys
import time
import json
import urllib3
import requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Suporte a UTF-8 no terminal Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

"""
COLETOR & APURADOR DE DADOS PRESIDENCIAIS POR MUNICÍPIO - 2º TURNO (2026)
-------------------------------------------------------------------------
Monitora todos os 5.571 municípios do Brasil diretamente do CDN oficial do TSE:
- Eleição Federal 2º Turno: 6258
- Cargo: Presidente (c0001)
- Concorrência de alta performance (40 conexões simultâneas)
- Gera os dados oficiais consolidados para os mapas municipais do Flourish
"""

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = r"c:\Users\RED.AyuriReis\Downloads\Apurador_real" if os.path.exists(r"c:\Users\RED.AyuriReis\Downloads\Apurador_real") else SCRIPT_DIR

DICIONARIO_PATH = os.path.join(BASE_DIR, "dicionario_municipios_brasil.csv")
PASTA_RECORTES = os.path.join(BASE_DIR, "recortes_gerados_2turno")
os.makedirs(PASTA_RECORTES, exist_ok=True)

ELEICAO_ID = "6258"  # Eleição Federal - 2º Turno Oficial TSE
CARGO_ID = "c0001"   # Cargo Presidente

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*"
}

def carregar_dicionario_municipios():
    """Carrega o dicionário base de 5.571 municípios com cod_tse e cod_ibge7."""
    if os.path.exists(DICIONARIO_PATH):
        return pd.read_csv(DICIONARIO_PATH, encoding="utf-8-sig")
    
    print("[Aviso] Dicionário local não encontrado. Baixando do TSE...")
    url_mun = f"https://resultados.tse.jus.br/oficial/ele2026/{ELEICAO_ID}/config/mun-e00{ELEICAO_ID}-cm.json"
    r = requests.get(url_mun, headers=HEADERS, verify=False, timeout=15)
    data = r.json()
    
    sigla_para_estado = {
        'ac': 'Acre', 'al': 'Alagoas', 'am': 'Amazonas', 'ap': 'Amapá', 'ba': 'Bahia',
        'ce': 'Ceará', 'df': 'Distrito Federal', 'es': 'Espírito Santo',
        'go': 'Goiás', 'ma': 'Maranhão', 'mt': 'Mato Grosso', 'ms': 'Mato Grosso do Sul',
        'mg': 'Minas Gerais', 'pa': 'Pará', 'pb': 'Paraíba', 'pr': 'Paraná',
        'pe': 'Pernambuco', 'pi': 'Piauí', 'rj': 'Rio de Janeiro', 'rn': 'Rio Grande do Norte',
        'rs': 'Rio Grande do Sul', 'ro': 'Rondônia', 'rr': 'Roraima', 'sc': 'Santa Catarina',
        'sp': 'São Paulo', 'se': 'Sergipe', 'to': 'Tocantins'
    }
    
    municipios = []
    for u in data.get('abr', []):
        sigla = u.get('cd', '').lower()
        if sigla in ['zz', 'br']:
            continue
        nome_estado = sigla_para_estado.get(sigla, sigla.upper())
        for m in u.get('mu', []):
            municipios.append({
                'cod_mun': str(m.get('cd')).zfill(5),
                'cod_ibge7': str(m.get('cdi')),
                'Estado': nome_estado,
                'Município': m.get('nm', '').title(),
                'UF_sigla': sigla.upper()
            })
            
    df = pd.DataFrame(municipios)
    df.sort_values(by=['Estado', 'Município'], inplace=True)
    df.to_csv(DICIONARIO_PATH, index=False, encoding="utf-8-sig")
    return df

def coletar_municipios_brasil(max_workers=40):
    """
    Executa a coleta concorrente de todos os 5.571 municípios do Brasil para Presidente no 2º Turno.
    Retorna os DataFrames formatados para os mapas do Flourish.
    """
    df_dicionario = carregar_dicionario_municipios()
    total_mun = len(df_dicionario)
    
    print("=" * 68)
    print(f"APURAÇÃO PRESIDENCIAL POR MUNICÍPIO - 2º TURNO (TSE {ELEICAO_ID})")
    print(f"Total de Municípios no Brasil: {total_mun}")
    print(f"Conexões simultâneas: {max_workers}")
    print("=" * 68)
    
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(pool_connections=max_workers, pool_maxsize=max_workers, max_retries=2)
    session.mount("https://", adapter)
    session.headers.update(HEADERS)
    
    t0 = time.time()
    resultados = []
    
    def fetch_item(row):
        sigla = str(row['UF_sigla']).lower()
        cd_tse = str(row['cod_mun']).zfill(5)
        url = f"https://resultados.tse.jus.br/oficial/ele2026/{ELEICAO_ID}/dados/{sigla}/{sigla}{cd_tse}-{CARGO_ID}-e00{ELEICAO_ID}-u.json"
        
        try:
            r = session.get(url, verify=False, timeout=8)
            if r.status_code == 200:
                d = r.json()
                lula = 0
                flavio = 0
                total = 0
                
                for c in d.get('carg', []):
                    for agr in c.get('agr', []):
                        for par in agr.get('par', []):
                            for cand in par.get('cand', []):
                                n = cand.get('nmu') or cand.get('nm') or ''
                                v = int(cand.get('vap', 0))
                                total += v
                                if 'LULA' in n.upper():
                                    lula += v
                                elif 'FLAVIO' in n.upper() or 'FLÁVIO' in n.upper():
                                    flavio += v
                                    
                return {
                    'cod_ibge7': row['cod_ibge7'],
                    'Estado': row['Estado'],
                    'Município': row['Município'],
                    'UF_sigla': row['UF_sigla'],
                    'Lula': lula,
                    'Flávio Bolsonaro': flavio,
                    'Total': total
                }
        except Exception:
            pass
            
        return {
            'cod_ibge7': row['cod_ibge7'],
            'Estado': row['Estado'],
            'Município': row['Município'],
            'UF_sigla': row['UF_sigla'],
            'Lula': 0,
            'Flávio Bolsonaro': 0,
            'Total': 0
        }

    print(f"Iniciando varredura em tempo real dos {total_mun} municípios...")
    linhas = [row for _, row in df_dicionario.iterrows()]
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for i, res in enumerate(executor.map(fetch_item, linhas), 1):
            resultados.append(res)
            if i % 1000 == 0 or i == total_mun:
                taxa = i / (time.time() - t0)
                print(f"  -> {i}/{total_mun} municípios apurados ({taxa:.1f} mun/s)...")
                
    tempo_total = time.time() - t0
    print(f"\n✔ Apuração dos {total_mun} municípios concluída em {tempo_total:.1f} segundos!")
    
    # Monta o DataFrame
    df = pd.DataFrame(resultados)
    df['Total'] = df['Total'].astype(int)
    df['Lula'] = df['Lula'].astype(int)
    df['Flávio Bolsonaro'] = df['Flávio Bolsonaro'].astype(int)
    
    # Percentuais
    mask = df['Total'] > 0
    df['Lula_percentual'] = "0,00%"
    df['Bolsonaro_percentual'] = "0,00%"
    
    df.loc[mask, 'Lula_percentual'] = (df['Lula'] / df['Total'] * 100).round(2).apply(lambda v: f"{v:.2f}%".replace(".", ","))
    df.loc[mask, 'Bolsonaro_percentual'] = (df['Flávio Bolsonaro'] / df['Total'] * 100).round(2).apply(lambda v: f"{v:.2f}%".replace(".", ","))
    
    df['Diferença'] = df['Lula'] - df['Flávio Bolsonaro']
    df['Outros_candidatos'] = "0,00%"
    df['Outros_candidatos(total)'] = 0
    
    def definir_vencedor(row):
        if row['Lula'] > row['Flávio Bolsonaro']:
            return 'Lula'
        elif row['Flávio Bolsonaro'] > row['Lula']:
            return 'Flávio Bolsonaro'
        return 'Empate'
        
    df['Vencedor'] = df.apply(definir_vencedor, axis=1)
    
    # -------------------------------------------------------------
    # 1. TABELA MAPA BRASIL - PRESIDENTES (13 COLUNAS OFICIAIS FLOURISH)
    # -------------------------------------------------------------
    cols_mapa_brasil = [
        'cod_ibge7', 'Estado', 'Município', 'UF_sigla', 
        'Lula', 'Flávio Bolsonaro', 'Outros_candidatos(total)', 'Total', 
        'Lula_percentual', 'Bolsonaro_percentual', 'Diferença', 
        'Outros_candidatos', 'Vencedor'
    ]
    df_mapa_brasil = df[cols_mapa_brasil].copy()
    
    # -------------------------------------------------------------
    # 2. TABELA MAPA PRESIDENTE MUNICIPIO (10 COLUNAS)
    # -------------------------------------------------------------
    cols_pres_mun = [
        'cod_ibge7', 'Estado', 'Município', 'UF_sigla', 
        'Lula', 'Flávio Bolsonaro', 'Total', 
        'Lula_percentual', 'Bolsonaro_percentual', 'Diferença'
    ]
    df_pres_mun = df[cols_pres_mun].copy()
    
    # Salva CSVs locais para backup imediato
    path_csv_1 = os.path.join(PASTA_RECORTES, "mapa_brasil_presidentes_2turno.csv")
    path_csv_2 = os.path.join(PASTA_RECORTES, "presidente_br_resultado_direto.csv")
    path_csv_root = os.path.join(BASE_DIR, "presidente_br_resultado_direto.csv")
    
    df_mapa_brasil.to_csv(path_csv_1, index=False, sep=";", encoding="utf-8-sig")
    df_pres_mun.to_csv(path_csv_2, index=False, sep=";", encoding="utf-8-sig")
    df_pres_mun.to_csv(path_csv_root, index=False, sep=";", encoding="utf-8-sig")
    print(f"Backups locais salvos em: {path_csv_2}")
    
    return {
        "mapa_brasil_presidentes": df_mapa_brasil,
        "mapa_presidente_municipio": df_pres_mun
    }

if __name__ == "__main__":
    tabelas = coletar_municipios_brasil(max_workers=40)
