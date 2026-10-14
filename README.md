# MachineInnovators-Inc
 Pipeline MLOps per il monitoraggio del sentiment sui social


## Avvio del progetto

Per avviare il progetto la sequenza di comandi da seguire è questa:

Creazione di una rete da far condividere ai container:

```bash
docker network create mlops-network
```

Avvio delle API (girano sulla porta 8000):

```bash
docker compose -f docker-compose.yml up -d
```


Avvio di Grafana (gira sulla porta 3000):

```bash
docker compose -f monitoring/docker-compose.yml up -d
```

Inizializzazione e avvio di Airflow (gira sulla porta 8080):

```bash
docker compose -f airflow/docker-compose.yaml up airflow-init
docker compose -f airflow/docker-compose.yaml up -d
```

Per poter avere dei dati a disposizione di Grafana, sarà necessario avviare uno script che una volta avviato manderà richieste alle API fino a quando non viene stoppato, è documentato nella sezione **Generazione dati di test**. Per avviarlo bisogna:

Creare un ambiente virtuale e attivare l'ambiente virtuale:

```bash
python -m venv .venv
source .venv/bin/activate
```

installare la libreria di python 'request':
```bash
python -m pip install requests
```

lanciare lo script:
```bash
python scripts\generate_monitoring_data.py
```

lo script continuerà ad inviare dati fino a quando l'utente non premerà ctrl + C per bloccarne l'esecuzione.

## Strumenti utilizzati

### 1. Creazione e attivazione del virtual environment

Creare l'ambiente virtuale:

```bash
python -m venv .venv
```

Attivare l'ambiente virtuale:

```bash
source .venv/bin/activate
```

Installare le dipendenze:

```bash
pip install -r requirements.txt
```

### 2. Avvio dell'API

Dalla root del progetto, con il virtual environment attivo:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

L'API sarà disponibile su:

```text
http://localhost:8000
```

### 3. Esecuzione dei test

Per eseguire tutti i test automatici:

```bash
python -m pytest -v
```

### 4. Formatting con Black

Per formattare automaticamente il codice:

```bash
black app tests scripts
```

Per verificare che il codice sia già formattato:

```bash
black --check app tests scripts
```

### 5. Linting con Pylint

Per controllare la qualità del codice:

```bash
pylint app tests scripts
```

### 6. Docker

L'applicazione può essere eseguita in un container Docker.

Il file `Dockerfile` definisce l'immagine dell'applicazione usando Python 3.11-slim.

Il file `requirements-docker.txt` contiene le dipendenze minime necessarie
all'esecuzione dell'API nel container:

```text
fastapi
uvicorn[standard]
transformers
torch
```

Il file `requirements.txt` contiene invece le dipendenze dell'ambiente di
sviluppo incluse quelle usate per test, linting e formatting.

#### Build dell'immagine

Dalla root del progetto, eseguire:

```bash
docker build -t sentiment-service .
```

Per visualizzare un output più dettagliato durante la build:

```bash
docker build --progress=plain -t sentiment-service .
```

#### Avvio del container

Dopo la build, avviare il container:

```bash
docker run --rm -p 8000:8000 sentiment-service
```

L'opzione `--rm` elimina automaticamente il container quando viene fermato.

#### PyTorch CPU-only

Il modello Hugging Face viene eseguito localmente tramite la libreria `transformers`. Anche se il codice dell'applicazione non importa direttamente `torch`, PyTorch è necessario come backend per caricare ed eseguire il modello.

la versione di PyTorch è stata definita in un file separato:

```text
requirements-docker-torch-cpu.txt
```

Contenuto:

```text
--index-url https://download.pytorch.org/whl/cpu
torch
```

In modo da poter specificare di scaricare la versione CPU-only.

Questa separazione evita che vengano installate dipendenze di Pytorch non necessarie per questo servizio. Ho dovuto farlo perchè altrimenti CodeSpace nonostante avessi creato la versione con più risorse andava in difficoltà quando provavo a fare docker build.

Nel Dockerfile le dipendenze vengono installate in due passaggi:

```dockerfile
RUN pip install --no-cache-dir -r requirements-docker.txt \
    && pip install --no-cache-dir -r requirements-docker-torch-cpu.txt
```

### 7. Monitoraggio con Grafana

#### Raccolta delle metriche

Le metriche vengono raccolte dall'API stessa in `app/monitoring.py`:

- il middleware FastAPI registra ogni richiesta con status code e tempo di risposta
- l'endpoint `/inference` registra la classe predetta, la confidenza e la lunghezza del testo

