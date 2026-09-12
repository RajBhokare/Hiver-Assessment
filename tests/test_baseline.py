"""Smoke tests for baseline model training and prediction pipeline."""
from src.models.baseline import BaselineClassifier


def test_baseline_fit_and_predict(tmp_path):
    train_texts = [
        "Need help with refund and billing invoice",
        "How to get my invoice statement",
        "System crashed error 500 internal bug",
        "Error in application service",
    ]
    train_labels = ["billing", "billing", "technical", "technical"]

    model = BaselineClassifier(max_features=100)
    model.fit(train_texts, train_labels)

    # Test prediction
    test_texts = ["invoice question", "app error bug"]
    preds = model.predict(test_texts)
    assert len(preds) == 2
    assert preds[0] == "billing"
    assert preds[1] == "technical"

    # Test save and reload
    save_file = tmp_path / "model.pkl"
    model.save(save_file)
    assert save_file.exists()

    loaded_model = BaselineClassifier()
    loaded_model.load(save_file)
    loaded_preds = loaded_model.predict(test_texts)
    assert loaded_preds.tolist() == preds.tolist()
