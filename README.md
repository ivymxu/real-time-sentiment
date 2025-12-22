# Real-Time Trend Monitor API

### Rationale
As a doom-scroller with FOMO but is also deeply interested in Machine Learning, DevOps, and SRE, I wanted to explore something that blends all of these concepts using an interesting live data source.

### Idea
Build a microservice that ingests a live stream of data using Reddit comments on a trending topic, runs it through a sentiment analysis model, and exposes metrics via an API or dashboard.

### Architecture Overview
- Ingestion Service: A Python script that polls an API (Reddit/NewsAPI)
- ML Service: A lightweight FastAPI wrapper around a Hugging Face Transformer
- Infrastructure: Dockerized containers orchestrated via a docker-compose file
- Monitoring (SRE): Prometheus metrics exposed by an API to track request latency and sentiment distribution
