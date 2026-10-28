import pandas as pd

df = pd.read_csv(r"C:\Users\RED.AyuriReis\Downloads\dados_secoes_ceara_presidente_1Te2T.csv", sep=";", encoding="utf-8-sig")

print("=== 1. TOP 5 LOCAIS COM MAIOR CRESCIMENTO ABSOLUTO DE LULA (2T - 1T) ===")
top_lula = df.sort_values(by="Lula_Variacao_Votos", ascending=False).head(5)
for i, (_, r) in enumerate(top_lula.iterrows(), 1):
    print(f"{i}º | {r['Local_Votacao']}")
    print(f"     Município: {r['Municipio']} (Zona {r['Zona']}, Bairro: {r['Bairro']})")
    print(f"     1º Turno: {r['Lula_Votos_1T']} votos ({r['Lula_Pct_1T']}%)")
    print(f"     2º Turno: {r['Lula_Votos_2T']} votos ({r['Lula_Pct_2T']}%)")
    print(f"     Aumento absoluto: +{r['Lula_Variacao_Votos']} votos (+{r['Lula_Variacao_Pct_pp']} pp)\n")

print("=== 2. TOP 5 LOCAIS COM MAIOR CRESCIMENTO ABSOLUTO DE FLÁVIO BOLSONARO (2T - 1T) ===")
top_bolso = df.sort_values(by="Flavio_Variacao_Votos", ascending=False).head(5)
for i, (_, r) in enumerate(top_bolso.iterrows(), 1):
    print(f"{i}º | {r['Local_Votacao']}")
    print(f"     Município: {r['Municipio']} (Zona {r['Zona']}, Bairro: {r['Bairro']})")
    print(f"     1º Turno: {r['Flavio_Votos_1T']} votos ({r['Flavio_Pct_1T']}%)")
    print(f"     2º Turno: {r['Flavio_Votos_2T']} votos ({r['Flavio_Pct_2T']}%)")
    print(f"     Aumento absoluto: +{r['Flavio_Variacao_Votos']} votos (+{r['Flavio_Variacao_Pct_pp']} pp)\n")

print("=== 3. VIRA-VOTOS (LOCAIS COM VIRADA DE VENCEDOR) ===")
viradas = df[df["Teve_Virada"] == "Sim"]
print(f"Total de locais com virada de vencedor: {len(viradas)}")
print(f"Flávio 1T -> Lula 2T: {len(df[df['Tipo_Virada'] == 'Flavio Bolsonaro para Lula'])}")
print(f"Lula 1T -> Flávio 2T: {len(df[df['Tipo_Virada'] == 'Lula para Flavio Bolsonaro'])}\n")

print("TOP 5 MAIORES COLÉGIOS ELEITORAIS QUE VIRARAM (Por Total de Votos Válidos 2T):")
top_viradas = viradas.sort_values(by="Validos_2T", ascending=False).head(5)
for i, (_, r) in enumerate(top_viradas.iterrows(), 1):
    print(f"{i}º | {r['Local_Votacao']}")
    print(f"     Município: {r['Municipio']} (Zona {r['Zona']}, Bairro: {r['Bairro']}) | Total Válidos 2T: {r['Validos_2T']}")
    print(f"     1º Turno: Flávio {r['Flavio_Votos_1T']} ({r['Flavio_Pct_1T']}%) x Lula {r['Lula_Votos_1T']} ({r['Lula_Pct_1T']}%) [Flávio +{r['Flavio_Votos_1T']-r['Lula_Votos_1T']}]")
    print(f"     2º Turno: Lula {r['Lula_Votos_2T']} ({r['Lula_Pct_2T']}%) x Flávio {r['Flavio_Votos_2T']} ({r['Flavio_Pct_2T']}%) [Lula +{r['Lula_Votos_2T']-r['Flavio_Votos_2T']}]")
    print(f"     Variação: Lula {r['Lula_Variacao_Votos']:+} votos | Flávio {r['Flavio_Variacao_Votos']:+} votos | Saldo virado em +{r['Balanco_Liquido_Lula']} votos a favor de Lula\n")

print("=== 4. MAIORES INVERSÕES / BALANÇOS LÍQUIDOS ===")
print("TOP 3 ONDE LULA MAIS AMPLIOU A DISTÂNCIA:")
for i, (_, r) in enumerate(df.sort_values(by="Balanco_Liquido_Lula", ascending=False).head(3).iterrows(), 1):
    print(f"{i}º | {r['Local_Votacao']} ({r['Municipio']}): Ganho de margem de +{r['Balanco_Liquido_Lula']} votos (Saldo 1T: {r['Saldo_Lula_1T']:+} -> Saldo 2T: {r['Saldo_Lula_2T']:+})")

print("\nTOP 3 ONDE FLÁVIO MAIS ENCURTOU A DISTÂNCIA:")
for i, (_, r) in enumerate(df.sort_values(by="Balanco_Liquido_Flavio", ascending=False).head(3).iterrows(), 1):
    print(f"{i}º | {r['Local_Votacao']} ({r['Municipio']}): Flávio tirou +{r['Balanco_Liquido_Flavio']} votos de diferença (Saldo Lula 1T: {r['Saldo_Lula_1T']:+} -> Saldo Lula 2T: {r['Saldo_Lula_2T']:+})")

