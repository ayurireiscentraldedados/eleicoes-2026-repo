import urllib.request
import json
import gzip
import pandas as pd

print("1. Baixando malha dos 184 municípios do Ceará via IBGE API...")
url = 'https://servicodados.ibge.gov.br/api/v3/malhas/estados/23?formato=application/vnd.geo+json&qualidade=intermediaria&intrarregiao=municipio'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as resp:
    raw = resp.read()
    try:
        raw = gzip.decompress(raw)
    except:
        pass
    geo_data = json.loads(raw.decode('utf-8'))

print(f"Total de municípios baixados: {len(geo_data['features'])}")

# Obter nomes dos municípios
print("2. Mapeando códigos IBGE para nomes dos municípios...")
df_ibge = pd.read_csv(r'C:\Users\RED.AyuriReis\Downloads\Apurador_real\presidente_br_resultado_direto.csv', sep=';', encoding='utf-8')
ce_df = df_ibge[df_ibge['UF_sigla'] == 'CE'][['cod_ibge7', 'Município']].drop_duplicates()
name_map = dict(zip(ce_df['cod_ibge7'].astype(str), ce_df['Município']))

for feat in geo_data['features']:
    cod = str(feat['properties'].get('codarea', ''))
    feat['properties']['nome'] = name_map.get(cod, '')
    feat['properties']['NM_MUNICIPIO'] = name_map.get(cod, '')

with open('ce_municipios.geojson', 'w', encoding='utf-8') as f:
    json.dump(geo_data, f)

print(f"ce_municipios.geojson atualizado com sucesso! Exemplo: {geo_data['features'][0]['properties']}")
