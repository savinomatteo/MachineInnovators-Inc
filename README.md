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