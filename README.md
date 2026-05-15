# internet-e-social-media
Progetto universitario

Struttura codici

## scraper
dato il file *link.txt* estrae tutti i link che vi trova (nonverifica duplicati o pertinenza) e li copia sul file *link_puliti.txt*
successivamente, grazie alla libreria *newspaper3k*, estrae da ogni link titolo, testo, data e incolla tutto sul file *archivio_articoli.txt* nels eguete formato:

<art(n)>

Titolo

Data

Testo

/---------
## analisi_UDPipe
effettua la conversione e catalogazione dei dati presenti in *archivio_articoli.txt* generando un file csv catalogando tutte le parole presenti e associandole al giornale e alla data

## analisi_dati
effettua l'analisi vera e propria
attualmente:

-elimina stopword

-effettua un analisi di contesto degli articoli

-effettua un analisi sulla presenza di locuzioni d'urgenza