Le chiamate a `/health` e agli endpoint `/monitoring/*` non vengono conteggiate, altrimenti le interrogazioni di Grafana falserebbero volume e latenza.

Ogni 30 secondi un task in background dell'app salva nello storico `data/monitoring_history.json` uno snapshot con le metriche dell'ultimo intervallo, poi azzera i contatori dell'intervallo. All'inizio salvavo i totali cumulativi dall'avvio, ma l'aumentare dei numeri farebbe perdere traccia dei picchi.

Ogni snapshot contiene:
- `requests`: richieste ricevute nell'intervallo 
- `client_errors`, `client_error_rate` : risposte 4xx (input non validi, dipendono da ciò che manda il client) 
- `server_errors`, `error_rate`: risposte 5xx (errori del servizio) 
- `avg_latency_ms`, `max_latency_ms`: tempo di risposta medio e massimo in ms
- `predictions`: predizioni andate a buon fine 
- `positive_*`, `neutral_*`, `negative_*`: numero e rate di predizioni per classe 
- `avg_text_length` | lunghezza media dei testi in caratteri 
- `avg_confidence` | confidenza media del modello 
- `timestamp`, `window_seconds` | fine e durata dell'intervallo (UTC) 


#### Avvio dello stack con Grafana

Per avviare API e Grafana:

```bash
docker compose -f 'monitoring/docker-compose.yml' up -d --build
```

Grafana è disponibile su `http://localhost:3000` (utente e password di default `admin` / `admin`).

Se dopo aver fatto `compose-up` non è stata aggiunta nella liste delle porte la porta 3000, basta fara `Aggiungi porta` e mettere la 3000 e il servizio di Grafana sarà disponibile.

Datasource, dashboard e alert non vanno configurati a mano: Grafana li carica all'avvio dai file che sono in `monitoring/grafana/`.

In questo modo chi riceve il progetto trova la dashboard già pronta e le modifiche alla dashboard passano dalla repository. Per modificarla: la si cambia dall'interfaccia di Grafana, si esporta il JSON (Export > Export as JSON) e lo si sostituisce in `sentiment-api.json`.

Prima di andare su Grafana, quando le api sono avviate la prima cosa che sarebbe meglio fare è avviare lo script per la generazione dei dati di test che permetterà di avere dei dati per dashboar e alert.

#### Dashboard

La dashboard `MachineInnovators-Inc` contiene:

- richieste, error rate, latenza media e negative rate dall'avvio del servizio;
- distribuzione delle classi predette e negative rate, con la soglia dell'alert;
- lunghezza media dei testi e confidenza media del modello, utili per accorgersi di un data drift.

#### Alert

Sono configurati due alert:

- `Negative rate elevata`: predizioni negative > 50% delle predizioni degli ultimi 30 minuti, serve per accorgersi in tempo quando il sentiment cambia
- `Latenza media elevata`: latenza media degli ultimi 5 minuti > 1 s


#### Generazione dati di test

Per avere dati da visualizzare nella dashboard ho creato lo script:

```bash
scripts/generate_monitoring_data.py
```

Lo script invia richieste di esempio all'API (con dei testi di esempio trovati per il modello) a intervalli casuali fino a quando l'utente non esce con ctrl + C

Per eseguirlo:

```bash
python scripts/generate_monitoring_data.py
```

Con l'opzione `--scenario negative` la maggior parte dei messaggi inviati diventa negativa: serve a simulare un cambio di sentiment nei tweet e verificare che l'alert sul negative rate si attivi

```bash
python scripts/generate_monitoring_data.py --scenario negative
```

Si possono modificare anche gli intervalli tra una richiesta e l'altra con `--min-wait` e `--max-wait` (in secondi)

### 8. Airflow

E' stato aggiunto Airflow utilizzando la configurazione ufficiale fornita dal progetto.

#### Installazione e configurazione

Dalla cartella del progetto, scaricare il file `docker-compose.yaml` della versione 2.5.0:

```bash
curl -LfO '[https://airflow.apache.org/docs/apache-airflow/2.5.0/docker-compose.yaml](https://airflow.apache.org/docs/apache-airflow/2.5.0/docker-compose.yaml)'
```

E' necessario creare le cartelle utilizzate da Airflow per i DAG, i log e i plugin, e generare il file `.env` contenente l’UID dell’utente corrente, possiamo farlo con questi due comandi:

```bash
mkdir -p ./dags ./logs ./plugins
echo -e "AIRFLOW_UID=$(id -u)" > .env
```

E' stato aggiunto il .gitignore nella cartella airflow/logs per evitare che il log finiscano nel repository

#### Inizializzazione

Prima di avviare Airflow, eseguire il servizio di inizializzazione:

