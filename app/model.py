"""Caricamento e inferenza del modello"""

from transformers import pipeline

MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment-latest"


class SentimentClassifier:
    def __init__(self) -> None:
        """Carico il modello una volta sola all'avvio"""
        self.pipe = pipeline(
            "sentiment-analysis",
            model=MODEL_NAME,
            tokenizer=MODEL_NAME,
        )

    def predict(self, text: str) -> dict:
        """Restituisce label e confidenza dato un testo in input"""
        if not isinstance(text, str):
            raise TypeError("text deve essere una stringa")

        if not text.strip():
            raise ValueError("text non può essere vuoto")

        result = self.pipe(text)[0]

        return {
            "text": text,
            "label": result["label"].lower(),
            "confidence": float(result["score"]),
        }


classifier = SentimentClassifier()
