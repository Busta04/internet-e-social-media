import re
import os
import time
from newspaper import Article, Config

# Configurazione Browser
config = Config()
config.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'

def fase_1_pulizia(file_input, file_link_puliti):
    """Estrae i link dal testo sporco e li salva in un file dedicato."""
    print("--- FASE 1: Estrazione e Pulizia Link ---")
    with open(file_input, 'r', encoding='utf-8') as f:
        contenuto = f.read()
    
    links = re.findall(r'(https?://[^\s]+)', contenuto)
    links_unici = list(dict.fromkeys(links))
    
    with open(file_link_puliti, 'w', encoding='utf-8') as f_out:
        for link in links_unici:
            f_out.write(f"{link}\n")
    
    print(f"✅ Trovati {len(links_unici)} link unici. Salvati in: {file_link_puliti}\n")
    return links_unici

def fase_2_estrazione_contenuti(file_link_puliti, file_output_testo):
    """Legge i link puliti e scarica il testo degli articoli."""
    print("--- FASE 2: Download Articoli ---")
    
    if not os.path.exists(file_link_puliti):
        print("Errore: File link puliti non trovato.")
        return

    with open(file_link_puliti, 'r', encoding='utf-8') as f_in:
        links = [line.strip() for line in f_in if line.strip()]

    with open(file_output_testo, 'w', encoding='utf-8') as f_out:
        for i, url in enumerate(links, 1):
            try:
                print(f"[{i}/{len(links)}] Elaborazione: {url}")
                
                articolo = Article(url, config=config, language='it')
                articolo.download()
                articolo.parse()
                
                data = articolo.publish_date if articolo.publish_date else "Data non disponibile"
                nome_giornale = articolo.source_url.replace('https://', '').replace('www.', '').split('/')[0]

                f_out.write(f"<Art({i})>\n")
                f_out.write(f"{nome_giornale}\n")
                f_out.write(f"{data}\n")
                f_out.write(f"{articolo.title}\n")
                f_out.write(f"{articolo.text}\n\n")
                f_out.write("-" * 50 + "\n\n")
                
                # Pausa anti-ban
                time.sleep(0.5) 
                
            except Exception as e:
                print(f"   ⚠️ Salto articolo {i} a causa di un errore: {e}")

    print(f"\n✅ Operazione completata! Archivio creato in: {file_output_testo}")

# --- ESECUZIONE ---
FILE_SPORCO = 'link.txt'
FILE_LINK_PULITI = 'link_puliti.txt'
FILE_ARCHIVIO_FINALE = 'archivio_articoli.txt'

fase_1_pulizia(FILE_SPORCO, FILE_LINK_PULITI)
fase_2_estrazione_contenuti(FILE_LINK_PULITI, FILE_ARCHIVIO_FINALE)