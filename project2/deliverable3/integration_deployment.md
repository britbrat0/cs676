# Persona Feedback Simulator – Integration & Deployment

## Table of Contents
1. [Overview](#overview)  
2. [System Architecture](#system-architecture)  
3. [Prerequisites](#prerequisites)  
4. [Installation and Setup](#installation-and-setup)  
5. [Configuration](#configuration)  
6. [Database / Data Storage](#database--data-storage)  
7. [API Specifications](#api-specifications)  
8. [Deployment Procedures](#deployment-procedures)  
9. [Monitoring and Metrics](#monitoring-and-metrics)  
10. [Maintenance and Update Procedures](#maintenance-and-update-procedures)  
11. [Troubleshooting](#troubleshooting)  
12. [Backup and Recovery](#backup-and-recovery)  

---

## 1. Overview
The **Persona Feedback Simulator** is a Streamlit-based application that allows users to simulate conversations among virtual personas regarding product features. The system is designed to support:

- Multiple personas stored in `personas.json`
- AI-driven responses via OpenAI models (`gpt-4o-mini` recommended)
- Automatic backup and recovery of persona data
- Monitoring and observability via Prometheus metrics
- Scalable deployment with load balancing

---

## 2. System Architecture
**Components:**
1. **Streamlit App** (`app.py`)  
   - Handles UI, persona selection, question submission, AI integration, and persona responses.
2. **Prometheus Metrics** (`Counter`, `Histogram`)  
   - Exposes metrics on `/metrics` for request counts, response times, and errors.
3. **Load Balancer** (NGINX)  
   - Balances traffic between multiple containerized app instances.
4. **Persistent Storage** (`personas.json` + backup `personas_backup.json`)  
   - Stores persona definitions and allows safe recovery.
5. **Optional Cloud Integration**  
   - Can use S3, GCS, or a database backend for production durability.

**Diagram:**

```
[User Browser] --> [NGINX Load Balancer] --> [Streamlit App Containers]
                                         \--> [Prometheus Metrics]
                                         \--> [Persistent Storage / Backup]
```

---

## 3. Prerequisites
- **Python 3.11+** (tested with 3.13)  
- **Docker & Docker Compose** for containerized deployment  
- **OpenAI API key** for AI responses  
- **Prometheus** for metrics collection (optional, but recommended)  

**Python packages** (in `requirements.txt`):
```
streamlit
openai
prometheus_client
```

---

## 4. Installation and Setup

1. **Clone the repository:**
```bash
git clone https://github.com/<your-username>/persona-feedback-simulator.git
cd persona-feedback-simulator
```

2. **Set OpenAI API Key:**
```bash
export OPENAI_API_KEY="sk-..."
```

3. **Install dependencies locally (optional):**
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

4. **Run the app locally:**
```bash
streamlit run app.py
```

---

## 5. Configuration

### Environment Variables
- `OPENAI_API_KEY` – OpenAI authentication
- `PROMETHEUS_PORT` – Optional, defaults to 8000
- `STREAMLIT_PORT` – Optional, defaults to 8501

### Configuration Files
- `personas.json` – Primary persona definitions
- `personas_backup.json` – Auto-backup file
- `prometheus.yml` – Prometheus scrape configuration
- `nginx.conf` – Load balancer configuration

---

## 6. Database / Data Storage
Currently uses **JSON files**:

### `personas.json`
| Field | Type | Description |
|-------|------|-------------|
| id | integer | Unique persona ID |
| name | string | Persona full name |
| occupation | string | Job title |
| location | string | Geographical location |
| tech_proficiency | string | "Low", "Medium", or "High" |
| behavioral_traits | array[string] | List of persona traits |

### Backup Strategy
- Automatic backup to `personas_backup.json` whenever personas are added or modified.
- Restore automatically if `personas.json` is missing or corrupted.

---

## 7. API Specifications

### 7.1 Internal App Functions
| Function | Endpoint/Usage | Description |
|----------|----------------|-------------|
| `generate_response` | Internal | Sends feature input + persona data to OpenAI and returns conversation |
| `generate_feedback_report` | Internal | Summarizes conversation with actionable insights |
| `instrumented` | Decorator | Wraps functions for Prometheus metrics (`REQUEST_COUNTER`, `RESPONSE_TIME`) |

### 7.2 Prometheus Metrics
Exposed at `/metrics` (default port 8000):

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `app_requests_total` | Counter | `endpoint`, `status` | Counts total requests and success/error outcomes |
| `app_response_time_seconds` | Histogram | `endpoint` | Measures response duration per endpoint |
| `app_heartbeat` | Gauge | – | Optional: timestamp for health checks |

### 7.3 Health Endpoint
Optional `/healthz` endpoint for load balancer or Kubernetes:

```python
@app.route("/healthz")
def health():
    return "OK", 200
```

---

## 8. Deployment Procedures

### 8.1 Docker Deployment
**Dockerfile**
```dockerfile
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8501 8000
CMD ["streamlit", "run", "app.py", "--server.port=8501"]
```

**Docker Compose**
```yaml
version: '3'
services:
  app1:
    build: .
    ports:
      - "8501:8501"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
  nginx:
    image: nginx:latest
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
```

---

## 9. Monitoring and Metrics

1. **Prometheus Scraping**
```yaml
scrape_configs:
  - job_name: 'persona_app'
    static_configs:
      - targets: ['app1:8000', 'app2:8000', 'app3:8000']
```

2. **Metrics to Watch**
- Request counts per endpoint
- Error rate
- Response latency
- Heartbeat (optional)

3. **Optional Visualization**
- Connect Prometheus to Grafana dashboards
- Create alerts for:
  - High error rate
  - Service unavailability
  - Slow response times

---

## 10. Maintenance and Update Procedures

- **Update Python packages:** `pip install -r requirements.txt --upgrade`
- **Update app code:** Pull latest from GitHub and rebuild Docker containers
- **Persona updates:** Add through UI, then backup occurs automatically
- **Rolling restart:** Use Docker Compose `up -d --force-recreate` or Kubernetes Deployment rolling update
- **Configuration changes:** Update `nginx.conf`, `prometheus.yml`, or `.env` variables and reload respective services

---

## 11. Troubleshooting

| Issue | Solution |
|-------|---------|
| `personas.json` not found | Ensure it exists next to `app.py` or restore from backup |
| Duplicated Prometheus metrics | Use custom registry or `st.cache_resource` (see metrics setup) |
| OpenAI errors | Verify `OPENAI_API_KEY` and network connectivity |
| Streamlit reload issues | Clear browser cache or restart app container |

---

## 12. Backup and Recovery

1. **Automatic Backup:** Occurs whenever personas are added or modified → saved to `personas_backup.json`.
2. **Restore Backup:** If `personas.json` missing or corrupted, app restores from backup on startup.
3. **Manual Backup Trigger:** Call `backup_personas()` in code after persona updates.
4. **Optional Cloud Backup:** Sync `personas_backup.json` to S3/GCS for off-site durability.

---

### Notes for Developers
- Always maintain a **clean `personas.json`** in version control for initial deployments.
- Use the **backup/restore helpers** to prevent accidental persona data loss.
- Keep **metrics endpoints open** only for internal monitoring (don’t expose publicly without authentication).

