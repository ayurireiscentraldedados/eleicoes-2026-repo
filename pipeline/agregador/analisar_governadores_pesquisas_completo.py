import os
import json
import sys
import unicodedata
import pandas as pd
import numpy as np

# Forçar stdout UTF-8
sys.stdout.reconfigure(encoding='utf-8')

def normalize_text(s):
    if not isinstance(s, str):
        return ""
    s = s.replace('\xad', '').replace('\x8d', '')
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    s = s.lower().strip()
    s = s.replace('.', '').replace('-', ' ')
    return ' '.join(s.split())

uf_to_estado = {
    'ac': 'Acre', 'al': 'Alagoas', 'am': 'Amazonas', 'ap': 'Amapá', 'ba': 'Bahia',
    'ce': 'Ceará', 'df': 'Distrito Federal', 'es': 'Espírito Santo', 'go': 'Goiás',
    'ma': 'Maranhão', 'mg': 'Minas Gerais', 'ms': 'Mato Grosso do Sul', 'mt': 'Mato Grosso',
    'pa': 'Pará', 'pb': 'Paraíba', 'pe': 'Pernambuco', 'pi': 'Piauí', 'pr': 'Paraná',
    'rj': 'Rio de Janeiro', 'rn': 'Rio Grande do Norte', 'ro': 'Rondônia', 'rr': 'Roraima',
    'rs': 'Rio Grande do Sul', 'sc': 'Santa Catarina', 'se': 'Sergipe', 'sp': 'São Paulo',
    'to': 'Tocantins'
}

base_dir = r'c:\Users\RED.AyuriReis\Downloads\Apurador_real\dados_brutos'

urnas_rows = []

for uf in sorted(uf_to_estado.keys()):
    json_path = os.path.join(base_dir, f'governador_{uf}.json')
    if not os.path.exists(json_path):
        continue
    
    with open(json_path, 'r', encoding='utf-8') as f:
        d = json.load(f)
    
    data = d.get('data', {})
    total_votes = int(data.get('number_votes', 0))
    candidates = data.get('candidates', [])
    
    nulo_votes = 0
    branco_votes = 0
    abstencao_votes = 0
    cands_valid = []
    
    for c in candidates:
        name = c.get('name', '').strip()
        votes = int(c.get('valid_votes', 0))
        
        if name == 'Nulo':
            nulo_votes = votes
        elif name == 'Branco':
            branco_votes = votes
        elif 'Absten' in name:
            abstencao_votes = votes
        else:
            cands_valid.append({
                'nome': name,
                'numero': c.get('number'),
                'partido': c.get('party'),
                'situacao': c.get('situation'),
                'votos': votes
            })
    
    total_validos = sum(c['votos'] for c in cands_valid)
    
    for c in cands_valid:
        pct_total = (c['votos'] / total_votes * 100) if total_votes > 0 else 0
        pct_validos = (c['votos'] / total_validos * 100) if total_validos > 0 else 0
        urnas_rows.append({
            'UF': uf.upper(),
            'Estado': uf_to_estado[uf],
            'Tipo': 'Candidato',
            'Candidato': c['nome'],
            'Numero': c['numero'],
            'Partido': c['partido'],
            'Situacao': c['situacao'],
            'Votos': c['votos'],
            'Pct_Total': round(pct_total, 2),
            'Pct_Validos': round(pct_validos, 2),
            'Total_Apurado': total_votes,
            'Total_Validos': total_validos,
            'Brancos_Total': branco_votes,
            'Nulos_Total': nulo_votes,
            'Abstencao_Total': abstencao_votes
        })
    
    pct_branco = (branco_votes / total_votes * 100) if total_votes > 0 else 0
    pct_nulo = (nulo_votes / total_votes * 100) if total_votes > 0 else 0
    pct_bn = ((branco_votes + nulo_votes) / total_votes * 100) if total_votes > 0 else 0
    
    urnas_rows.append({
        'UF': uf.upper(),
        'Estado': uf_to_estado[uf],
        'Tipo': 'Branco',
        'Candidato': 'Branco',
        'Numero': '',
        'Partido': '',
        'Situacao': '',
        'Votos': branco_votes,
        'Pct_Total': round(pct_branco, 2),
        'Pct_Validos': 0.0,
        'Total_Apurado': total_votes,
        'Total_Validos': total_validos,
        'Brancos_Total': branco_votes,
        'Nulos_Total': nulo_votes,
        'Abstencao_Total': abstencao_votes
    })
    
    urnas_rows.append({
        'UF': uf.upper(),
        'Estado': uf_to_estado[uf],
        'Tipo': 'Nulo',
        'Candidato': 'Nulo',
        'Numero': '',
        'Partido': '',
        'Situacao': '',
        'Votos': nulo_votes,
        'Pct_Total': round(pct_nulo, 2),
        'Pct_Validos': 0.0,
        'Total_Apurado': total_votes,
        'Total_Validos': total_validos,
        'Brancos_Total': branco_votes,
        'Nulos_Total': nulo_votes,
        'Abstencao_Total': abstencao_votes
    })
    
    urnas_rows.append({
        'UF': uf.upper(),
        'Estado': uf_to_estado[uf],
        'Tipo': 'Branco/Nulo',
        'Candidato': 'Branco/nulo/nenhum',
        'Numero': '',
        'Partido': '',
        'Situacao': '',
        'Votos': branco_votes + nulo_votes,
        'Pct_Total': round(pct_bn, 2),
        'Pct_Validos': 0.0,
        'Total_Apurado': total_votes,
        'Total_Validos': total_validos,
        'Brancos_Total': branco_votes,
        'Nulos_Total': nulo_votes,
        'Abstencao_Total': abstencao_votes
    })

