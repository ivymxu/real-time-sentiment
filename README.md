# Real-Time Sentiment Analysis Pipeline

### Rationale
As a doom-scroller with FOMO but is also deeply interested in Machine Learning, DevOps, and SRE, I wanted to explore something that blends all of these concepts using an interesting live data source.

### Overview
This project is a fully functional microservice that converts noisy social media streams into actionable market signals. It ingests live Reddit comments, analyzes sentiment using a machine learning model, and exposes metrics and market signals via a REST API.

### Architecture Overview
- **Ingestion Service**: Python script that continuously polls Reddit API for live comments
- **ML Service**: FastAPI wrapper around a Hugging Face Transformer (DistilBERT) for sentiment analysis
- **Market Signal Aggregation**: Real-time calculation of market sentiment signals (BULLISH/BEARISH/NEUTRAL)
- **Infrastructure**: Dockerized containers orchestrated via docker-compose
- **Monitoring**: Prometheus metrics exposed by the API to track request latency and sentiment distribution

### Features
✅ **Live Data Ingestion**: Continuously streams Reddit comments from configurable subreddits  
✅ **Sentiment Analysis**: Uses state-of-the-art NLP model for accurate sentiment classification  
✅ **Market Signals**: Aggregates sentiment data into actionable BULLISH/BEARISH/NEUTRAL signals  
✅ **Prometheus Metrics**: Exposes metrics for monitoring and alerting  
✅ **Docker Support**: Fully containerized with docker-compose orchestration  
✅ **Health Checks**: Built-in health endpoints for service monitoring  
✅ **Configurable**: Environment-based configuration for flexibility  

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Reddit API credentials (get them from https://www.reddit.com/prefs/apps)

### Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd real-time-sentiment
```

2. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your Reddit API credentials
```

3. **Start the services**
```bash
docker-compose up --build
```

The services will be available at:
- Sentiment API: http://localhost:8000
- Prometheus: http://localhost:9090

### API Endpoints

#### 1. Analyze Sentiment
```bash
POST /analyze
Content-Type: application/json

{
  "text": "This stock is going to the moon! 🚀"
}
```

Response:
```json
{
  "sentiment": "POSITIVE",
  "confidence": 0.9998
}
```

#### 2. Get Market Signal
```bash
GET /market-signal
```

Response:
```json
{
  "signal": "BULLISH",
  "strength": 0.75,
  "positive_ratio": 0.75,
  "negative_ratio": 0.25,
  "sample_size": 100,
  "avg_confidence": 0.94
}
```

#### 3. Health Check
```bash
GET /health
```

Response:
```json
{
  "status": "healthy",
  "service": "sentiment-analyzer",
  "model_loaded": true,
  "sentiment_history_size": 42
}
```

#### 4. Prometheus Metrics
```bash
GET /metrics
```

Returns Prometheus-formatted metrics including:
- `sentiment_requests_total`: Total requests processed
- `sentiment_positive_total`: Total positive sentiments
- `sentiment_negative_total`: Total negative sentiments
- `sentiment_score`: Current aggregate sentiment score (-1 to 1)
- `sentiment_request_duration_seconds`: Request latency histogram

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `REDDIT_CLIENT_ID` | Reddit API client ID | required |
| `REDDIT_CLIENT_SECRET` | Reddit API client secret | required |
| `REDDIT_USER_AGENT` | Reddit API user agent | sentiment-analyzer/1.0 |
| `REDDIT_USERNAME` | Reddit username | optional |
| `REDDIT_PASSWORD` | Reddit password | optional |
| `SUBREDDIT` | Subreddit to monitor | wallstreetbets |
| `BATCH_SIZE` | Number of comments per batch | 10 |
| `POLL_INTERVAL` | Seconds between polls | 60 |

## Development

### Running Locally (without Docker)

1. **Install dependencies**
```bash
pip install -r requirements.txt
```

2. **Start the sentiment API**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

3. **Start the ingestion service** (in another terminal)
```bash
python ingestion_service.py
```

### Testing the API

```bash
# Test sentiment analysis
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "I love this project!"}'

# Get market signal
curl http://localhost:8000/market-signal

# Check health
curl http://localhost:8000/health

# View metrics
curl http://localhost:8000/metrics
```

## Monitoring

Access Prometheus at http://localhost:9090 to:
- Query metrics
- Create custom dashboards
- Set up alerts based on sentiment trends

Example queries:
- `rate(sentiment_requests_total[5m])` - Request rate
- `sentiment_score` - Current sentiment score
- `sentiment_positive_total / (sentiment_positive_total + sentiment_negative_total)` - Positive ratio

## Architecture Details

```
┌─────────────────┐
│  Reddit API     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────────┐
│   Ingestion     │────▶│  Sentiment API   │
│   Service       │     │   (FastAPI)      │
└─────────────────┘     └────────┬─────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
              ┌──────────┐  ┌────────┐  ┌──────────┐
              │ /analyze │  │/market-│  │/metrics  │
              │          │  │signal  │  │          │
              └──────────┘  └────────┘  └────┬─────┘
                                              │
                                              ▼
                                        ┌──────────┐
                                        │Prometheus│
                                        └──────────┘
```

## Troubleshooting

**Issue**: Model download fails  
**Solution**: Ensure you have internet connectivity. The model is downloaded on first run.

**Issue**: Reddit API authentication fails  
**Solution**: Verify your credentials in `.env` file. Get valid credentials from https://www.reddit.com/prefs/apps

**Issue**: Services can't communicate  
**Solution**: Ensure all services are running in the same Docker network. Check `docker-compose logs`.

## Future Enhancements
- [ ] Add support for multiple data sources (Twitter, News APIs)
- [ ] Implement WebSocket for real-time updates
- [ ] Add Grafana dashboards for visualization
- [ ] Implement data persistence with database
- [ ] Add ML model fine-tuning for financial sentiment
- [ ] Implement alert system for significant sentiment shifts

## License
MIT
