# Monitoring & Observability

The MareAnalytica cluster has a full monitoring stack pre-installed.

## Stack Overview

| Component | URL | Namespace |
|-----------|-----|-----------|
| **Prometheus** | https://prometheus.mareanalytica.com | `monitoring` |
| **Grafana** | https://grafana.mareanalytica.com | `monitoring` |
| **Alertmanager** | https://alertmanager.mareanalytica.com | `monitoring` |
| **Loki** (logs) | Internal only | `monitoring` |
| **Headlamp** (k8s UI) | https://headlamp.mareanalytica.com | `kube-system` |

All dashboards are accessible via the `*.mareanalytica.com` wildcard DNS.

## Prometheus

Deployed via `kube-prometheus-stack` Helm chart. Scrapes metrics from:
- **kube-state-metrics** — Kubernetes object states (pods, deployments, nodes)
- **node-exporter** — Host-level metrics (CPU, memory, disk, network)
- **kubelet/cAdvisor** — Container-level metrics
- **Any pod with Prometheus annotations**

### Adding metrics to your service

Add these annotations to your pod template to get automatic scraping:

```yaml
spec:
  template:
    metadata:
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"      # your metrics port
        prometheus.io/path: "/metrics"   # your metrics endpoint
```

For Python services, use `prometheus-client`:
```python
from prometheus_client import Counter, Histogram, generate_latest
from fastapi import FastAPI
from fastapi.responses import Response

app = FastAPI()
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'Request latency', ['endpoint'])

@app.get("/metrics")
def metrics():
    return Response(content=generate_latest(), media_type="text/plain")
```

## Grafana

Pre-configured dashboards:
- **Kubernetes / Compute Resources / Namespace** — CPU/memory per namespace
- **Kubernetes / Compute Resources / Pod** — CPU/memory per pod
- **Node Exporter / Nodes** — Host-level resource usage
- **Kubernetes / Networking / Namespace** — Network I/O

### Creating dashboards for your service

1. Go to https://grafana.mareanalytica.com
2. Create → Dashboard → Add visualization
3. Select "Prometheus" as data source
4. Query examples:
   ```promql
   # Request rate for your service
   rate(http_requests_total{namespace="MY_PROJECT-dev"}[5m])

   # Memory usage
   container_memory_working_set_bytes{namespace="MY_PROJECT-dev", container="backend"}

   # CPU usage
   rate(container_cpu_usage_seconds_total{namespace="MY_PROJECT-dev", container="backend"}[5m])

   # Pod restarts
   kube_pod_container_status_restarts_total{namespace="MY_PROJECT-dev"}
   ```

## Alertmanager

Receives alerts from Prometheus. Default alerts include:
- Node down
- Pod crash looping
- High memory usage
- PVC nearly full

### Adding custom alerts

Create a `PrometheusRule` in your namespace:
```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: MY_PROJECT-alerts
  namespace: MY_PROJECT-dev
  labels:
    release: kube-prometheus-stack
spec:
  groups:
    - name: my-project
      rules:
        - alert: HighErrorRate
          expr: rate(http_requests_total{namespace="MY_PROJECT-dev", status=~"5.."}[5m]) > 0.1
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "High 5xx error rate in {{ $labels.namespace }}"
```

## Loki (Logs)

Loki collects logs from all pods. Query via Grafana → Explore → Select "Loki" data source.

```logql
# All logs from your namespace
{namespace="MY_PROJECT-dev"}

# Logs from a specific container
{namespace="MY_PROJECT-dev", container="backend"}

# Filter for errors
{namespace="MY_PROJECT-dev"} |= "ERROR"

# JSON log fields
{namespace="MY_PROJECT-dev"} | json | level="error"
```

## Useful kubectl commands

```bash
# Pod resource usage (requires metrics-server)
kubectl top pods -n MY_PROJECT-dev

# Node resource usage
kubectl top nodes

# Pod logs
kubectl logs -n MY_PROJECT-dev deploy/backend --tail=100 -f

# Events (good for debugging scheduling issues)
kubectl get events -n MY_PROJECT-dev --sort-by=.lastTimestamp

# Check HPA status (if using)
kubectl get hpa -n MY_PROJECT-dev
```

## Headlamp

Web-based Kubernetes dashboard at https://headlamp.mareanalytica.com.

Provides:
- Real-time pod status and logs
- Resource usage visualization
- YAML editor for quick fixes
- Event timeline

Generate a token:
```bash
kubectl create token headlamp-admin -n kube-system
```
