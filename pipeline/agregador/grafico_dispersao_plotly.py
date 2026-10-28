import os
import json
import unicodedata
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import shutil

# Carregar JSON estruturado com Votos Válidos
json_path = r'c:\Users\RED.AyuriReis\Downloads\Apurador_real\dados_grafico_dispersao.json'
with open(json_path, 'r', encoding='utf-8') as f:
    estados_data = json.load(f)

COLOR_PALETTE = [
    '#38bdf8', '#ef4444', '#3b82f6', '#10b981', '#f59e0b',
    '#a855f7', '#ec4899', '#14b8a6', '#f97316', '#6366f1', '#84cc16'
]

def criar_figura_dispersao(estado='Ceará', metrica='pct_validos', candidatos_selecionados=None):
    """
    Gera o gráfico de dispersão com Média Móvel Ponderada e Destaque das Urnas.
    metrica: 'pct_validos' (padrão oficial TSE) ou 'pct_total' (estimulada com brancos/nulos)
    """
    if estado not in estados_data:
        estado = list(estados_data.keys())[0]
    
    st_info = estados_data[estado]
    cands_lista = st_info['candidatos_lista']
    
    # Se metrica for votos válidos, remove candidatos não válidos por padrão
    if metrica == 'pct_validos':
        valid_cands = [c for c in cands_lista if not c.startswith('Indeciso') and not c.startswith('Branco')]
        if candidatos_selecionados is None:
            candidatos_selecionados = valid_cands
    else:
        if candidatos_selecionados is None:
            candidatos_selecionados = [c for c in cands_lista if not c.startswith('Indeciso') and not c.startswith('Branco')]
    
    fig = go.Figure()
    
    for idx, cand_nome in enumerate(cands_lista):
        if cand_nome not in candidatos_selecionados and len(candidatos_selecionados) > 0:
            continue
        
        cand = st_info['candidatos'][cand_nome]
        cor = '#94a3b8' if ('Branco' in cand_nome or 'Indeciso' in cand_nome) else COLOR_PALETTE[idx % len(COLOR_PALETTE)]
        
        # 1. Bolinhas de Dispersão das Pesquisas Individuais (Válidos ou Total)
        if cand['pesquisas'] and len(cand['pesquisas']) > 0:
            x_pesq = [p['data'] for p in cand['pesquisas']]
            y_pesq = [p['valor_validos'] if metrica == 'pct_validos' else p['valor'] for p in cand['pesquisas']]
            
            hover_pesq = [
                f"<b>{cand_nome}</b><br>"
                f"🏢 Instituto: {p['instituto']}<br>"
                f"📅 Data: {p['data_str']}<br>"
                f"📊 Votos Válidos: <b>{p['valor_validos']:.2f}%</b><br>"
                f"<span style='color:#94a3b8; font-size:11px;'>(Estimulada Total: {p['valor']:.2f}%)</span>"
                if metrica == 'pct_validos' else
                f"<b>{cand_nome}</b><br>"
                f"🏢 Instituto: {p['instituto']}<br>"
                f"📅 Data: {p['data_str']}<br>"
                f"📊 Valor: <b>{p['valor']:.2f}%</b>"
                for p in cand['pesquisas']
            ]
            
            fig.add_trace(go.Scatter(
                x=x_pesq,
                y=y_pesq,
                mode='markers',
                name=f"{cand_nome} (Pesquisas)",
                marker=dict(
                    color=cor,
                    size=8,
                    opacity=0.65,
                    line=dict(color='white', width=0.5)
                ),
                text=hover_pesq,
                hoverinfo='text',
                legendgroup=cand_nome,
                showlegend=False
            ))
        
        # 2. Linha da Média Móvel Ponderada
        if cand['media_ponderada'] and len(cand['media_ponderada']) > 0:
            x_mp = [p['data'] for p in cand['media_ponderada']]
            y_mp = [p['valor_validos'] if metrica == 'pct_validos' else p['valor'] for p in cand['media_ponderada']]
            
            hover_mp = [
                f"<b>{cand_nome}</b> (Média Ponderada)<br>"
                f"📅 Data: {p['data_str']}<br>"
                f"📈 Média ({'Válidos' if metrica == 'pct_validos' else 'Total'}): <b>{(p['valor_validos'] if metrica == 'pct_validos' else p['valor']):.2f}%</b>"
                for p in cand['media_ponderada']
            ]
            
            fig.add_trace(go.Scatter(
                x=x_mp,
                y=y_mp,
                mode='lines',
                name=cand_nome,
                line=dict(
                    color=cor,
                    width=3.5,
                    shape='spline'
                ),
                text=hover_mp,
                hoverinfo='text',
                legendgroup=cand_nome
            ))
        
        # 3. Bolinha de Destaque Oficial das Urnas (04/10/2026)
        if cand['resultado_urna']:
            u = cand['resultado_urna']
            target_val = u['pct_validos'] if metrica == 'pct_validos' else u['pct_total']
            ult_media = cand['ultima_media_validos'] if metrica == 'pct_validos' else cand['ultima_media_total']
            diff_text = ""
            if ult_media is not None:
                diff = target_val - ult_media
                sinal = "+" if diff >= 0 else ""
                diff_text = f"<br>🎯 Desvio vs Média: <b>{sinal}{diff:.2f} p.p.</b>"
            
            hover_urna = (
                f"🗳️ <b>RESULTADO OFICIAL URNAS (04/10/2026)</b><br>"
                f"👤 <b>{cand_nome}</b> ({u['partido']}) - <i>{u['situacao']}</i><br>"
                f"📊 Resultado Urna: <b>{target_val:.2f}%</b> "
                f"({'Votos Válidos' if metrica == 'pct_validos' else 'Total Apurado'})<br>"
                f"🗳️ Votos: <b>{u['votos']:,}</b>"
                f"{diff_text}"
            ).replace(',', '.')
            
            fig.add_trace(go.Scatter(
                x=[u['data']],
                y=[target_val],
                mode='markers',
                name=f"{cand_nome} (Urnas)",
                marker=dict(
                    color=cor,
                    size=17,
                    symbol='circle',
                    line=dict(color='#fbbf24', width=3.5)
                ),
                text=[hover_urna],
                hoverinfo='text',
                legendgroup=cand_nome,
                showlegend=False
            ))

    # Layout Dark Moderno
    metrica_label = "Votos Válidos (Critério Oficial TSE)" if metrica == 'pct_validos' else "% sobre Total Apurado (c/ Brancos/Nulos)"
    fig.update_layout(
        title=dict(
            text=f"<b>{estado}:</b> Dispersão das Pesquisas, Média Ponderada e Resultado das Urnas<br><sup>Metodologia: {metrica_label} • Destaque Dourado = 04/10/2026</sup>",
            font=dict(family="Inter, sans-serif", size=18, color="#f8fafc")
        ),
        paper_bgcolor="#090d16",
        plot_bgcolor="#111827",
        hovermode="closest",
        legend=dict(
            font=dict(family="Inter, sans-serif", size=12, color="#94a3b8"),
            bgcolor="rgba(19, 27, 44, 0.7)",
            bordercolor="rgba(255, 255, 255, 0.1)",
            borderwidth=1,
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis=dict(
            title="Linha do Tempo",
            title_font=dict(color="#94a3b8"),
            tickfont=dict(color="#94a3b8"),
            gridcolor="rgba(255, 255, 255, 0.05)",
            showline=True,
            linecolor="rgba(255, 255, 255, 0.15)"
        ),
        yaxis=dict(
            title="Votos Válidos (%)" if metrica == 'pct_validos' else "Intenção de Voto (%)",
            title_font=dict(color="#94a3b8"),
            tickfont=dict(color="#94a3b8"),
            gridcolor="rgba(255, 255, 255, 0.08)",
            showline=True,
            linecolor="rgba(255, 255, 255, 0.15)",
            ticksuffix="%"
        ),
        margin=dict(l=60, r=40, t=90, b=60)
    )
    
    return fig

if __name__ == '__main__':
    fig = criar_figura_dispersao(estado='Ceará', metrica='pct_validos')
    out_plotly = r'c:\Users\RED.AyuriReis\Downloads\Apurador_real\grafico_dispersao_ceara_validos_plotly.html'
    fig.write_html(out_plotly)
    print(f"Gráfico Plotly em Votos Válidos gerado e salvo em: {out_plotly}")
