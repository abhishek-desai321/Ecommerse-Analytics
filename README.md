# Real-Time E-commerce Analytics Platform

A high-performance analytics system built with FastAPI, Redis Streams, and React.

## Features
- **High Throughput**: Handles >100 events/second using Redis Streams and Asyncio.
- **Real-Time Dashboard**: Auto-refreshing metrics for Active Users, Sessions, and Top Pages.
- **Rolling Windows**: 
  - Active Users (Last 5 mins)
  - Page Views (Last 15 mins)
  - Active Sessions (Last 5 mins)
- **Scalable Architecture**: Dockerized microservices.

## Technology Stack
- **Backend**: FastAPI, Python 3.11, Pydantic
- **Broker/DB**: Redis (Streams + Sorted Sets)
- **Frontend**: React, Vite, Recharts, Lucide
- **Infra**: Docker Compose

## Architecture

```mermaid
graph TD
    Client[Client / Mock Gen] -->|POST /ingest| API[FastAPI Backend]
    Client -->|GET /metrics| API
    
    subgraph Redis
        Stream[Redis Stream (events_stream)]
        Stats[Redis Stats (ZSETs & Hashes)]
        DLQ[DLQ Stream (events_dlq)]
    end
    
    API -->|XADD| Stream
    API -->|Read| Stats
    API -.->|Invalid Events| DLQ
    
    Stream -->|XREADGROUP| Worker[Analytics Worker]
    Worker -->|Process & Bucket| Stats
    
    Prometheus[Prometheus] -->|Scrape| API
    Prometheus -->|Scrape| Worker
    Prometheus -->|Scrape| RedisExporter[Redis Exporter]
    RedisExporter -->|Collect| Stats
    
    Grafana[Grafana] -->|Query| Prometheus
```

## Setup
1. **Start Services**:
   ```bash
   docker-compose up --build
   ```
   Wait for services to initialize. The frontend may take a moment to install dependencies.

2. **Access Dashboard**:
   Open [http://localhost:5173](http://localhost:5173).

3. **Generate Traffic**:
   Run the mock generator to simulate users:
   ```bash
   python mock_gen.py
   ```
   (Requires `requests` installed locally: `pip install requests`)

## Design Rationale

### Key Requirements
1. **Real-time Aggregation**: Show metrics (Active users, Active sessions, Pageviews) over rolling time windows (5/15 mins).
2. **High Performance**: Needs a high throughput, low latency system for fast aggregation and periodic dashboard polling.
3. **Architecture Choice**: **Redis Streams** (Ingestion) + **Redis Cache** (Aggregation) fits these needs perfectly.

### Trade-offs & Benefits
| Trade-off | Description |
|-----------|-------------|
| **No Historical Data** | System focuses on live windows, not long-term storage. |
| **Volatile Storage** | In-memory Redis data is fast but prone to loss on crash (without AOF/RDB). |
| **Fixed Windows** | Metrics are optimized for specific time slices (e.g., last 15 mins). |
| **Prone to Downtime** | Single Redis instance can be a point of failure. |

**Key Benefit**: Extremely light-weight and fast.

### Reliability & Recovery
Assuming a Kubernetes (K8s) deployment:
- **Service Downtime**: Restart services in ~5 mins.
- **Data Recovery**: Time to accurate windowed data ~15 mins (window fill time).
- **MTTR**: ~20 mins.

For higher uptime SLAs or historical analysis, we would migrate to distributed systems:
- **Kafka** instead of Redis Streams (Durability).
- **Apache Pinot / Druid** instead of Redis Cache (OLAP, Historicals).
- **Cost**: This would significantly increase infrastructure costs but guarantee high availability and data persistence.

### Scalability
The **Event Processing Layer** (REST API + Worker) is completely stateless. It can be easily horizontally scaled (e.g., adding more worker replicas to consume from Consumer Groups) to handle increased load.

### Bucketing Strategy (Optimized Page Views)
For high-volume metrics like "Top 5 Pages", storing every individual event in a Sorted Set is inefficient (O(N) memory). We implemented a "Time Bucket" strategy:
- **Write**: The worker aggregates page views into **1-minute Redis Hashes**.
- **Read**: The API pipeline-fetches the last 15 bucket keys/hashes.
- **Efficiency**: Reduces memory usage from linear to constant.

## Testing

The project includes unit tests for both backend (pytest) and frontend (vitest).

### Backend Tests
Run tests inside the backend container:
```bash
docker-compose exec backend pytest
```

### Frontend Tests
Run tests inside the frontend container:
```bash
docker-compose exec frontend npm test
```

### Running Tests Locally (Optional)
If you have dependencies installed locally:
- Backend: `pytest`
- Frontend: `npm install && npm test`


## Monitoring
The platform includes a complete observability stack:
- **Prometheus**: Collects metrics from all services.
  - Access: [http://localhost:9094](http://localhost:9094)
- **Grafana**: Visualizes metrics on a pre-provisioned dashboard.
  - Access: [http://localhost:3000](http://localhost:3000) (Credentials: `admin`/`admin`)
  - Dashboard: "E-Commerce Analytics" (Auto-refreshes every 10s)

