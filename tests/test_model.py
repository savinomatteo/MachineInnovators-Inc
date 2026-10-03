"""Test automatici del modello"""

from app.model import classifier


def test_positive_text():
    """Verifica la classificazione di un testo chiaramente positivo"""
    result = classifier.predict("love")
    assert result["label"] == "positive"
    assert 0 <= result["confidence"] <= 1


def test_negative_text():
    """Verifica la classificazione di un testo chiaramente negativo"""
    result = classifier.predict("useless.")
    assert result["label"] == "negative"
    assert 0 <= result["confidence"] <= 1