```bash
docker compose up airflow-init
```

#### Avvio

Dopo l’inizializzazione, avviare Airflow con:

```bash
docker compose up
```

L’interfaccia web è disponibile all’indirizzo:

```text
http://localhost:8080
```



### 9. Data drift e concept drift

Il monitoraggio non serve solo per controllare che l'API funzioni, ma anche per capire se il modello resta affidabile nel tempo. In paritcolare possono verificarsi due problemi diversi:
- **Data drift**: cambiano i testi che arrivano al modello, ma il modo in cui un testo esprime un sentiment rimane simile.   
  Per esempio, i commenti possono diventare più lunghi, contenere più hashtag, più slang oppure essere scritti in una lingua diversa da quella vista durante l'addestramento del modello.
- **Concept drift**: cambia la relazione tra testo e sentiment.  
  Per esempio, una frase o un modo di scrivere che prima veniva percepito come neutro può ad un certo punto diventare in realtà negativo

#### Segnali da monitorare

I principali segnali a cui prestare attenzione sono:
- **Aumento della lunghezza media dei testi**: può indicare un data drift, perché arrivano testi diversi da quelli abituali
- **Calo della confidenza media**: può indicare che il modello riceve testi meno simili a quelli visti in addestramento
- **Cambio improvviso nella distribuzione positive / neutral / negative**: può indicare un concept drift oppure un cambiamento reale nell'opinione del pubblico
- **Aumento della negative rate**: può indicare un deterioramento della reputazione, ma anche un possibile drift
- **Calo di accuracy o macro-F1 sul dataset etichettato**: indica che il modello non sta più generalizzando bene sui dati recenti
- **Aumento di testi vuoti, molto corti o fuori dominio**: può indicare un problema di qualità o copertura dei dati in ingresso

L'API raccoglie già alcune metriche utili per notare questi cambiamenti:

- lunghezza media dei testi in ingresso
- confidenza media del modello
- distribuzione delle predizioni positive, neutral e negative
- negative rate

Questi dati sono visibili nella dashboard Grafana e permettono di notare rapidamente un comportamento anomalo.

Però un aumento della negative rate **non dimostra da solo** che sia avvenuto un drift. Può anche significare che, in quel periodo, gli utenti stanno davvero esprimendo più opinioni negative, ad esempio dopo una notizia negativa sull'azienda.

Per confermare un sospetto di drift serve una valutazione su dati recenti etichettati. Questo è il compito del dag Airflow `evaluate_model_retraining` che carica il dataset con testi e label reali, chiama l'API, calcola accuracy e macro-F1 e salva un report. Se la qualità scende sotto la soglia configurata, il DAG segnala la necessità di un retraining.

In un progetto reale questo ciclo dovrebbe esssere schedulato ripetetuto periodicamente: si raccolgono nuovi dati, si etichetta un campione, si valuta il modello e così facendo si può decidere se è necessario addestrarlo nuovamente.


### 10. Deploy su Hugging Face

Il deploy su Hugging Face non è stato implementato perché, durante la creazione dello Space con il mio account personale le opzioni Docker e Gradio richiedevano un piano a pagamento.
Per questo progetto avrei usato Docker, perché l'applicazione è un'API FastAPI ed è già containerizzata.
Dato che il deploy su Hugging Face è facoltativo nella consegna, ho scelto di non sottoscrivere un abbonamento e di documentare come potrebbe essere configurato.

#### Struttura dello space

Sarebbe necessario creare uno Space scegliendo Docker come SDK e caricare solo i file necessari per eseguire l'API:
- la cartella app
- i due file di requiremnts: `requirements-docker.txt` e `requirements-docker-torch-cpu.txt`
- il file docker `Dockerfile`

In modo che il deploy nello Space avrebbe riguardato solo il servizio delle API

#### Configurazione

Sarebbe corretto adattare il Dockerfile per avviare FastAPI sulla porta `7860`, essendo quella la  porta predefinita di Hugging Face Docker Spaces (anche se non è obbligatoria), e quindi poi addattare di conseguenza il Dockerfile:

```dockerfile
EXPOSE 7860

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
```

Dopo aver caricato i file nel repository dello space, Hugging Face costrusce l'immagine ed esegue il container

Eventuali token andrebbero configurati come Secret nelle impostazioni dello Space, evitando di inserirli nel codice o nel Dockerfile

#### Verifica del servizio
Una volta avviato lo Space, tramite l'indirizzo pubblico fornito da Hugging Face sarebbe possibile verificare:

- `/health`: per controllare che il servizio rispondesse.
- `/inference`: per inviare un testo e controllare la risposta del modello.

