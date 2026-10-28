import pandas as pd
import os

CSV_INPUT = r"C:\Users\RED.AyuriReis\Downloads\dados_secoes_ceara_presidente_1Te2T.csv"
CSV_OUT_DOWNLOADS = r"C:\Users\RED.AyuriReis\Downloads\71_locais_votacao_virada_ceara_presidente_2026.csv"
CSV_OUT_PROJECT = r"C:\Users\RED.AyuriReis\.gemini\antigravity-ide\scratch\nexo_map\71_locais_votacao_virada_ceara_presidente_2026.csv"

df = pd.read_csv(CSV_INPUT, sep=";", encoding="utf-8-sig")

# Filtra apenas os que tiveram virada
df_viradas = df[df["Teve_Virada"] == "Sim"].copy()

print(f"Total de locais com virada encontrados: {len(df_viradas)}")

# Adiciona colunas analíticas extras para o repórter
df_viradas["Diferenca_1T_Votos"] = (df_viradas["Flavio_Votos_1T"] - df_viradas["Lula_Votos_1T"])
df_viradas["Diferenca_2T_Votos"] = (df_viradas["Lula_Votos_2T"] - df_viradas["Flavio_Votos_2T"])

# Ordena por maior colégio eleitoral (votos válidos no 2º turno)
df_viradas = df_viradas.sort_values(by="Validos_2T", ascending=False)

# Seleciona e renomeia colunas para máxima clareza na redação
colunas = [
    "Municipio",
    "Zona",
    "Local_Votacao",
    "Bairro",
    "Endereco",
    "Validos_1T",
    "Flavio_Votos_1T",
    "Flavio_Pct_1T",
    "Lula_Votos_1T",
    "Lula_Pct_1T",
    "Vencedor_1T",
    "Diferenca_1T_Votos",
    "Validos_2T",
    "Lula_Votos_2T",
    "Lula_Pct_2T",
    "Flavio_Votos_2T",
    "Flavio_Pct_2T",
    "Vencedor_2T",
    "Diferenca_2T_Votos",
    "Tipo_Virada",
    "Lula_Variacao_Votos",
    "Flavio_Variacao_Votos",
    "Lula_Variacao_Pct_pp",
    "Flavio_Variacao_Pct_pp",
    "Balanco_Liquido_Lula"
]

df_export = df_viradas[colunas].copy()

# Renomeia colunas para padrão amigável do Excel
df_export = df_export.rename(columns={
    "Diferenca_1T_Votos": "Vantagem_Flavio_1T",
    "Diferenca_2T_Votos": "Vantagem_Lula_2T",
    "Balanco_Liquido_Lula": "Inversao_Saldo_Total_Votos",
    "Lula_Variacao_Votos": "Lula_Novos_Votos_2T",
    "Flavio_Variacao_Votos": "Flavio_Novos_Votos_2T",
    "Lula_Variacao_Pct_pp": "Lula_Crescimento_pp",
    "Flavio_Variacao_Pct_pp": "Flavio_Crescimento_pp"
})

# Salva em UTF-8 com BOM e separador ponto-e-vírgula para Excel
df_export.to_csv(CSV_OUT_DOWNLOADS, sep=";", index=False, encoding="utf-8-sig")
df_export.to_csv(CSV_OUT_PROJECT, sep=";", index=False, encoding="utf-8-sig")

print(f"Salvo em Downloads: {CSV_OUT_DOWNLOADS}")
print(f"Salvo no Projeto: {CSV_OUT_PROJECT}")
print("\nResumo por Município:")
print(df_export["Municipio"].value_counts())

