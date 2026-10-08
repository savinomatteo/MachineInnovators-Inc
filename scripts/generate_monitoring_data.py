"""Questo script genera dati di esempio per avere dei dati in Grafana"""

import argparse
import random
import time
import requests

BASE_URL = "http://localhost:8000"

POSITIVE_MESSAGES = [
    "Amazing service and excellent support!",
    "I love this new feature!",
    "Great product, I am very satisfied.",
]
NEUTRAL_MESSAGES = [
    "The update is available today.",
    "The package arrived this morning.",
]
NEGATIVE_MESSAGES = [
    "This product is useless and disappointing.",
    "The application crashes every time I open it.",
    "The app is slow and unreliable.",
    "I hate this service.",
]

# Probabilita' di scegliere un messaggio negativo nei due scenari:
# "negative" simula un cambio di sentiment per far azionare l'alert
NEGATIVE_RATIO = {"normal": 0.3, "negative": 0.8}


def pick_message(scenario):
    """Sceglie un messaggio in base allo scenario richiesto"""
    if random.random() < NEGATIVE_RATIO[scenario]:
        return random.choice(NEGATIVE_MESSAGES)
    return random.choice(POSITIVE_MESSAGES + NEUTRAL_MESSAGES)


def send_inference(text):
    """Invia un testo all'endpoint di inferenza e restituisce la risposta"""
    response = requests.post(
        f"{BASE_URL}/inference",
        json={"text": text},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def parse_args():
    """Legge i parametri da riga di comando"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scenario",
        choices=sorted(NEGATIVE_RATIO),
        default="normal",
        help="normal: traffico misto, negative: prevalenza di commenti negativi",
    )
    parser.add_argument("--min-wait", type=float, default=1, help="secondi minimi")
    parser.add_argument("--max-wait", type=float, default=5, help="secondi masimi")
    return parser.parse_args()


def main():
    """Invia richieste a intervalli casuali fino a ctrl+C"""
    args = parse_args()

    print(f"Generazione continua dei dati avviata (scenario: {args.scenario}).")
    print("Premi Ctrl+C per interrompere.\n")

    try:
        while True:
            text = pick_message(args.scenario)

            print(f"Testo:{text}")

            try:
                result = send_inference(text)
                print(
                    f"Label: {result['label']} "
                    f"(confidence: {result['confidence']:.3f})"
                )
            except requests.RequestException as exc:
                print(f"Richiesta fallita: {exc}")

            wait_seconds = random.uniform(args.min_wait, args.max_wait)
            print(f"Attendo {wait_seconds:.1f} secondi..\n")

            time.sleep(wait_seconds)

    except KeyboardInterrupt:
        print("\nGenerazione interrotta dall'utente")


if __name__ == "__main__":
    main()
