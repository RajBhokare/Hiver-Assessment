"""Main Hiver Agent Orchestrator.

Pipeline:
Customer message -> Intent Classification -> Historical Retrieval -> Grounded Generation -> Escalation Decision -> AgentDecision
"""
from pathlib import Path
from typing import Optional, Union, Dict, Any
import pandas as pd
from hiver_agent.schema import AgentDecision
from hiver_agent.baselines.tfidf_logistic import TFIDFLogisticBaseline
from hiver_agent.retrieval.historical_store import HistoricalResponseRetriever
from hiver_agent.generation.grounded_generator import GroundedResponseGenerator
from src.data.labeler import apply_labels
from src.utils.logger import get_logger

logger = get_logger("hiver_agent")


class HiverAgent:
    """Production-grade customer support AI agent for AppleSupport."""

    def __init__(
        self,
        classifier: Optional[TFIDFLogisticBaseline] = None,
        retriever: Optional[HistoricalResponseRetriever] = None,
        generator: Optional[GroundedResponseGenerator] = None,
    ):
        self.classifier = classifier or TFIDFLogisticBaseline()
        self.retriever = retriever or HistoricalResponseRetriever()
        self.generator = generator or GroundedResponseGenerator()

    @classmethod
    def load_or_train(
        cls,
        train_path: Union[str, Path] = "data/splits/train.csv",
        model_dir: Union[str, Path] = "artifacts/models",
    ) -> "HiverAgent":
        """Load pretrained models or train directly on the training split."""
        model_dir = Path(model_dir)
        model_dir.mkdir(parents=True, exist_ok=True)
        
        clf_path = model_dir / "tfidf_logistic_intent.pkl"
        retriever_path = model_dir / "retrieval_index.pkl"

        classifier = TFIDFLogisticBaseline()
        retriever = HistoricalResponseRetriever()

        # Check if saved artifacts exist
        if clf_path.exists() and retriever_path.exists():
            logger.info("Loading serialized classifier and retrieval index...")
            classifier.load(clf_path)
            retriever.load(retriever_path)
        else:
            logger.info(f"Building models from training split at {train_path}...")
            train_file = Path(train_path)
            if not train_file.exists():
                raise FileNotFoundError(f"Training split not found at {train_file.resolve()}. Run 'make prepare' first.")

            df_train = pd.read_csv(train_file)
            df_train_labeled = apply_labels(df_train, text_col="clean_customer_text")

            texts = df_train_labeled["clean_customer_text"].fillna("").tolist()
            labels = df_train_labeled["intent"].tolist()
            responses = df_train_labeled["clean_apple_text"].fillna("").tolist()

            # Train classifier
            logger.info(f"Fitting TF-IDF Logistic Regression on {len(texts):,} training samples...")
            classifier.fit(texts, labels)
            classifier.save(clf_path)

            # Build retrieval index
            logger.info("Building historical response retrieval index...")
            retriever.build_index(customer_texts=texts, apple_responses=responses)
            retriever.save(retriever_path)

        generator = GroundedResponseGenerator()
        return cls(classifier=classifier, retriever=retriever, generator=generator)

    def respond(self, message: str, top_k_evidence: int = 3) -> AgentDecision:
        """Run the full end-to-end agent pipeline for an incoming customer message."""
        # Clean text
        clean_msg = message.strip()

        # Step 1: Predict Intent & Confidence
        predicted_intent, confidence = self.classifier.predict_with_confidence(clean_msg)

        # Step 2: Retrieve Top-k Historical Evidence
        evidence = self.retriever.retrieve(query=clean_msg, top_k=top_k_evidence)

        # Step 3: Grounded Response Generation & Escalation Analysis
        decision = self.generator.process(
            customer_message=clean_msg,
            predicted_intent=predicted_intent,
            intent_confidence=confidence,
            evidence=evidence,
        )

        return decision
