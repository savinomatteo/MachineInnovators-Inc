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

#### Nota

Il primo avvio del container può richiedere più tempo perché il modello e il 
tokenizer vengono scaricati da Hugging Face

Il container richiede spazio disco sufficiente per installare tutte le dipendenze,
in particolare pytorch che occupa molto spazio