df_urnas = pd.DataFrame(urnas_rows)
output_urnas_csv = r'C:\Users\RED.AyuriReis\.gemini\antigravity-ide\scratch\nexo_map\resultado_governadores_urnas_1turno.csv'
df_urnas.to_csv(output_urnas_csv, index=False, sep=';', encoding='utf-8-sig')

# Carregar Agregador de Pesquisas
pesq_path = r'c:\Users\RED.AyuriReis\Downloads\Apurador_real\Agregador de pesquisas x urnas - Agregador de Pesquisas.csv'
df_pesq = pd.read_csv(pesq_path, encoding='utf-8')
df_pesq['Valor_num'] = df_pesq['Valor (%)'].astype(str).str.replace(',', '.').str.strip()
df_pesq['Valor_num'] = pd.to_numeric(df_pesq['Valor_num'], errors='coerce')
df_pesq['Data_dt'] = pd.to_datetime(df_pesq['Data'], format='%d/%m/%Y', errors='coerce')

# Aliases completos de matching entre pesquisas e urnas
aliases = {
    ('amapa', 'clecio luis'): 'clecio',
    ('amapa', 'clecio'): 'clecio',
    ('amapa', 'dr furlan'): 'dr furlan',
    ('distrito federal', 'ricardo cappelli'): 'cappelli',
    ('distrito federal', 'elisson ferreira'): 'elisson',
    ('goias', 'danilo pinheiro'): 'danilo da silva',
    ('goias', 'danilo pinheiro evangelista'): 'danilo da silva',
    ('mato grosso', 'natasha slhessarenko'): 'doutora natasha',
    ('mato grosso do sul', 'jefferson bezerra'): 'jeferson bezerra',
    ('minas gerais', 'gabriel azevedo'): 'gabriel',
    ('para', 'dr daniel santos'): 'dr daniel',
    ('para', 'araceli lemos'): 'araceli',
    ('pernambuco', 'renan hallais'): 'renan',
    ('pernambuco', 'gulherme fonseca'): 'guilherme fonseca',
    ('piaui', 'francisco jurity'): 'professor jurity',
    ('piaui', 'ravenna castro'): 'ravenna da inclusao',
    ('rio grande do norte', 'allyson bezerra'): 'allyson',
    ('rio grande do sul', 'luciano zucco'): 'zucco',
    ('rio de janeiro', 'anthony garotinho'): 'garotinho',
    ('rio de janeiro', 'juliete pantoja'): 'juliete',
    ('rio de janeiro', 'juliette'): 'juliete',
    ('rio de janeiro', 'cornoel busnello'): 'coronel busnello',
    ('tocantins', 'professor witer naves'): 'prof witer naves',
    ('ceara', 'delegado hugo'): 'delegado huggo',
    ('ceara', 'ze bastista'): 'ze batista',
    ('maranhao', 'weverton'): 'weverton rocha',
    ('bahia', 'acm neto'): 'acm neto',
    ('bahia', 'antonio carlos magalhaes neto'): 'acm neto'
}

