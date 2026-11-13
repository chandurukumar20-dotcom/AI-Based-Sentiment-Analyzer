import re
import logging
from typing import Dict, List, Any
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.corpus import stopwords
from config import Config

logger = logging.getLogger(__name__)

# Ensure required NLTK resources are available
for pkg in ["vader_lexicon", "punkt", "stopwords"]:
    try:
        nltk.download(pkg, quiet=True)
    except Exception as e:
        logger.warning(f"Could not download NLTK package {pkg}: {e}")


class SentimentAnalyzer:
    """
    AI-driven Sentiment Analysis engine supporting Hugging Face Transformers
    and NLTK VADER with robust multi-class (Positive, Negative, Neutral) classification.
    """

    def __init__(self, model_name: str = None, use_transformers: bool = None):
        self.model_name = model_name or Config.MODEL_NAME
        self.use_transformers = (
            use_transformers if use_transformers is not None else Config.USE_TRANSFORMERS
        )
        self.engine_name = "NLTK VADER (Rule-based & Lexicon NLP)"
        self.hf_pipeline = None
        self.vader_analyzer = None

        # Initialize NLTK VADER analyzer
        try:
            self.vader_analyzer = SentimentIntensityAnalyzer()
        except Exception as e:
            logger.error(f"Failed to initialize VADER: {e}")

        # Attempt to load Hugging Face pipeline if requested
        if self.use_transformers:
            self._init_hf_pipeline()

        # Stopwords set for token inspection
        try:
            self.stop_words = set(stopwords.words("english"))
        except Exception:
            self.stop_words = set()

    def _init_hf_pipeline(self):
        """Attempts to load pre-trained Hugging Face transformer model."""
        try:
            from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer
            logger.info(f"Loading Hugging Face model: {self.model_name}...")
            self.hf_pipeline = pipeline(
                "sentiment-analysis",
                model=self.model_name,
                tokenizer=self.model_name,
                top_k=None
            )
            self.engine_name = f"Hugging Face ({self.model_name})"
            logger.info("Hugging Face model loaded successfully!")
        except Exception as exc:
            logger.warning(
                f"Could not load Hugging Face transformer model ({exc}). "
                f"Falling back smoothly to NLTK VADER analyzer."
            )
            self.hf_pipeline = None
            self.engine_name = "NLTK VADER (Lexicon & Heuristics NLP)"

    def preprocess_text(self, text: str) -> Dict[str, Any]:
        """
        Cleans and preprocesses input text:
        - Removes HTML tags and URLs
        - Standardizes whitespace
        - Extracts word count and key tokens
        """
        if not text or not isinstance(text, str):
            return {
                "cleaned": "",
                "original": text or "",
                "word_count": 0,
                "char_count": 0,
                "tokens": [],
                "key_words": []
            }

        original = text
        # Remove URLs
        cleaned = re.sub(r"https?://\S+|www\.\S+", "", text)
        # Remove HTML tags
        cleaned = re.sub(r"<.*?>", "", cleaned)
        # Standardize whitespace
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        # Tokenize words
        words = re.findall(r"\b[A-Za-z0-9'-]+\b", cleaned)
        key_words = [
            w for w in words
            if len(w) > 2 and w.lower() not in self.stop_words
        ]

        return {
            "original": original,
            "cleaned": cleaned if cleaned else original,
            "word_count": len(words),
            "char_count": len(cleaned),
            "tokens": words,
            "key_words": key_words[:10]  # top keywords for visualization
        }

    def _analyze_with_hf(self, text: str) -> Dict[str, Any]:
        """Runs inference with Hugging Face transformer pipeline."""
        outputs = self.hf_pipeline(text)
        # Handle format: [{'label': 'positive', 'score': 0.98}, ...]
        if isinstance(outputs, list) and len(outputs) > 0:
            if isinstance(outputs[0], list):
                scores_list = outputs[0]
            else:
                scores_list = outputs
        else:
            scores_list = []

        label_map = {
            "positive": "Positive",
            "pos": "Positive",
            "label_2": "Positive",
            "5 stars": "Positive",
            "4 stars": "Positive",
            "negative": "Negative",
            "neg": "Negative",
            "label_0": "Negative",
            "1 star": "Negative",
            "2 stars": "Negative",
            "neutral": "Neutral",
            "neu": "Neutral",
            "label_1": "Neutral",
            "3 stars": "Neutral"
        }

        best_label = "Neutral"
        best_score = 0.0
        scores_dict = {"positive": 0.0, "negative": 0.0, "neutral": 0.0}

        for item in scores_list:
            raw_label = str(item.get("label", "")).lower()
            score = float(item.get("score", 0.0))
            mapped = label_map.get(raw_label, "Neutral")
            if mapped.lower() in scores_dict:
                scores_dict[mapped.lower()] += score
            if score > best_score:
                best_score = score
                best_label = mapped

        confidence_pct = round(best_score * 100, 2)

        return {
            "sentiment": best_label,
            "confidence": confidence_pct,
            "compound": round(scores_dict["positive"] - scores_dict["negative"], 4),
            "scores": {
                "positive": round(scores_dict["positive"] * 100, 1),
                "negative": round(scores_dict["negative"] * 100, 1),
                "neutral": round(scores_dict["neutral"] * 100, 1)
            },
            "engine": f"Hugging Face Transformers ({self.model_name})"
        }

    def _analyze_with_vader(self, text: str) -> Dict[str, Any]:
        """Runs sentiment classification using NLTK VADER."""
        if not self.vader_analyzer:
            self.vader_analyzer = SentimentIntensityAnalyzer()

        scores = self.vader_analyzer.polarity_scores(text)
        compound = scores["compound"]
        pos = scores["pos"]
        neg = scores["neg"]
        neu = scores["neu"]

        # Classification rules:
        # compound >= 0.05 -> Positive
        # compound <= -0.05 -> Negative
        # otherwise -> Neutral
        if compound >= 0.05:
            sentiment = "Positive"
            # Calibrated confidence calculation
            confidence = min(99.0, max(55.0, (0.50 + abs(compound) * 0.48) * 100))
        elif compound <= -0.05:
            sentiment = "Negative"
            confidence = min(99.0, max(55.0, (0.50 + abs(compound) * 0.48) * 100))
        else:
            sentiment = "Neutral"
            confidence = min(98.0, max(60.0, (neu * 0.85 + (1.0 - abs(compound)) * 0.15) * 100))

        return {
            "sentiment": sentiment,
            "confidence": round(confidence, 2),
            "compound": round(compound, 4),
            "scores": {
                "positive": round(pos * 100, 1),
                "negative": round(neg * 100, 1),
                "neutral": round(neu * 100, 1)
            },
            "engine": "NLTK VADER Sentiment Engine"
        }

    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Analyzes a single piece of text and returns a rich classification dictionary.
        """
        if not text or not text.strip():
            return {
                "text": text,
                "sentiment": "Neutral",
                "confidence": 0.0,
                "compound": 0.0,
                "scores": {"positive": 0.0, "negative": 0.0, "neutral": 100.0},
                "preprocessing": self.preprocess_text(""),
                "engine": self.engine_name
            }

        prep = self.preprocess_text(text)
        target_text = prep["cleaned"] or text

        # Use HF if loaded, otherwise VADER
        if self.hf_pipeline is not None:
            try:
                res = self._analyze_with_hf(target_text)
            except Exception as e:
                logger.warning(f"Inference error in Hugging Face: {e}. Using VADER.")
                res = self._analyze_with_vader(target_text)
        else:
            res = self._analyze_with_vader(target_text)

        # Merge with preprocessing stats
        res["text"] = text
        res["preprocessing"] = prep
        return res

    def analyze_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Analyzes a list of text strings."""
        return [self.analyze_text(t) for t in texts]


# Global analyzer singleton
_analyzer_instance = None


def get_analyzer() -> SentimentAnalyzer:
    """Returns singleton instance of SentimentAnalyzer."""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = SentimentAnalyzer()
    return _analyzer_instance
