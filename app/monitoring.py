"""Raccolta delle metriche del servizio e storico per Grafana"""

import asyncio
import json
import logging
import os
import threading
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

HISTORY_FILE = os.getenv("MONITORING_HISTORY_FILE", "data/monitoring_history.json")

# Ogni quanti secondi l'app salva uno snapshot nello storico
SNAPSHOT_INTERVAL_S = float(os.getenv("MONITORING_SNAPSHOT_INTERVAL_S", "30"))

# Numero max di snapsot tenuti nel file (2880 sarebbero uno ogni 30 secondi in 24 ore)
HISTORY_MAX_ITEMS = int(os.getenv("MONITORING_HISTORY_MAX_ITEMS", "2880"))

LABELS = ("positive", "neutral", "negative")

_lock = threading.Lock()


def _empty_counters():
    """Restituisco i contatori azzerati"""
    return {
        "requests": 0,
        "client_errors": 0,
        "server_errors": 0,
        "latency_total_ms": 0.0,
        "latency_max_ms": 0.0,
        "text_length_total": 0,
        "confidence_total": 0.0,
        **{label: 0 for label in LABELS},
    }


# Contatori dall'avvio del servizio e contatori dell'intervallo corrente,
# che vengono azzerati a ogni snapshot
_totals = _empty_counters()
_window = _empty_counters()
_window_start = datetime.now(timezone.utc)


def _update(key, value):
    """Somma un valore allo stesso contatore dei totali e dell'intervallo"""
    _totals[key] += value
    _window[key] += value


def record_request(status_code, latency_ms):
    """Registra una richiesta con il suo esito e il tempo di risposta"""
    with _lock:
        _update("requests", 1)
        _update("latency_total_ms", latency_ms)

        for counters in (_totals, _window):
            counters["latency_max_ms"] = max(counters["latency_max_ms"], latency_ms)

        if status_code >= 500:
            _update("server_errors", 1)
        elif status_code >= 400:
            _update("client_errors", 1)


def record_prediction(sentiment, confidence):
    """Registra la classe predetta e la confidenza del modello"""
    sentiment = sentiment.strip().lower()

    with _lock:
        if sentiment in LABELS:
            _update(sentiment, 1)
        _update("confidence_total", confidence)


def record_text(text):
    """Registra la lunghezza del testo ricevuto"""
    with _lock:
        _update("text_length_total", len(text))


def _ratio(numerator, denominator, digits=4):
    """Divisione che restituisce None se il denominatore e' 0. 
    Fatto per fare in modo che Grafana mostri un buco
    invece di uno 0 che sembrerebbe un valore reale"""
    return round(numerator / denominator, digits) if denominator else None


def build_stats(counters):
    """Calcola le metriche aggregate a partire dai contatori"""
    requests = counters["requests"]
    predictions = sum(counters[label] for label in LABELS)

    stats = {
        "requests": requests,
        "client_errors": counters["client_errors"],
        "server_errors": counters["server_errors"],
        "error_rate": _ratio(counters["server_errors"], requests),
        "client_error_rate": _ratio(counters["client_errors"], requests),
        "avg_latency_ms": _ratio(counters["latency_total_ms"], requests, 2),
        "max_latency_ms": round(counters["latency_max_ms"], 2),
        "predictions": predictions,
        "avg_text_length": _ratio(counters["text_length_total"], predictions, 2),
        "avg_confidence": _ratio(counters["confidence_total"], predictions),
    }

    for label in LABELS:
        stats[f"{label}_predictions"] = counters[label]
        stats[f"{label}_rate"] = _ratio(counters[label], predictions)

    return stats


def get_summary():
    """Restituisce le metriche aggregate dall'avvio del servizio"""
    with _lock:
        return build_stats(_totals)


def read_history():
    """Legge lo storico dal file, lista vuota se non esiste ancora"""
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        logger.warning("Storico %s non leggibile, riparto da zero", HISTORY_FILE)
        return []


def write_history(history):
    """Scrive lo storico su un file temporaneo e poi lo sostituisce,
    cosi' Grafana non legge mai un file scritto a meta'"""
    folder = os.path.dirname(HISTORY_FILE)
    if folder:
        os.makedirs(folder, exist_ok=True)

    tmp_file = f"{HISTORY_FILE}.tmp"
    with open(tmp_file, "w", encoding="utf-8") as file:
        json.dump(history, file, indent=2)
    os.replace(tmp_file, HISTORY_FILE)


def save_snapshot():
    """Salva nello storico le metriche dell'ultimo intervallo e lo azzera"""
    global _window_start  # pylint: disable=global-statement

    now = datetime.now(timezone.utc)

    with _lock:
        snapshot = build_stats(_window)
        snapshot["timestamp"] = now.isoformat()
        snapshot["window_seconds"] = round((now - _window_start).total_seconds(), 1)

        history = read_history()
        history.append(snapshot)
        write_history(history[-HISTORY_MAX_ITEMS:])

        _window.update(_empty_counters())
        _window_start = now

    return snapshot


def get_history(minutes=None):
    """Restituisce lo storico, eventualmente solo gli ultimi N minuti"""
    with _lock:
        history = read_history()

    if minutes is None:
        return history

    since = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    return [item for item in history if _parse_timestamp(item) >= since]


def _parse_timestamp(item):
    """Legge il timestamp di uno snapshot, considerando UTC quelli senza fuso"""
    timestamp = datetime.fromisoformat(item["timestamp"])
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    return timestamp


async def snapshot_loop(interval_s=SNAPSHOT_INTERVAL_S):
    """Salva uno snapshot a intervalli regolari finche' l'app e' attiva"""
    while True:
        await asyncio.sleep(interval_s)
        try:
            await asyncio.to_thread(save_snapshot)
        except OSError:
            logger.exception("Impossibile salvare lo snapshot delle metriche")
