import json
import pandas as pd
import unicodedata
import os
import sys

import re
def remove_accents(input_str):
    if not isinstance(input_str, str):
        return ""
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    s = u"".join([c for c in nfkd_form if not unicodedata.combining(c)]).upper()
    s = re.sub(r'[^A-Z0-9 ]', ' ', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()

print("Carregando arquivo de geometria base (fallback)...")
with open(r'C:\Users\RED.AyuriReis\.gemini\antigravity-ide\scratch\nexo_map\points.geojson', 'r', encoding='utf-8') as f:
    geo = json.load(f)

print("Carregando enderecos e coordenadas do eleitorado...")
df_eleitorado = pd.read_csv(r'C:\Users\RED.AyuriReis\Downloads\Apurador_real\dados_tse\eleitorado_local_votacao_2026_CE.csv', sep=';', encoding='latin1', usecols=['NR_ZONA', 'NM_LOCAL_VOTACAO', 'NM_MUNICIPIO', 'DS_ENDERECO', 'NM_BAIRRO', 'NR_LATITUDE', 'NR_LONGITUDE'])

df_eleitorado['NR_LATITUDE'] = pd.to_numeric(df_eleitorado['NR_LATITUDE'].astype(str).str.replace(',', '.'), errors='coerce')
df_eleitorado['NR_LONGITUDE'] = pd.to_numeric(df_eleitorado['NR_LONGITUDE'].astype(str).str.replace(',', '.'), errors='coerce')
df_eleitorado['Local_Norm'] = df_eleitorado['NM_LOCAL_VOTACAO'].apply(remove_accents)
df_eleitorado = df_eleitorado.drop_duplicates(subset=['NR_ZONA', 'Local_Norm'])

escolas_geo = {}
# 1. Primeiro tenta usar os pontos do geojson como fallback
for feat in geo['features']:
    props = feat['properties']
    zona = int(props['Zona'])
    local_norm = remove_accents(props.get('Local_Norm', ''))
    
    escolas_geo[(zona, local_norm)] = {
        'geometry': feat['geometry'],
        'Municipio': props.get('Município', ''),
        'Local': props.get('Local', ''),
        'Endereco': '',
        'Bairro': ''
    }

# 2. Atualiza com os dados oficiais do TSE, que tem lat/long e endereco
for _, row in df_eleitorado.iterrows():
    zona = int(row['NR_ZONA'])
    local_norm = row['Local_Norm']
    
    lat = row['NR_LATITUDE']
    lon = row['NR_LONGITUDE']
    
    has_coord = pd.notna(lat) and pd.notna(lon) and lat != -1 and lon != -1
    
    if (zona, local_norm) not in escolas_geo:
        escolas_geo[(zona, local_norm)] = {}
        
    escola = escolas_geo[(zona, local_norm)]
    escola['Municipio'] = str(row['NM_MUNICIPIO'])
    escola['Local'] = str(row['NM_LOCAL_VOTACAO'])
    escola['Endereco'] = str(row['DS_ENDERECO']) if pd.notna(row['DS_ENDERECO']) else ''
    escola['Bairro'] = str(row['NM_BAIRRO']) if pd.notna(row['NM_BAIRRO']) else ''
    
    if has_coord:
        escola['geometry'] = {
            'type': 'Point',
            'coordinates': [float(lon), float(lat)]
        }

print("Carregando Nomes de Urna (consulta_cand)...")
df_cand_ce = pd.read_csv(r'C:\Users\RED.AyuriReis\Downloads\Apurador_real\temp_zip\consulta_cand_2026_CE.csv', sep=';', encoding='latin1', usecols=['SQ_CANDIDATO', 'NM_URNA_CANDIDATO'])
try:
    df_cand_br = pd.read_csv(r'C:\Users\RED.AyuriReis\Downloads\Apurador_real\temp_zip\consulta_cand_2026_BR.csv', sep=';', encoding='latin1', usecols=['SQ_CANDIDATO', 'NM_URNA_CANDIDATO'])
    df_cand = pd.concat([df_cand_ce, df_cand_br])
except FileNotFoundError:
    df_cand = df_cand_ce

nome_urna_map = dict(zip(df_cand['SQ_CANDIDATO'], df_cand['NM_URNA_CANDIDATO']))

print("Carregando CSV do TSE (isso pode demorar uns segundos)...")
# Usa colunas estritas para economizar RAM
usecols = ['NR_ZONA', 'NM_LOCAL_VOTACAO', 'CD_CARGO', 'DS_CARGO', 'NR_VOTAVEL', 'NM_VOTAVEL', 'QT_VOTOS', 'SQ_CANDIDATO']
df = pd.read_csv(r'C:\Users\RED.AyuriReis\Downloads\Apurador_real\temp_zip\votacao_secao_2026_CE.csv', sep=';', encoding='latin1', usecols=usecols)

# Remover votos brancos (95) e nulos (96) para o clculo de vlidos nominais e legenda
df = df[~df['NR_VOTAVEL'].isin([95, 96])]

# Normalizar local de votao
df['Local_Norm'] = df['NM_LOCAL_VOTACAO'].apply(remove_accents)

# Processar cada Cargo
cargos = df['DS_CARGO'].unique()

def export_geojson(features, filename):
    out = {"type": "FeatureCollection", "features": features}
    out_path = os.path.join(r'C:\Users\RED.AyuriReis\.gemini\antigravity-ide\scratch\nexo_map', filename)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False)
    print(f"-> Salvo: {filename} ({len(features)} locais)")