def resolve_key(estado, nome, tipo=''):
    est_norm = normalize_text(estado)
    nome_norm = normalize_text(nome)
    
    if tipo == 'Branco/Nulo' or 'branco/nulo' in nome_norm or 'branco/nulo/nenhum' in nome_norm:
        return 'branco/nulo/nenhum'
    if tipo == 'Branco' or nome_norm == 'branco':
        return 'branco'
    if tipo == 'Nulo' or nome_norm == 'nulo':
        return 'nulo'
    if 'indeciso' in nome_norm or 'nao sabe' in nome_norm:
        return 'indeciso/nao sabe'
    
    if (est_norm, nome_norm) in aliases:
        return aliases[(est_norm, nome_norm)]
    
    return nome_norm

df_urnas['match_key'] = df_urnas.apply(lambda r: resolve_key(r['Estado'], r['Candidato'], r['Tipo']), axis=1)

# Pegar a última Média Ponderada
df_mp = df_pesq[df_pesq['Instituto'] == 'Media Ponderada'].copy()
last_mp_dates = df_mp.groupby('Estado')['Data_dt'].max().reset_index().rename(columns={'Data_dt': 'Ultima_Data_MP'})
df_last_mp = pd.merge(df_mp, last_mp_dates, left_on=['Estado', 'Data_dt'], right_on=['Estado', 'Ultima_Data_MP'])
df_last_mp['match_key'] = df_last_mp.apply(lambda r: resolve_key(r['Estado'], r['Candidato']), axis=1)

