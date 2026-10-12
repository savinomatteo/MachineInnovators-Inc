"""DAG per valutare il modello e decidere un eventuale retraining"""

import csv
import json
import os
from datetime import datetime
from pathlib import Path
import requests
from airflow import DAG
from airflow.decorators import task
from airflow.operators.empty import EmptyOperator
from sklearn.metrics import accuracy_score, f1_score


DATASET_PATH = "/opt/airflow/data/sentiment_evaluation.csv"
REPORT_PATH = "/opt/airflow/data/latest_evaluation_report.json"
API_URL = os.getenv(
    "API_URL",
    "http://mlops-api:8000",
)
MIN_MACRO_F1 = 0.70


with DAG(
    dag_id="evaluate_model_retraining",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    schedule="0 6 * * *"
) as dag:

    inizio = EmptyOperator(task_id="inizio")

    @task()
    def load_evaluation_dataset():
        """Legge dati reali dal CSV"""
        dataset_file = Path(DATASET_PATH)

        if not dataset_file.exists():
            raise FileNotFoundError(
                f"Dataset non trovato: {dataset_file}"
            )

        with dataset_file.open("r", encoding="utf-8", newline="") as file:
            rows = list(csv.DictReader(file))

        if not rows:
            raise ValueError("Il dataset è vuoto")

        required_columns = {"text", "label"}
        if not required_columns.issubset(rows[0]):
            raise ValueError("Il CSV deve avere le colonne text,label")

        valid_labels = {"positive", "neutral", "negative"}

        for row in rows:
            row["text"] = row["text"].strip()
            row["label"] = row["label"].strip().lower()

            if not row["text"]:
                raise ValueError("Trovato testo vuoto nel dataset")
            if row["label"] not in valid_labels:
                raise ValueError(f"Label non valida: {row['label']}")

        print(f"Dataset caricato: {len(rows)} record")
        return rows

    @task()
    def evaluate_api(dataset_rows):
        """Chiama davvero l'endpoint FastAPI e calcola le metriche"""
        true_labels = []
        predicted_labels = []
        confidences = []

        for row in dataset_rows:
            response = requests.post(
                f"{API_URL}/inference",
                json={"text": row["text"]},
                timeout=60,
            )
            response.raise_for_status()

            prediction = response.json()

            true_labels.append(row["label"])
            predicted_labels.append(prediction["label"])
            confidences.append(prediction["confidence"])

        accuracy = accuracy_score(true_labels, predicted_labels)
        macro_f1 = f1_score(
            true_labels,
            predicted_labels,
            labels=["negative", "neutral", "positive"],
            average="macro",
            zero_division=0,
        )

        report = {
            "api_url": API_URL,
            "records_evaluated": len(dataset_rows),
            "accuracy": round(float(accuracy), 4),
            "macro_f1": round(float(macro_f1), 4),
            "avg_confidence": round((sum(confidences) / len(confidences)),4,),
            "minimum_macro_f1": MIN_MACRO_F1,
            "evaluated_at_utc": datetime.utcnow().isoformat(),
        }

        Path(REPORT_PATH).write_text(
            json.dumps(report, indent=2),
            encoding="utf-8",
        )

        print(json.dumps(report, indent=2))
        return report

    @task.branch()
    def check_model_quality(evaluation_result):
        """Decide se la qualità richiede il retraining"""
        if evaluation_result["macro_f1"] < evaluation_result["minimum_macro_f1"]:
            return "retrain_model"

        return "no_retraining_needed"

    @task(task_id="retrain_model")
    def retrain_model(evaluation_result):
        """Flusso richiesta di retraining"""
        print("Retraining richiesto: macro-F1 sotto soglia")
        print(f"Macro-F1: {evaluation_result['macro_f1']}")
        print(f"Soglia: {evaluation_result['minimum_macro_f1']}")
        print("In produzione qui partirebbe un job di fine-tuning.")

    @task(task_id="no_retraining_needed")
    def no_retraining_needed(evaluation_result):
        """Flusso per le prestazioni del modello sono ancora accettabili"""
        print("Modello approvato: retraining non necessario")
        print(f"Macro-F1: {evaluation_result['macro_f1']}")
        print(f"Soglia: {evaluation_result['minimum_macro_f1']}")

    dataset_task = load_evaluation_dataset()
    evaluation_task = evaluate_api(dataset_task)
    quality_check_task = check_model_quality(evaluation_task)

    retrain_task = retrain_model(evaluation_task)
    no_retraining_task = no_retraining_needed(evaluation_task)

    (
        inizio
        >> dataset_task
        >> evaluation_task
        >> quality_check_task
        >> [retrain_task, no_retraining_task]
    )