from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import pipeline
import logging

app = FastAPI(title="Sentiment Analysis Microservice")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load the model globally so it only runs once when the server starts
print("Loading model... this might take a minute...")
classifier = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
print("Model loaded!")

# Data Model 
class SentimentRequest(BaseModel):
    text: str

# Endpoint
@app.post("/analyze")
async def analyze_sentiment(request: SentimentRequest):
    try:
        # Perform inference
        result = classifier(request.text)[0]
        
        # Log the activity
        logger.info(f"Analyzed text: '{request.text[:30]}...' | Result: {result['label']}")
        
        return {
            "sentiment": result["label"],
            "confidence": round(result["score"], 4)
        }
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail="Model inference failed")

# Health Check
@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "sentiment-analyzer"}
