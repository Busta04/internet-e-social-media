import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from collections import Counter
import re

# ── CONFIG ──────────────────────────────────────────────────────────────────
INPUT_TOKENS = "tokens.csv"
OUTPUT_DIR   = "output/"

import os
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Stopword italiane essenziali (integra pure se vuoi)
STOPWORDS_IT = {
    "essere","avere","fare","dire","andare","vedere","sapere","volere","potere",
    "dovere","stare","venire","dare","tutto","molto","tanto","poco","più","meno",
    "anche","così","come","quando","dove","perché","però","ma","che","non","si",
    "già","ancora","sempre","mai","ora","dopo","prima","poi","qui","là","via",
    "uno","due","tre","anno","mese","giorno","cosa","modo","caso","parte","volta",
    "questo","quello","stesso","altro","nuovo","grande","piccolo","proprio","ogni",
    "io","tu","lui","lei","noi","voi","loro","mi","ti","ci","vi","lo","la","li",
    "le","ne","gli","del","della","dei","degli","delle","nel","nella","nei",
    "negli","nelle","sul","sulla","sui","sugli","sulle","al","alla","ai","agli",
    "alle","dal","dalla","dai","dagli","dalle","col","con","per","tra","fra",
}

# Marcatori di urgenza per analisi 3
URGENZA = {
    "ora","adesso","subito","live","breaking","emergenza","allarme","urgente",
    "immediato","immediatamente","improvviso","improvvisamente","attuale",
    "attualmente","ultimora","aggiornamento","diretta","flash","ultime",
    "poche","minuti","appena","poco","stanotte","stamane","stamattina",
    "stasera","oggi","ieri","domani","presto","tardi","intanto","frattempo",
}

# Keyword tematiche per analisi 1
TEMI = {
    "politica":   ["governo","parlamento","ministro","partito","elezione","legge","decreto"],
    "guerra":     ["guerra","conflitto","attacco","bomba","missile","soldato","esercito"],
    "economia":   ["economia","mercato","borsa","inflazione","euro","pil","crisi"],
    "immigrazione":["migrante","immigrato","sbarco","confine","profugo","rifugiato"],
    "ambiente":   ["clima","ambiente","temperatura","emissione","siccità","alluvione"],
}

# ── CARICAMENTO E PULIZIA ───────────────────────────────────────────────────

print("Carico tokens.csv…")
df = pd.read_csv(INPUT_TOKENS, encoding="utf-8-sig")
df["data"] = pd.to_datetime(df["data"], utc=True, errors="coerce").dt.tz_localize(None)
print(f"  Articoli senza data valida: {df['data'].isna().sum()}")

# ── FILTRO TEMPORALE (modifica qui per tagliare outlier) ──
DATA_INIZIO = "2026-04-15"  # None per non filtrare
DATA_FINE   = "2026-05-14"  # None per non filtrare

if DATA_INIZIO:
    df = df[df["data"].isna() | (df["data"] >= DATA_INIZIO)]
if DATA_FINE:
    df = df[df["data"].isna() | (df["data"] <= DATA_FINE)]

print(f"  Articoli con data valida nel range: {df['data'].notna().sum()} token")
df["data_giorno"] = df["data"].dt.date

# Rimuovi punteggiatura e stopword
df_clean = df[
    (df["upos"].isin({"NOUN","VERB","ADJ","ADV"})) &
    (~df["lemma"].str.lower().isin(STOPWORDS_IT)) &
    (df["lemma"].str.match(r"^[a-zA-Zàèìòùéáíóú]{3,}$"))
].copy()
df_clean["lemma"] = df_clean["lemma"].str.lower()

print(f"✔ Token dopo pulizia: {len(df_clean)} (su {len(df)} totali)")

# ── ANALISI 1 — KEYWORD NEL TEMPO ──────────────────────────────────────────

print("\n── Analisi 1: keyword nel tempo ──")

# Appiattisci tutte le keyword in un unico dict lemma→tema
lemma2tema = {}
for tema, parole in TEMI.items():
    for p in parole:
        lemma2tema[p] = tema

df_temi = df_clean[df_clean["lemma"].isin(lemma2tema)].copy()
df_temi["tema"] = df_temi["lemma"].map(lemma2tema)

# Conta per giorno e tema
pivot = (
    df_temi
    .groupby(["data_giorno","tema"])
    .size()
    .reset_index(name="freq")
    .pivot(index="data_giorno", columns="tema", values="freq")
    .fillna(0)
)
pivot.index = pd.to_datetime(pivot.index)
pivot = pivot.sort_index()

