from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from transformers import pipeline
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import logging
import time
from collections import deque
from typing import List, Dict

app = FastAPI(title="Sentiment Analysis Microservice")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter('sentiment_requests_total', 'Total sentiment analysis requests')
REQUEST_LATENCY = Histogram('sentiment_request_duration_seconds', 'Request duration in seconds')
SENTIMENT_POSITIVE = Counter('sentiment_positive_total', 'Total positive sentiments')
SENTIMENT_NEGATIVE = Counter('sentiment_negative_total', 'Total negative sentiments')
SENTIMENT_SCORE = Gauge('sentiment_score', 'Current sentiment score (-1 to 1)')

# Load the model globally so it only runs once when the server starts
print("Loading model... this might take a minute...")
classifier = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
print("Model loaded!")

# Store recent sentiment results for market signal calculation
sentiment_history = deque(maxlen=100)

# Data Model 
class SentimentRequest(BaseModel):
    text: str

class MarketSignal(BaseModel):
    signal: str  # "BULLISH", "BEARISH", "NEUTRAL"
    strength: float  # 0.0 to 1.0
    positive_ratio: float
    negative_ratio: float
    sample_size: int
    avg_confidence: float

# Endpoint
@app.post("/analyze")
async def analyze_sentiment(request: SentimentRequest):
    REQUEST_COUNT.inc()
    start_time = time.time()
    
    try:
        # Perform inference
        result = classifier(request.text)[0]
        
        # Update metrics
        if result["label"] == "POSITIVE":
            SENTIMENT_POSITIVE.inc()
        else:
            SENTIMENT_NEGATIVE.inc()
        
        # Store in history
        sentiment_history.append({
            "sentiment": result["label"],
            "confidence": result["score"],
            "timestamp": time.time()
        })
        
        # Update sentiment score gauge
        _update_sentiment_score()
        
        # Log the activity
        logger.info(f"Analyzed text: '{request.text[:30]}...' | Result: {result['label']}")
        
        # Track latency
        REQUEST_LATENCY.observe(time.time() - start_time)
        
        return {
            "sentiment": result["label"],
            "confidence": round(result["score"], 4)
        }
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail="Model inference failed")

def _update_sentiment_score():
    """Calculate and update the current sentiment score"""
    if not sentiment_history:
        return
    
    positive_count = sum(1 for s in sentiment_history if s["sentiment"] == "POSITIVE")
    total_count = len(sentiment_history)
    
    # Score from -1 (all negative) to +1 (all positive)
    score = (positive_count / total_count * 2) - 1
    SENTIMENT_SCORE.set(score)

@app.get("/market-signal")
async def get_market_signal() -> MarketSignal:
    """
    Aggregate recent sentiment data into actionable market signal.
    Returns BULLISH, BEARISH, or NEUTRAL based on sentiment trends.
    """
    if not sentiment_history:
        return MarketSignal(
            signal="NEUTRAL",
            strength=0.0,
            positive_ratio=0.0,
            negative_ratio=0.0,
            sample_size=0,
            avg_confidence=0.0
        )
    
    # Calculate statistics
    positive_count = sum(1 for s in sentiment_history if s["sentiment"] == "POSITIVE")
    negative_count = len(sentiment_history) - positive_count
    total_count = len(sentiment_history)
    
    positive_ratio = positive_count / total_count
    negative_ratio = negative_count / total_count
    avg_confidence = sum(s["confidence"] for s in sentiment_history) / total_count
    
    # Determine signal
    if positive_ratio > 0.6:
        signal = "BULLISH"
        strength = positive_ratio
    elif negative_ratio > 0.6:
        signal = "BEARISH"
        strength = negative_ratio
    else:
        signal = "NEUTRAL"
        strength = 1.0 - abs(positive_ratio - negative_ratio)
    
    logger.info(f"Market signal: {signal} (strength: {strength:.2f})")
    
    return MarketSignal(
        signal=signal,
        strength=round(strength, 4),
        positive_ratio=round(positive_ratio, 4),
        negative_ratio=round(negative_ratio, 4),
        sample_size=total_count,
        avg_confidence=round(avg_confidence, 4)
    )

@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest()

# Health Check
@app.get("/health")
def health_check():
    return {
        "status": "healthy", 
        "service": "sentiment-analyzer",
        "model_loaded": classifier is not None,
        "sentiment_history_size": len(sentiment_history)
    }
