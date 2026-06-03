# helpdesk-api

API REST para mesa de ayuda (solicitante, ticket, comentario) usando Django + DRF.

---

## Despliegue Canary en Kubernetes

### Estrategia de distribución de tráfico

Se usa una estrategia de **Canary Deployment basada en proporción de réplicas**:

| Deployment | Réplicas | Tráfico aproximado | Versión | Health status |
|---|---|---|---|---|
| `helpdesk-stable` | 2 | ~67% | 2.0.0 | `stable` |
| `helpdesk-canary` | 1 | ~33% | 2.1.0 | `canary` |

**Cómo funciona:**

1. Ambos Deployments comparten el label `app: helpdesk-api`.
2. El **Service común** (`helpdesk-service`) selecciona todos los pods con ese label, balanceando el tráfico entre los 3 pods en total.
3. El **Ingress** expone el Service al exterior con una única IP pública. Todo el tráfico externo entra por el mismo punto de entrada.
4. La distribución 67/33 emerge naturalmente de la relación 2:1 de réplicas — sin configuración adicional de pesos ni reglas de enrutamiento.
5. Cada pod responde con su propia versión según la variable de entorno `DEPLOY_TYPE` configurada en su Deployment.

```
Internet
    │
    ▼
[ Ingress - IP: 136.114.90.59 ]
    │
    ▼
[ helpdesk-service ] ──── selector: app=helpdesk-api
    │
    ├── Pod stable-1  (DEPLOY_TYPE=stable, v2.0.0)  ┐
    ├── Pod stable-2  (DEPLOY_TYPE=stable, v2.0.0)  ├ ~67% del tráfico
    │
    └── Pod canary-1  (DEPLOY_TYPE=canary, v2.1.0)    ~33% del tráfico
```

### Archivos Kubernetes

```
k8s/
├── namespace.yaml           # Namespace "helpdesk"
├── stable-deployment.yaml   # 2 réplicas, DEPLOY_TYPE=stable, v2.0.0
├── canary-deployment.yaml   # 1 réplica,  DEPLOY_TYPE=canary, v2.1.0
├── service.yaml             # Service común (ClusterIP)
└── ingress.yaml             # Ingress nginx → helpdesk-service
```

---

## URLs para validar ambos despliegues (Postman / curl)

La IP pública del Ingress es `136.114.90.59`.

Para obtenerla en cualquier momento:
```bash
kubectl get ingress -n helpdesk
```

---

### Health Check — detecta stable o canary

**Método:** `GET`
**URL:** `http://136.114.90.59/health/`

Ejecutar varias veces para observar la distribución. Aproximadamente 1 de cada 3 requests llegará al pod canary.

**Respuesta stable** (~67% de las veces):
```json
{
  "status": "stable",
  "version": "2.0.0",
  "app": "helpdesk-api",
  "environment": "production",
  "timestamp": "2026-06-03T12:00:00.000000+00:00"
}
```

**Respuesta canary** (~33% de las veces):
```json
{
  "status": "canary",
  "version": "2.1.0",
  "app": "helpdesk-api",
  "environment": "production",
  "timestamp": "2026-06-03T12:00:00.000000+00:00",
  "deploy_date": "2026-06-03",
  "features_preview": ["priority-filter-v2", "real-time-ticket-notifications"]
}
```

---

### Endpoints funcionales

| Método | URL | Descripción |
|---|---|---|
| GET | `http://136.114.90.59/health/` | Health check — muestra si el pod es stable o canary |
| GET | `http://136.114.90.59/api/v2/tickets/` | Listar tickets |
| POST | `http://136.114.90.59/api/v2/tickets/` | Crear ticket |
| GET | `http://136.114.90.59/api/v2/solicitantes/` | Listar solicitantes |
| GET | `http://136.114.90.59/api/docs/` | Swagger UI |

---

## Monitoreo de la estrategia canary

### 1. Ver distribución de tráfico en tiempo real (curl)

```bash
for i in $(seq 1 15); do
  curl -s http://136.114.90.59/health/ | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['status'], d['version'])"
done
```

Resultado esperado: ~10 respuestas `stable 2.0.0` y ~5 respuestas `canary 2.1.0`.

---

### 2. Ver estado de los pods en tiempo real (kubectl)

```bash
# Listar pods con track (stable/canary) y versión
kubectl get pods -n helpdesk -L track,version

# Ver logs en vivo del pod canary
kubectl logs -n helpdesk -l track=canary -f

# Ver logs en vivo de los pods stable
kubectl logs -n helpdesk -l track=stable -f
```

---

### 3. Consola GCP — Kubernetes Engine

URL directa al cluster en GCP Console:
```
https://console.cloud.google.com/kubernetes/workload/overview?project=helpdesk-api-492703
```

Desde ahí se puede ver:
- **Workloads** → `helpdesk-stable` (2 pods) y `helpdesk-canary` (1 pod)
- **Services & Ingress** → IP pública `136.114.90.59`
- **Pods** → estado individual de cada pod con su label `track`

---

### 4. Cloud Logging — filtrar por versión

En GCP Console → **Cloud Logging**, usar estos filtros:

**Solo logs del pod canary:**
```
resource.type="k8s_container"
resource.labels.namespace_name="helpdesk"
labels."k8s-pod/track"="canary"
```

**Solo logs de los pods stable:**
```
resource.type="k8s_container"
resource.labels.namespace_name="helpdesk"
labels."k8s-pod/track"="stable"
```

---

## Variables de entorno relevantes

| Variable | Stable | Canary |
|---|---|---|
| `DEPLOY_TYPE` | `stable` | `canary` |
| `APP_VERSION` | `2.0.0` | `2.1.0` |
| `DEPLOY_DATE` | — | `2026-06-03` |
| `ENVIRONMENT` | `production` | `production` |
