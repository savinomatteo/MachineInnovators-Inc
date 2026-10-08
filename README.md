# MachineInnovators-Inc
 Pipeline MLOps per il monitoraggio del sentiment sui social


## Avvio del progetto

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

Il file `Dockerfile` definisce l'immagine dell'applicazione usando Python 3.14-slim.

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

Nel `docker-compose.yml` ho dovuto mettere:

```text
network_mode: host
```

perchè l'installazione automatica di Infinity falliva perché la rete Docker Compose monitoring_default non riusciva a raggiungere grafana.com. Con 'network_mode: host' non bisogna usare il parametro ports, ma Grafana sarà disponibile direttamente sulla porta predefinita 3000. Se dopo aver fatto `compose-up` non è stata aggiunta nella liste delle porte la porta 3000, basta fara `Aggiungi porta` e mettere la 3000 e il servizio di Grafana sarà disponibile.

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