# Merge
comp_list = []
for estado in sorted(df_last_mp['Estado'].unique()):
    sub_mp = df_last_mp[df_last_mp['Estado'] == estado]
    sub_urn = df_urnas[df_urnas['Estado'] == estado]
    
    data_mp = sub_mp['Data'].iloc[0] if len(sub_mp) > 0 else ''
    
    indecisos_row = sub_mp[sub_mp['match_key'] == 'indeciso/nao sabe']
    indecisos_val = indecisos_row['Valor_num'].iloc[0] if len(indecisos_row) > 0 else 0.0
    
    for _, r_mp in sub_mp.iterrows():
        key = r_mp['match_key']
        if key == 'indeciso/nao sabe':
            continue
        
        # Filtro preciso: se a opção for branco/nulo, busca especificamente Tipo == 'Branco/Nulo'
        if key == 'branco/nulo/nenhum':
            cand_urn = sub_urn[sub_urn['Tipo'] == 'Branco/Nulo']
        else:
            cand_urn = sub_urn[sub_urn['match_key'] == key]
            if len(cand_urn) == 0:
                parts = key.split()
                if len(parts) >= 2:
                    cand_urn = sub_urn[sub_urn['match_key'].str.contains(parts[0]) & sub_urn['match_key'].str.contains(parts[-1])]
        
        if len(cand_urn) > 0:
            u_row = cand_urn.iloc[0]
            pct_urna_total = u_row['Pct_Total']
            pct_urna_validos = u_row['Pct_Validos']
            votos_urna = u_row['Votos']
            nome_urna = u_row['Candidato']
            partido_urna = u_row['Partido'] if pd.notnull(u_row['Partido']) and u_row['Partido'] != '' else r_mp['Partido']
            situacao_urna = u_row['Situacao']
            matched = True
        else:
            pct_urna_total = np.nan
            pct_urna_validos = np.nan
            votos_urna = np.nan
            nome_urna = r_mp['Candidato']
            partido_urna = r_mp['Partido']
            situacao_urna = 'Não Concorreu'
            matched = False
        
        val_mp = r_mp['Valor_num']
        
        dif_total = round(pct_urna_total - val_mp, 2) if pd.notnull(pct_urna_total) and pd.notnull(val_mp) else np.nan
        dif_validos = round(pct_urna_validos - val_mp, 2) if pd.notnull(pct_urna_validos) and pd.notnull(val_mp) else np.nan
        
        comp_list.append({
            'Estado': estado,
            'Data_Pesquisa': data_mp,
            'Candidato_Pesquisa': r_mp['Candidato'],
            'Candidato_Urna': nome_urna,
            'Partido': partido_urna,
            'Situacao_Urna': situacao_urna,
            'Media_Ponderada (%)': val_mp,
            'Urna_Pct_Total (%)': pct_urna_total,
            'Urna_Pct_Validos (%)': pct_urna_validos,
            'Erro_vs_Total (Urna - MP)': dif_total,
            'Erro_vs_Validos (Urna - MP)': dif_validos,
            'Votos_Urna': votos_urna,
            'Indecisos_Pesquisa (%)': indecisos_val,
            'Matched': matched
        })

df_comp = pd.DataFrame(comp_list)
output_comp_csv = r'C:\Users\RED.AyuriReis\.gemini\antigravity-ide\scratch\nexo_map\comparativo_agregador_pesquisas_x_urnas.csv'
df_comp.to_csv(output_comp_csv, index=False, sep=';', encoding='utf-8-sig')

# 4. Avaliação de Acurácia da Média Ponderada por Estado
df_comp_valid = df_comp[df_comp['Matched'] == True].copy()
df_comp_valid['Erro_Abs_Total'] = df_comp_valid['Erro_vs_Total (Urna - MP)'].abs()
df_comp_valid['Erro_Abs_Validos'] = df_comp_valid['Erro_vs_Validos (Urna - MP)'].abs()

acuracia_estados = df_comp_valid.groupby('Estado').agg(
    Qtd_Candidatos=('Candidato_Pesquisa', 'count'),
    MAE_Total=('Erro_Abs_Total', 'mean'),
    Max_Erro_Total=('Erro_Abs_Total', 'max'),
    MAE_Validos=('Erro_Abs_Validos', 'mean'),
    Indecisos_Vespera=('Indecisos_Pesquisa (%)', 'first')
).reset_index().round(2)

acuracia_estados = acuracia_estados.sort_values('MAE_Total')

output_acuracia_csv = r'C:\Users\RED.AyuriReis\.gemini\antigravity-ide\scratch\nexo_map\acuracia_agregador_por_estado.csv'
acuracia_estados.to_csv(output_acuracia_csv, index=False, sep=';', encoding='utf-8-sig')

print(f"Relatório de Acurácia por Estado salvo em: {output_acuracia_csv}")
print("\nTop 5 Estados mais precisos (Menor Erro Médio Absoluto vs Total):")
print(acuracia_estados.head(5).to_string(index=False))

print("\nTop 5 Estados com maior dispersão:")
print(acuracia_estados.tail(5).to_string(index=False))

print(f"\nMAE Geral em todos os 23 estados: {df_comp_valid['Erro_Abs_Total'].mean():.2f} p.p.")
