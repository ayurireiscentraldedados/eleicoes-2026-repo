import os
import json
import sys
import unicodedata
import pandas as pd
import numpy as np

# Configurar stdout para UTF-8
sys.stdout.reconfigure(encoding='utf-8')

def normalize_text(s):
    if not isinstance(s, str):
        return ""
    s = s.replace('\xad', '').replace('\x8d', '')
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    s = s.lower().strip()
    s = s.replace('.', '').replace('-', ' ')
    return ' '.join(s.split())

# 1. Mapeamento de UF para Estados
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

urnas_list = []

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
        urnas_list.append({
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
    
    # Adicionar Branco, Nulo e Branco/Nulo
    pct_branco = (branco_votes / total_votes * 100) if total_votes > 0 else 0
    pct_nulo = (nulo_votes / total_votes * 100) if total_votes > 0 else 0
    pct_bn = ((branco_votes + nulo_votes) / total_votes * 100) if total_votes > 0 else 0
    
    urnas_list.append({
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
    
    urnas_list.append({
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
    
    urnas_list.append({
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

df_urnas = pd.DataFrame(urnas_list)

# Salvar resultado das urnas
output_urnas_csv = r'C:\Users\RED.AyuriReis\.gemini\antigravity-ide\scratch\nexo_map\resultado_governadores_urnas_1turno.csv'
df_urnas.to_csv(output_urnas_csv, index=False, sep=';', encoding='utf-8-sig')
print(f"1. Resultados das Urnas salvos com sucesso em: {output_urnas_csv}")

# 2. Carregar e processar Agregador de Pesquisas
pesq_path = r'c:\Users\RED.AyuriReis\Downloads\Apurador_real\Agregador de pesquisas x urnas - Agregador de Pesquisas.csv'
df_pesq = pd.read_csv(pesq_path, encoding='utf-8')

df_pesq['Valor_num'] = df_pesq['Valor (%)'].astype(str).str.replace(',', '.').str.strip()
df_pesq['Valor_num'] = pd.to_numeric(df_pesq['Valor_num'], errors='coerce')
df_pesq['Data_dt'] = pd.to_datetime(df_pesq['Data'], format='%d/%m/%Y', errors='coerce')

# Obter a última data de Média Ponderada para cada estado
df_mp = df_pesq[df_pesq['Instituto'] == 'Media Ponderada'].copy()
last_mp_dates = df_mp.groupby('Estado')['Data_dt'].max().reset_index().rename(columns={'Data_dt': 'Ultima_Data_MP'})

df_last_mp = pd.merge(df_mp, last_mp_dates, left_on=['Estado', 'Data_dt'], right_on=['Estado', 'Ultima_Data_MP'])

# Obter também a última pesquisa individual realizada em cada estado
df_inst = df_pesq[df_pesq['Instituto'] != 'Media Ponderada'].copy()
last_inst_dates = df_inst.groupby('Estado')['Data_dt'].max().reset_index().rename(columns={'Data_dt': 'Ultima_Data_Pesq'})
df_last_inst = pd.merge(df_inst, last_inst_dates, left_on=['Estado', 'Data_dt'], right_on=['Estado', 'Ultima_Data_Pesq'])

print(f"2. Agregador carregado. Estados com Média Ponderada: {len(last_mp_dates)}")

# 3. Matching Inteligente de Candidatos
df_urnas['norm_estado'] = df_urnas['Estado'].apply(normalize_text)
df_last_mp['norm_estado'] = df_last_mp['Estado'].apply(normalize_text)

df_urnas['norm_cand'] = df_urnas['Candidato'].apply(normalize_text)
df_last_mp['norm_cand'] = df_last_mp['Candidato'].apply(normalize_text)

# Normalizar brancos/nulos
df_urnas.loc[df_urnas['norm_cand'].str.contains('branco/nulo'), 'norm_cand'] = 'branco/nulo/nenhum'
df_last_mp.loc[df_last_mp['norm_cand'].str.contains('branco|nulo'), 'norm_cand'] = 'branco/nulo/nenhum'

# Dicionário de sinônimos/aliases comuns entre urna e pesquisa por estado
aliases = {
    ('ceara', 'ciro gomes'): 'ciro gomes',
    ('ceara', 'elmano de freitas'): 'elmano de freitas',
    ('ceara', 'delegado huggo'): 'delegado huggo',
    ('ceara', 'delegado hugo'): 'delegado huggo',
    ('ceara', 'ze batista'): 'ze batista',
    ('ceara', 'ze bastista'): 'ze batista',
    ('bahia', 'acm neto'): 'acm neto',
    ('bahia', 'antonio carlos magalhaes neto'): 'acm neto',
    ('bahia', 'jeronimo rodrigues'): 'jeronimo rodrigues',
    ('bahia', 'jeronimo'): 'jeronimo rodrigues',
    ('minas gerais', 'romeu zema'): 'romeu zema',
    ('minas gerais', 'alexandre kalil'): 'alexandre kalil',
    ('rio de janeiro', 'claudio castro'): 'claudio castro',
    ('rio de janeiro', 'marcelo freixo'): 'marcelo freixo',
    ('rio grande do sul', 'eduardo leite'): 'eduardo leite',
    ('rio grande do sul', 'onyx lorenzoni'): 'onyx lorenzoni',
    ('parana', 'ratinho junior'): 'ratinho junior',
    ('parana', 'carlos massa ratinho junior'): 'ratinho junior',
    ('parana', 'roberto requiao'): 'roberto requiao',
    ('pernambuco', 'marilia arraes'): 'marilia arraes',
    ('pernambuco', 'raquel lyra'): 'raquel lyra',
    ('maranhao', 'carlos brandao'): 'carlos brandao',
    ('maranhao', 'weverton rocha'): 'weverton rocha',
    ('maranhao', 'weverton'): 'weverton rocha',
    ('para', 'helder barbalho'): 'helder barbalho',
    ('para', 'helder'): 'helder barbalho',
    ('goias', 'ronaldo caiado'): 'ronaldo caiado',
    ('goias', 'gustavo mendanha'): 'gustavo mendanha',
    ('distrito federal', 'ibaneis rocha'): 'ibaneis rocha',
    ('distrito federal', 'ibaneis'): 'ibaneis rocha',
    ('distrito federal', 'leila do volei'): 'leila do volei',
    ('distrito federal', 'leila barros'): 'leila do volei',
    ('alagoas', 'paulo dantas'): 'paulo dantas',
    ('alagoas', 'rodrigo cunha'): 'rodrigo cunha',
    ('alagoas', 'fernando collor'): 'fernando collor',
    ('acre', 'gladson cameli'): 'gladson cameli',
    ('acre', 'jorge viana'): 'jorge viana',
    ('amazonas', 'wilson lima'): 'wilson lima',
    ('amazonas', 'eduardo braga'): 'eduardo braga',
    ('amazonas', 'amazonino mendes'): 'amazonino mendes',
    ('espirito santo', 'renato casagrande'): 'renato casagrande',
    ('espirito santo', 'manato'): 'manato',
    ('espirito santo', 'carlos manato'): 'manato',
    ('mato grosso', 'mauro mendes'): 'mauro mendes',
    ('mato grosso do sul', 'eduardo riedel'): 'eduardo riedel',
    ('mato grosso do sul', 'capitao contar'): 'capitao contar',
    ('paraiba', 'joao azevêdo'): 'joao azevedo',
    ('paraiba', 'joao azevedo'): 'joao azevedo',
    ('paraiba', 'pedro cunha lima'): 'pedro cunha lima',
    ('piaui', 'rafael fonteles'): 'rafael fonteles',
    ('piaui', 'silvio mendes'): 'silvio mendes',
    ('rio grande do norte', 'fatima bezerra'): 'fatima bezerra',
    ('rio grande do norte', 'capitao styvenson'): 'styvenson valentim',
    ('rio grande do norte', 'styvenson valentim'): 'styvenson valentim',
    ('rondonia', 'marcos rocha'): 'marcos rocha',
    ('rondonia', 'coronel marcos rocha'): 'marcos rocha',
    ('rondonia', 'marcos rogerio'): 'marcos rogerio',
    ('tocantins', 'wanderlei barbosa'): 'wanderlei barbosa',
    ('tocantins', 'ronaldo dimas'): 'ronaldo dimas'
}

def get_match_key(estado, nome):
    est_norm = normalize_text(estado)
    nome_norm = normalize_text(nome)
    
    if (est_norm, nome_norm) in aliases:
        return aliases[(est_norm, nome_norm)]
    
    if 'branco' in nome_norm or 'nulo' in nome_norm:
        return 'branco/nulo/nenhum'
    if 'indeciso' in nome_norm or 'nao sabe' in nome_norm:
        return 'indeciso/nao sabe'
    
    return nome_norm

df_urnas['match_key'] = df_urnas.apply(lambda r: get_match_key(r['Estado'], r['Candidato']), axis=1)
df_last_mp['match_key'] = df_last_mp.apply(lambda r: get_match_key(r['Estado'], r['Candidato']), axis=1)

# Realizar o merge entre Urnas e Média Ponderada
merged = []

for estado in sorted(df_last_mp['Estado'].unique()):
    sub_mp = df_last_mp[df_last_mp['Estado'] == estado]
    sub_urn = df_urnas[df_urnas['Estado'] == estado]
    
    data_mp = sub_mp['Data'].iloc[0] if len(sub_mp) > 0 else ''
    
    # Indecisos na última pesquisa
    indecisos_row = sub_mp[sub_mp['match_key'] == 'indeciso/nao sabe']
    indecisos_pct = indecisos_row['Valor_num'].iloc[0] if len(indecisos_row) > 0 else 0.0
    
    for _, r_mp in sub_mp.iterrows():
        key = r_mp['match_key']
        if key == 'indeciso/nao sabe':
            continue
        
        # Buscar na urna
        cand_urn = sub_urn[sub_urn['match_key'] == key]
        
        # Se não achou exato, busca se o primeiro e último nome batem
        if len(cand_urn) == 0:
            parts = key.split()
            if len(parts) >= 2:
                first_last = f"{parts[0]} {parts[-1]}"
                cand_urn = sub_urn[sub_urn['match_key'].str.contains(parts[0]) & sub_urn['match_key'].str.contains(parts[-1])]
        
        if len(cand_urn) > 0:
            u_row = cand_urn.iloc[0]
            pct_urna_total = u_row['Pct_Total']
            pct_urna_validos = u_row['Pct_Validos']
            votos_urna = u_row['Votos']
            nome_urna = u_row['Candidato']
            partido_urna = u_row['Partido']
            situacao_urna = u_row['Situacao']
        else:
            pct_urna_total = np.nan
            pct_urna_validos = np.nan
            votos_urna = np.nan
            nome_urna = r_mp['Candidato']
            partido_urna = r_mp['Partido']
            situacao_urna = ''
        
        val_mp = r_mp['Valor_num']
        
        dif_total = round(pct_urna_total - val_mp, 2) if pd.notnull(pct_urna_total) and pd.notnull(val_mp) else np.nan
        dif_validos = round(pct_urna_validos - val_mp, 2) if pd.notnull(pct_urna_validos) and pd.notnull(val_mp) else np.nan
        
        merged.append({
            'Estado': estado,
            'Data_Ultima_Pesquisa': data_mp,
            'Candidato_Pesquisa': r_mp['Candidato'],
            'Candidato_Urna': nome_urna,
            'Partido': partido_urna,
            'Situacao': situacao_urna,
            'Media_Ponderada_Pct': val_mp,
            'Urna_Pct_Total': pct_urna_total,
            'Urna_Pct_Validos': pct_urna_validos,
            'Diferenca_vs_Total (Urna - MP)': dif_total,
            'Diferenca_vs_Validos (Urna - MP)': dif_validos,
            'Votos_Absolutos_Urna': votos_urna,
            'Indecisos_Pesquisa_Pct': indecisos_pct
        })

df_comp = pd.DataFrame(merged)

comp_output_csv = r'C:\Users\RED.AyuriReis\.gemini\antigravity-ide\scratch\nexo_map\comparacao_pesquisas_agregador_x_urnas.csv'
df_comp.to_csv(comp_output_csv, index=False, sep=';', encoding='utf-8-sig')
print(f"3. Comparação salva com sucesso em: {comp_output_csv}")
print(f"Total de candidatos/opções comparadas: {len(df_comp)}")

# Estatísticas gerais de erro
valid_diffs_total = df_comp['Diferenca_vs_Total (Urna - MP)'].dropna()
mae_total = valid_diffs_total.abs().mean()
print(f"\n--- Resumo de Acurácia Global ---")
print(f"Erro Médio Absoluto (MAE) vs Votos Totais: {mae_total:.2f} p.p.")

# Comparação do Ceará especificamente
print("\n=== Exemplo Detalhado: Ceará ===")
ce_comp = df_comp[df_comp['Estado'] == 'Ceará'][['Candidato_Pesquisa', 'Partido', 'Media_Ponderada_Pct', 'Urna_Pct_Total', 'Urna_Pct_Validos', 'Diferenca_vs_Total (Urna - MP)', 'Diferenca_vs_Validos (Urna - MP)']]
print(ce_comp.to_string(index=False))
