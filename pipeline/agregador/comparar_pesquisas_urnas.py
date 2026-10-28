import pandas as pd
import unicodedata
import os

def normalize_name(s):
    if not isinstance(s, str):
        return ""
    # Remove accents, lowercase, strip
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    s = s.lower().strip()
    # Normalize common abbreviations or suffixes
    s = s.replace('.', '').replace('-', ' ')
    s = ' '.join(s.split())
    return s

# 1. Carregar resultados das urnas
df_urnas = pd.read_csv(r'C:\Users\RED.AyuriReis\.gemini\antigravity-ide\scratch\nexo_map\resultado_governadores_1turno_com_brancos_nulos.csv', sep=';')

# 2. Carregar agregador de pesquisas
df_pesq = pd.read_csv(r'c:\Users\RED.AyuriReis\Downloads\Apurador_real\Agregador de pesquisas x urnas - Agregador de Pesquisas.csv', encoding='latin1')

print(f"Linhas em df_urnas: {len(df_urnas)}")
print(f"Linhas em df_pesq: {len(df_pesq)}")

# Limpar 'Valor (%)'
df_pesq['Valor_num'] = df_pesq['Valor (%)'].astype(str).str.replace(',', '.').str.strip()
df_pesq['Valor_num'] = pd.to_numeric(df_pesq['Valor_num'], errors='coerce')

df_pesq['Data_dt'] = pd.to_datetime(df_pesq['Data'], format='%d/%m/%Y', errors='coerce')

# Verificar estados em comum
estados_urnas = set(df_urnas['Estado'].unique())
estados_pesq = set(df_pesq['Estado'].unique())

print("\nEstados nas pesquisas:", sorted(estados_pesq))
print("Estados nas urnas mas não nas pesquisas:", sorted(estados_urnas - estados_pesq))

# Filtrar apenas a ÚLTIMA data de 'Media Ponderada' para cada estado
df_mp = df_pesq[df_pesq['Instituto'] == 'Media Ponderada'].copy()
last_mp_dates = df_mp.groupby('Estado')['Data_dt'].max().reset_index()

df_last_mp = pd.merge(df_mp, last_mp_dates, on=['Estado', 'Data_dt'])
print(f"\nTotal de registros na última Média Ponderada: {len(df_last_mp)}")

# Testar match de candidatos
df_urnas['norm_cand'] = df_urnas['Nome'].apply(normalize_name)
df_last_mp['norm_cand'] = df_last_mp['Candidato'].apply(normalize_name)

# Normalizar 'branco/nulo/nenhum'
df_last_mp.loc[df_last_mp['norm_cand'].str.contains('branco|nulo'), 'norm_cand'] = 'branco/nulo/nenhum'
df_urnas.loc[df_urnas['norm_cand'].str.contains('branco/nulo'), 'norm_cand'] = 'branco/nulo/nenhum'

sample_estado = 'Ceará'
ce_mp = df_last_mp[df_last_mp['Estado'] == sample_estado][['Candidato', 'norm_cand', 'Valor_num']]
ce_urn = df_urnas[df_urnas['Estado'] == sample_estado][['Nome', 'norm_cand', 'Pct_Total', 'Pct_Validos']]

print(f"\n--- Comparação no {sample_estado} ---")
print("Média Ponderada:")
print(ce_mp)
print("\nUrnas:")
print(ce_urn)
