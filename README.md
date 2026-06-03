# helpdesk-api

API REST para mesa de ayuda (solicitante, ticket, comentario) usando Django + DRF.

---

## Despliegue Canary en Kubernetes

### Estrategia de distribución de tráfico

Se usa una estrategia de **Canary Deployment basada en proporción de réplicas**:

| Deployment | Réplicas | Tráfico aproximado | Health status |
|---|---|---|---|
| `helpdesk-stable` | 3 | ~75% | `stable` |
| `helpdesk-canary` | 1 | ~25% | `canary` |

**Cómo funciona:**

1. Ambos Deployments comparten el label `app: helpdesk-api`.
2. El **Service común** (`helpdesk-service`) selecciona todos los pods con ese label, balanceando el tráfico entre los 4 pods en total.
3. El **Ingress** expone el Service al exterior. Todo el tráfico externo entra por el mismo punto de entrada.
4. La distribución 75/25 emerge naturalmente de la relación 3:1 de réplicas — sin configuración adicional de pesos.

```
Internet
    │
    ▼
[ Ingress ]  ──────────────────────────────────┐
    │                                           │
    ▼                                           │
[ helpdesk-service ] ──── selector: app=helpdesk-api
    │
    ├── Pod stable-1  (DEPLOY_TYPE=stable, v2.0.0)  ┐
    ├── Pod stable-2  (DEPLOY_TYPE=stable, v2.0.0)  ├ 75% del tráfico
    ├── Pod stable-3  (DEPLOY_TYPE=stable, v2.0.0)  ┘
    │
    └── Pod canary-1  (DEPLOY_TYPE=canary, v2.1.0)    25% del tráfico
```

### Archivos Kubernetes

```
k8s/
├── namespace.yaml           # Namespace "helpdesk"
├── stable-deployment.yaml   # 3 réplicas, DEPLOY_TYPE=stable
├── canary-deployment.yaml   # 1 réplica,  DEPLOY_TYPE=canary
├── service.yaml             # Service común (ClusterIP)
└── ingress.yaml             # Ingress nginx → helpdesk-service
```

### Despliegue manual

```bash
# 1. Reemplazar PROJECT_ID con el ID real del proyecto GCP
sed -i "s/PROJECT_ID/<tu-project-id>/g" k8s/stable-deployment.yaml k8s/canary-deployment.yaml

# 2. Aplicar todos los manifests
kubectl apply -f k8s/

# 3. Verificar pods de ambos deployments
kubectl get pods -n helpdesk -L track,version
```

---

## URLs para validar ambos despliegues (Postman)

Reemplazar `<INGRESS_IP>` con la IP externa del Ingress:

```bash
kubectl get ingress -n helpdesk
```

### Health Check — detecta stable o canary

```
GET http://<INGRESS_IP>/health/
```

**Respuesta stable:**
```json
{
  "status": "stable",
  "version": "2.0.0",
  "app": "helpdesk-api",
  "environment": "production",
  "timestamp": "2026-06-02T12:00:00.000000+00:00"
}
```

**Respuesta canary** (aparece ~25% de las veces):
```json
{
  "status": "canary",
  "version": "2.1.0",
  "app": "helpdesk-api",
  "environment": "production",
  "timestamp": "2026-06-02T12:00:00.000000+00:00",
  "deploy_date": "2026-06-02",
  "features_preview": ["priority-filter-v2", "real-time-ticket-notifications"]
}
```

### Endpoints funcionales

| Método | URL | Descripción |
|---|---|---|
| GET | `http://<INGRESS_IP>/health/` | Health check (stable/canary) |
| GET | `http://<INGRESS_IP>/api/v2/tickets/` | Listar tickets |
| POST | `http://<INGRESS_IP>/api/v2/tickets/` | Crear ticket |
| GET | `http://<INGRESS_IP>/api/v2/solicitantes/` | Listar solicitantes |
| GET | `http://<INGRESS_IP>/api/docs/` | Swagger UI |

---

## Monitoreo de la estrategia canary

### Ver distribución de pods en tiempo real

```bash
# Listar pods con su track (stable/canary) y versión
kubectl get pods -n helpdesk -L track,version

# Ver logs solo del deployment canary
kubectl logs -n helpdesk -l track=canary -f

# Ver logs solo del deployment stable
kubectl logs -n helpdesk -l track=stable -f
```

### Verificar la distribución de tráfico

Ejecutar múltiples requests al health check y contar respuestas:

```bash
# Requiere jq instalado
for i in $(seq 1 20); do
  curl -s http://<INGRESS_IP>/health/ | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['status'], d['version'])"
done
```

Resultado esperado: ~15 respuestas `stable` y ~5 respuestas `canary`.

### Cloud Monitoring (GKE)

En la consola de GCP → Kubernetes Engine → Workloads:
- `helpdesk-stable`: métricas de los 3 pods stable
- `helpdesk-canary`: métricas del 1 pod canary

Filtrar logs en Cloud Logging:
```
resource.type="k8s_container"
resource.labels.namespace_name="helpdesk"
labels."k8s-pod/track"="canary"
```

---

## Variables de entorno relevantes

| Variable | Stable | Canary |
|---|---|---|
| `DEPLOY_TYPE` | `stable` | `canary` |
| `APP_VERSION` | `2.0.0` | `2.1.0` |
| `DEPLOY_DATE` | — | `2026-06-02` |
| `ENVIRONMENT` | `production` | `production` |