for cargo in cargos:
    print(f"Processando: {cargo}...")
    df_cargo = df[df['DS_CARGO'] == cargo]
    
    # Agrupar votos por ZONA + LOCAL + CANDIDATO + SQ_CANDIDATO
    agrupado = df_cargo.groupby(['NR_ZONA', 'Local_Norm', 'NR_VOTAVEL', 'NM_VOTAVEL', 'SQ_CANDIDATO'])['QT_VOTOS'].sum().reset_index()
    
    features = []
    
    # Para cada escola
    escolas_grouped = agrupado.groupby(['NR_ZONA', 'Local_Norm'])
    for (zona, local_norm), group in escolas_grouped:
        if (zona, local_norm) not in escolas_geo:
            continue # Pula se no temos a geometria no mapa base
            
        geo_info = escolas_geo[(zona, local_norm)]
        
        # Calcular total de votos vlidos
        total_validos = int(group['QT_VOTOS'].sum())
        if total_validos == 0:
            continue
            
        props = {
            'Zona': int(zona),
            'Local_Norm': local_norm,
            'Municipio': geo_info['Municipio'],
            'Local': geo_info['Local'],
            'Endereco': geo_info.get('Endereco', ''),
            'Bairro': geo_info.get('Bairro', ''),
            'Cargo': cargo,
            'Total_Validos': total_validos
        }

        # Se for Majoritrio (Governador, Senador, Presidente)
        if cargo in ['Governador', 'Senador', 'Presidente']:
            cands = group.sort_values(by='QT_VOTOS', ascending=False).head(5)
            props['Candidatos'] = []
            for _, row in cands.iterrows():
                sq_cand = row.get('SQ_CANDIDATO', '')
                if pd.isna(sq_cand) or sq_cand == -1:
                    sq_cand = ""
                    sq_cand_int = None
                else:
                    sq_cand_int = int(sq_cand)
                    sq_cand = str(sq_cand_int)
                
                nome_cand = nome_urna_map.get(sq_cand_int, row['NM_VOTAVEL'])
                
                props['Candidatos'].append({
                    'Nome': nome_cand,
                    'Numero': int(row['NR_VOTAVEL']),
                    'Votos': int(row['QT_VOTOS']),
                    'Pct': round((row['QT_VOTOS'] / total_validos) * 100, 2),
                    'SQ': sq_cand
                })
            vencedor = props['Candidatos'][0]
            props['Vencedor_Nome'] = vencedor['Nome']
            props['Vencedor_Votos'] = vencedor['Votos']
            props['Vencedor_Pct'] = vencedor['Pct']
            
            if len(props['Candidatos']) > 1:
                props['Diferenca'] = props['Candidatos'][0]['Votos'] - props['Candidatos'][1]['Votos']
            else:
                props['Diferenca'] = props['Candidatos'][0]['Votos']
                
        # Se for Proporcional (Deputados)
        else:
            # Extrair partido (2 primeiros dgitos)
            group['Partido'] = group['NR_VOTAVEL'].astype(str).str.zfill(4).str[:2]
            
            # Votos por partido
            partidos = group.groupby('Partido')['QT_VOTOS'].sum().reset_index().sort_values(by='QT_VOTOS', ascending=False)
            props['Partidos'] = []
            for _, row in partidos.head(5).iterrows():
                props['Partidos'].append({
                    'Partido': row['Partido'],
                    'Votos': int(row['QT_VOTOS']),
                    'Pct': round((row['QT_VOTOS'] / total_validos) * 100, 2)
                })
                
            # Votos por candidato
            # Ignorar votos de legenda para a lista de candidatos (voto de legenda tem NR_VOTAVEL igual ao nmero do partido, ex: 13, 22)
            cands_nominais = group[group['NR_VOTAVEL'].astype(str).str.len() > 2]
            cands = cands_nominais.sort_values(by='QT_VOTOS', ascending=False).head(5)
            props['Candidatos'] = []
            for _, row in cands.iterrows():
                sq_cand = row.get('SQ_CANDIDATO', '')
                if pd.isna(sq_cand) or sq_cand == -1:
                    sq_cand = ""
                    sq_cand_int = None
                else:
                    sq_cand_int = int(sq_cand)
                    sq_cand = str(sq_cand_int)
                
                nome_cand = nome_urna_map.get(sq_cand_int, row['NM_VOTAVEL'])
                
                props['Candidatos'].append({
                    'Nome': nome_cand,
                    'Numero': int(row['NR_VOTAVEL']),
                    'Partido': row['Partido'],
                    'Votos': int(row['QT_VOTOS']),
                    'SQ': sq_cand
                })
            
            if len(props['Partidos']) > 0:
                props['Vencedor_Partido'] = props['Partidos'][0]['Partido']
                
        features.append({
            "type": "Feature",
            "properties": props,
            "geometry": geo_info['geometry']
        })
        
    export_geojson(features, f"mapa_{cargo.lower().replace(' ', '_')}.geojson")

print("FIM!")
