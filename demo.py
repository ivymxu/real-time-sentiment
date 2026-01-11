#!/usr/bin/env python3
"""
Demo script showing how the sentiment analysis pipeline works.
This demonstrates the data flow without requiring actual Reddit API access.
"""

import json
from datetime import datetime

def simulate_sentiment_analysis(text):
    """Simulate sentiment analysis (would normally call the API)"""
    # Simple keyword-based simulation
    positive_keywords = ['love', 'great', 'amazing', 'excellent', 'bull', 'up', 'gain', 'profit', 'moon', '🚀']
    negative_keywords = ['hate', 'terrible', 'awful', 'bad', 'bear', 'down', 'loss', 'crash', 'dump']
    
    text_lower = text.lower()
    positive_count = sum(1 for word in positive_keywords if word in text_lower)
    negative_count = sum(1 for word in negative_keywords if word in text_lower)
    
    if positive_count > negative_count:
        return {"sentiment": "POSITIVE", "confidence": 0.85 + (positive_count * 0.05)}
    elif negative_count > positive_count:
        return {"sentiment": "NEGATIVE", "confidence": 0.85 + (negative_count * 0.05)}
    else:
        return {"sentiment": "POSITIVE" if len(text) % 2 == 0 else "NEGATIVE", "confidence": 0.60}

def calculate_market_signal(sentiments):
    """Calculate market signal from sentiment list"""
    if not sentiments:
        return {
            "signal": "NEUTRAL",
            "strength": 0.0,
            "positive_ratio": 0.0,
            "negative_ratio": 0.0,
            "sample_size": 0
        }
    
    positive_count = sum(1 for s in sentiments if s["sentiment"] == "POSITIVE")
    total_count = len(sentiments)
    
    positive_ratio = positive_count / total_count
    negative_ratio = 1 - positive_ratio
    
    if positive_ratio > 0.6:
        signal = "BULLISH"
        strength = positive_ratio
    elif negative_ratio > 0.6:
        signal = "BEARISH"
        strength = negative_ratio
    else:
        signal = "NEUTRAL"
        strength = 1.0 - abs(positive_ratio - negative_ratio)
    
    return {
        "signal": signal,
        "strength": round(strength, 4),
        "positive_ratio": round(positive_ratio, 4),
        "negative_ratio": round(negative_ratio, 4),
        "sample_size": total_count
    }

def main():
    """Demonstrate the pipeline flow"""
    print("=" * 80)
    print("Real-Time Sentiment Analysis Pipeline - Demo")
    print("=" * 80)
    print()
    
    # Simulate Reddit comments
    sample_comments = [
        "This stock is going to the moon! 🚀🚀🚀",
        "Great earnings report, bullish on this one!",
        "Terrible news, expecting a crash soon",
        "Love the fundamentals, buying more",
        "This is awful, selling everything",
        "Amazing company with strong growth",
        "Very bullish on tech stocks right now",
        "Market looks bearish, time to be careful",
        "Excellent quarter, profit margins up",
        "Stock is up 20% today, incredible gains!"
    ]
    
    print("STEP 1: Ingestion Service")
    print("-" * 80)
    print(f"Fetching {len(sample_comments)} comments from r/wallstreetbets (simulated)")
    print()
    
    print("STEP 2: Sentiment Analysis")
    print("-" * 80)
    sentiment_results = []
    
    for i, comment in enumerate(sample_comments, 1):
        sentiment = simulate_sentiment_analysis(comment)
        sentiment_results.append(sentiment)
        
        emoji = "📈" if sentiment["sentiment"] == "POSITIVE" else "📉"
        print(f"{i}. {emoji} [{sentiment['sentiment']:8s}] {sentiment['confidence']:.2f} | {comment[:60]}")
    
    print()
    print("STEP 3: Market Signal Aggregation")
    print("-" * 80)
    
    market_signal = calculate_market_signal(sentiment_results)
    
    # Display results
    signal_emoji = {
        "BULLISH": "🐂",
        "BEARISH": "🐻",
        "NEUTRAL": "⚖️"
    }
    
    print(f"\n📊 MARKET SIGNAL: {signal_emoji.get(market_signal['signal'], '')} {market_signal['signal']}")
    print(f"   Strength: {market_signal['strength']:.2%}")
    print(f"   Positive Ratio: {market_signal['positive_ratio']:.2%}")
    print(f"   Negative Ratio: {market_signal['negative_ratio']:.2%}")
    print(f"   Sample Size: {market_signal['sample_size']} comments")
    print()
    
    print("STEP 4: Prometheus Metrics (would be exposed at /metrics)")
    print("-" * 80)
    print(f"sentiment_requests_total: {len(sample_comments)}")
    print(f"sentiment_positive_total: {sum(1 for s in sentiment_results if s['sentiment'] == 'POSITIVE')}")
    print(f"sentiment_negative_total: {sum(1 for s in sentiment_results if s['sentiment'] == 'NEGATIVE')}")
    print(f"sentiment_score: {(market_signal['positive_ratio'] * 2) - 1:.2f} (range: -1 to +1)")
    print()
    
    print("=" * 80)
    print("Pipeline Demonstration Complete!")
    print("=" * 80)
    print()
    print("📝 Next Steps:")
    print("   1. Configure Reddit API credentials in .env file")
    print("   2. Run: docker-compose up --build")
    print("   3. Access API at http://localhost:8000")
    print("   4. View metrics at http://localhost:9090 (Prometheus)")
    print()

if __name__ == "__main__":
    main()