# Salva CSV
pivot.to_csv(OUTPUT_DIR + "temi_nel_tempo.csv")

# Grafico
fig, ax = plt.subplots(figsize=(12, 5))
for col in pivot.columns:
    ax.plot(pivot.index, pivot[col], marker="o", markersize=3, label=col)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
plt.xticks(rotation=45)
ax.set_title("Presenza temi nel tempo")
ax.set_xlabel("Data")
ax.set_ylabel("Occorrenze giornaliere")
ax.legend()
plt.tight_layout()
plt.savefig(OUTPUT_DIR + "temi_nel_tempo.png", dpi=150)
plt.close()
print(f"✔ Salvati: temi_nel_tempo.csv + .png")

# ── ANALISI 2 — CONTESTO ATTORNO A KEYWORD (proto-sentiment) ───────────────

print("\n── Analisi 2: contesto keyword ──")

KEYWORD_SENTIMENT = ["trump","meloni","governo","europa"]
FINESTRA = 5  # token prima e dopo

risultati_contesto = []
for art_id, gruppo in df.groupby("art_id"):
    lemmi = gruppo["lemma"].str.lower().tolist()
    upos  = gruppo["upos"].tolist()
    for i, lemma in enumerate(lemmi):
        if lemma in KEYWORD_SENTIMENT:
            inizio = max(0, i - FINESTRA)
            fine   = min(len(lemmi), i + FINESTRA + 1)
            contesto = [
                lemmi[j] for j in range(inizio, fine)
                if j != i
                and upos[j] in {"ADJ","NOUN","VERB","ADV"}
                and lemmi[j] not in STOPWORDS_IT
                and len(lemmi[j]) > 3
            ]
            risultati_contesto.append({
                "art_id":  art_id,
                "keyword": lemma,
                "contesto": " ".join(contesto),
            })

df_contesto = pd.DataFrame(risultati_contesto)
df_contesto.to_csv(OUTPUT_DIR + "contesto_keyword.csv", index=False, encoding="utf-8-sig")

# Top parole per contesto di ogni keyword
print("  Parole più frequenti nel contesto:")
for kw in KEYWORD_SENTIMENT:
    sub = df_contesto[df_contesto["keyword"] == kw]["contesto"]
    if sub.empty:
        print(f"  {kw}: nessuna occorrenza")
        continue
    tutti = " ".join(sub).split()
    top = Counter(tutti).most_common(8)
    print(f"  {kw}: {top}")

print(f"✔ Salvato: contesto_keyword.csv")

# ── ANALISI 3 — MARCATORI DI URGENZA ───────────────────────────────────────

print("\n── Analisi 3: marcatori di urgenza ──")

df["lemma_low"] = df["lemma"].str.lower()
df_urgenza = df[df["lemma_low"].isin(URGENZA)].copy()

# Conta marcatori per articolo
urgenza_per_art = (
    df_urgenza.groupby("art_id")
    .size()
    .reset_index(name="n_urgenza")
)

# Lunghezza articolo in token
lunghezza = df.groupby("art_id").size().reset_index(name="n_token")

# Unisci e calcola densità
urgenza_merge = urgenza_per_art.merge(lunghezza, on="art_id")
urgenza_merge["densita_urgenza"] = urgenza_merge["n_urgenza"] / urgenza_merge["n_token"]
urgenza_merge = urgenza_merge.sort_values("densita_urgenza", ascending=False)

urgenza_merge.to_csv(OUTPUT_DIR + "urgenza_per_articolo.csv", index=False, encoding="utf-8-sig")

# Istogramma densità
fig, ax = plt.subplots(figsize=(10, 4))
ax.hist(urgenza_merge["densita_urgenza"], bins=30, color="steelblue", edgecolor="white")
ax.set_title("Distribuzione densità marcatori di urgenza per articolo")
ax.set_xlabel("Densità (marcatori / token totali)")
ax.set_ylabel("N articoli")
plt.tight_layout()
plt.savefig(OUTPUT_DIR + "urgenza_distribuzione.png", dpi=150)
plt.close()

# Top 10 articoli più allarmistici
print("  Top 10 articoli per densità urgenza:")
print(urgenza_merge.head(10)[["art_id","n_urgenza","n_token","densita_urgenza"]].to_string(index=False))
print(f"✔ Salvati: urgenza_per_articolo.csv + urgenza_distribuzione.png")

print("\n✅ Analisi completate. Output in cartella output/")