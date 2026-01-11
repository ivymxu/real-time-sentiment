import os
import time
import logging
import asyncio
from typing import List, Dict, Optional
import praw
from dotenv import load_dotenv
import httpx

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration constants
MAX_TEXT_LENGTH = int(os.getenv("MAX_TEXT_LENGTH", "512"))
SENTIMENT_BUFFER_SIZE = int(os.getenv("SENTIMENT_BUFFER_SIZE", "1000"))


class RedditStreamIngestion:
    """Service to ingest Reddit comments and send them for sentiment analysis"""
    
    def __init__(self):
        # Reddit API credentials from environment
        self.reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID", "demo_client"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET", "demo_secret"),
            user_agent=os.getenv("REDDIT_USER_AGENT", "sentiment-analyzer/1.0"),
            username=os.getenv("REDDIT_USERNAME"),
            password=os.getenv("REDDIT_PASSWORD")
        )
        
        self.sentiment_api_url = os.getenv("SENTIMENT_API_URL", "http://localhost:8000")
        self.subreddit_name = os.getenv("SUBREDDIT", "wallstreetbets")
        self.batch_size = int(os.getenv("BATCH_SIZE", "10"))
        self.poll_interval = int(os.getenv("POLL_INTERVAL", "60"))
        
        self.sentiment_buffer: List[Dict] = []
        
    async def analyze_text(self, text: str) -> Optional[Dict]:
        """Send text to sentiment analysis API"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.sentiment_api_url}/analyze",
                    json={"text": text[:MAX_TEXT_LENGTH]}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return None
    
    async def process_comment(self, comment) -> Optional[Dict]:
        """Process a single Reddit comment"""
        try:
            # Get sentiment
            sentiment_result = await self.analyze_text(comment.body)
            
            if sentiment_result:
                return {
                    "comment_id": comment.id,
                    "text": comment.body[:100],  # Store truncated version
                    "author": str(comment.author),
                    "created_utc": comment.created_utc,
                    "score": comment.score,
                    "sentiment": sentiment_result["sentiment"],
                    "confidence": sentiment_result["confidence"]
                }
        except Exception as e:
            logger.error(f"Error processing comment: {e}")
            return None
    
    async def fetch_and_analyze_batch(self) -> List[Dict]:
        """Fetch a batch of comments and analyze them"""
        logger.info(f"Fetching comments from r/{self.subreddit_name}...")
        
        try:
            subreddit = self.reddit.subreddit(self.subreddit_name)
            comments = list(subreddit.comments(limit=self.batch_size))
            
            results = []
            for comment in comments:
                result = await self.process_comment(comment)
                if result:
                    results.append(result)
                    logger.info(f"Processed comment: {result['sentiment']} ({result['confidence']:.2f})")
            
            return results
            
        except Exception as e:
            logger.error(f"Error fetching comments: {e}")
            return []
    
    async def run_continuous(self):
        """Continuously poll Reddit and analyze sentiment"""
        logger.info("Starting Reddit ingestion service...")
        logger.info(f"Monitoring r/{self.subreddit_name}")
        logger.info(f"Poll interval: {self.poll_interval}s, Batch size: {self.batch_size}")
        
        # Check if sentiment service is available
        try:
            async with httpx.AsyncClient() as client:
                health_response = await client.get(f"{self.sentiment_api_url}/health")
                logger.info(f"Sentiment service health: {health_response.json()}")
        except Exception as e:
            logger.warning(f"Could not reach sentiment service: {e}")
        
        iteration = 0
        while True:
            iteration += 1
            logger.info(f"\n--- Iteration {iteration} ---")
            
            # Fetch and analyze batch
            results = await self.fetch_and_analyze_batch()
            
            if results:
                self.sentiment_buffer.extend(results)
                
                # Keep buffer size manageable
                if len(self.sentiment_buffer) > SENTIMENT_BUFFER_SIZE:
                    self.sentiment_buffer = self.sentiment_buffer[-SENTIMENT_BUFFER_SIZE:]
                
                logger.info(f"Buffer size: {len(self.sentiment_buffer)} items")
                
                # Calculate aggregate sentiment
                positive = sum(1 for r in results if r["sentiment"] == "POSITIVE")
                negative = sum(1 for r in results if r["sentiment"] == "NEGATIVE")
                avg_confidence = sum(r["confidence"] for r in results) / len(results) if results else 0
                
                logger.info(f"Batch sentiment: {positive} positive, {negative} negative, avg confidence: {avg_confidence:.2f}")
            
            # Wait before next poll
            logger.info(f"Waiting {self.poll_interval}s before next poll...")
            await asyncio.sleep(self.poll_interval)


async def main():
    """Main entry point for ingestion service"""
    ingestion = RedditStreamIngestion()
    await ingestion.run_continuous()


if __name__ == "__main__":
    asyncio.run(main())
