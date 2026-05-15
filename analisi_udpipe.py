import re
import pandas as pd
from ufal.udpipe import Model, Pipeline, ProcessingError

CORPUS_FILE   = "archivio_articoli.txt"
MODEL_FILE    = "italian-isdt-ud-2.5-191206.udpipe"
OUTPUT_TOKENS = "tokens.csv"
OUTPUT_FREQ   = "frequenze_lemmi.csv"

POS_CONTENT = {"NOUN", "VERB", "ADJ", "ADV"}

def parse_corpus(path):
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    blocchi = re.split(r"-{10,}", raw)
    articoli = []
    for blocco in blocchi:
        blocco = blocco.strip()
        if not blocco:
            continue
        m = re.match(r"<Art\((\d+)\)>\s*\n(.+?)\n(.+?)\n(.+)", blocco, re.DOTALL)
        if not m:
            continue
        articoli.append({
            "id":      int(m.group(1)),
            "testata": m.group(2).strip(),
            "data":    m.group(3).strip(),
            "testo":   m.group(4).strip(),
        })
    print(f"✔ Articoli trovati: {len(articoli)}")
    return articoli

def process_article(pipeline, articolo):
    error = ProcessingError()
    conllu = pipeline.process(articolo["testo"], error)
    if error.occurred():
        print(f"  ⚠ Errore art {articolo['id']}: {error.message}")
        return []
    tokens = []
    for line in conllu.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        campi = line.split("\t")
        if len(campi) < 6:
            continue
        if "-" in campi[0] or "." in campi[0]:
            continue
        tokens.append({
            "art_id":  articolo["id"],
            "testata": articolo["testata"],
            "data":    articolo["data"],
            "forma":   campi[1],
            "lemma":   campi[2],
            "upos":    campi[3],
        })
    return tokens

def main():
    articoli = parse_corpus(CORPUS_FILE)

    print("Carico il modello UDPipe…")
    model = Model.load(MODEL_FILE)
    pipeline = Pipeline(model, "tokenize", Pipeline.DEFAULT, Pipeline.DEFAULT, "conllu")
    print("✔ Modello caricato")

    tutti_i_token = []
    for i, art in enumerate(articoli):
        if i % 50 == 0:
            print(f"  Processo articolo {i+1}/{len(articoli)}…")
        tutti_i_token.extend(process_article(pipeline, art))

    print(f"✔ Token totali estratti: {len(tutti_i_token)}")

    df = pd.DataFrame(tutti_i_token)
    df.to_csv(OUTPUT_TOKENS, index=False, encoding="utf-8-sig")
    print(f"✔ Salvato: {OUTPUT_TOKENS}")

    df_content = df[df["upos"].isin(POS_CONTENT)].copy()
    df_content["lemma"] = df_content["lemma"].str.lower()
    freq = (
        df_content
        .groupby(["lemma", "upos"])
        .size()
        .reset_index(name="freq")
        .sort_values("freq", ascending=False)
    )
    freq.to_csv(OUTPUT_FREQ, index=False, encoding="utf-8-sig")
    print(f"✔ Salvato: {OUTPUT_FREQ}  ({len(freq)} lemmi unici)")

if __name__ == "__main__":
    main()