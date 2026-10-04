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
requirements-torch-cpu.txt
```

Contenuto:

```text
--index-url [https://download.pytorch.org/whl/cpu](https://download.pytorch.org/whl/cpu)
torch
```

In modo da poter specificare di scaricare la versione CPU-only.

Questa separazione evita che vengano installate dipendenze di Pytorch non necessarie per questo servizio. Ho dovuto farlo perchè altrimenti CodeSpace nonostante avessi creato la versione con più risorse andava in difficoltà quando provavo a fare docker build.

```text
fastapi
uvicorn[standard]
transformers
```

Nel Dockerfile le dipendenze vengono installate in due passaggi:

```dockerfile
RUN pip install --no-cache-dir -r requirements-docker.txt \
    && pip install --no-cache-dir -r requirements-torch-cpu.txt
```

### 7. Grafana

Dopo aver configurato il file `monitoring/docker-compose.yml`, per farlo partire lanciare il comando:

```bash
docker compose -f 'monitoring/docker-compose.yml' up -d --build 
```

Nel `docker-compose.yml` ho dovuto mettere:

```text
network_mode: host
```

perchè l'installazione automatica di Infinity falliva perché la rete Docker Compose monitoring_default non riusciva a raggiungere grafana.com. Con 'network_mode: host' non bisogna usare il parametro ports, ma Grafana sarà disponibile direttamente sulla porta predefinita 3000:





