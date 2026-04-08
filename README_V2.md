# Helpdesk API - v2

API REST para sistema de Mesa de Ayuda con soporte multi-cloud y versionado de endpoints.

**Stack:** Django 5.2 + Django REST Framework + PostgreSQL + Google Cloud Run

---

## 📋 Tabla de Contenidos

- [Características](#características)
- [Versiones](#versiones)
- [Instalación Local](#instalación-local)
- [Variables de Entorno](#variables-de-entorno)
- [API Endpoints](#api-endpoints)
- [Despliegue en Google Cloud](#despliegue-en-google-cloud)
- [CI/CD Pipeline](#cicd-pipeline)
- [Integración Multi-Cloud](#integración-multi-cloud)

---

## ✨ Características

### v1 (Original)
- CRUD completo: Solicitantes, Tickets, Comentarios
- Endpoints: `/api/v1/solicitantes/`, `/api/v1/tickets/`, `/api/v1/comentarios/`
- Operaciones: GET, POST, PUT, DELETE

### v2 (Mejorada)
- ✅ **PATCH support**: Actualización parcial de recursos
- ✅ **Validaciones mejoradas**: Datos consistentes
- ✅ **Filtros avanzados**: Por estado, prioridad, etc.
- ✅ **Datos agregados**: Para integración multi-cloud
- ✅ **Documentación automática**: Swagger/OpenAPI
- ✅ **CORS habilitado**: Para conectar desde otras nubes
- Endpoints: `/api/v2/solicitantes/`, `/api/v2/tickets/`, `/api/v2/comentarios/`

---

## 🔄 Versiones

### GET - Listar recursos

```bash
# V1
curl http://localhost:8000/api/v1/solicitantes/

# V2
curl http://localhost:8000/api/v2/solicitantes/
```

### POST - Crear recurso

```bash
# V2
curl -X POST http://localhost:8000/api/v2/solicitantes/ \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Juan",
    "email": "juan@test.com",
    "telefono": "123456",
    "estado": "activo"
  }'
```

### PUT - Reemplazar completo

```bash
# Reemplaza TODO (requiere todos los campos)
curl -X PUT http://localhost:8000/api/v2/solicitantes/1/ \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Juan Updated",
    "email": "juan@test.com",
    "telefono": "999",
    "estado": "activo"
  }'
```

### PATCH - Actualización parcial (NUEVO en v2)

```bash
# Solo cambiar el teléfono (el resto se mantiene)
curl -X PATCH http://localhost:8000/api/v2/solicitantes/1/ \
  -H "Content-Type: application/json" \
  -d '{
    "telefono": "999"
  }'
```

### DELETE - Eliminar

```bash
curl -X DELETE http://localhost:8000/api/v2/solicitantes/1/
```

---

## 🚀 Instalación Local

### Requisitos
- Python 3.11+
- PostgreSQL 15
- pip

### Pasos

1. **Clonar repositorio**
```bash
git clone https://github.com/sebasruizr05/helpdesk-api.git
cd helpdesk-api
```

2. **Crear virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # En macOS/Linux
# o
venv\Scripts\activate  # En Windows
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**
```bash
cp .env.example .env
# Editar .env con tus datos
```

5. **Realizar migraciones**
```bash
python manage.py migrate
```

6. **Crear superusuario (opcional)**
```bash
python manage.py createsuperuser
```

7. **Ejecutar servidor**
```bash
python manage.py runserver
```

La API estará en: `http://localhost:8000`

---

## 🔑 Variables de Entorno

### Desarrollo (.env)
```
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1
ENVIRONMENT=development

DB_NAME=helpdesk_dev
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

### Staging (.env.staging)
```
DEBUG=False
SECRET_KEY=staging-secret-key-change-this
ALLOWED_HOSTS=helpdesk-staging.run.app
ENVIRONMENT=staging

DB_NAME=helpdesk_staging
DB_USER=staging_user
DB_PASSWORD=staging_pass_secure_12345
DB_HOST=34.31.168.14
DB_PORT=5432

CORS_ALLOWED_ORIGINS=https://helpdesk-staging.run.app
```

### Producción (.env.production)
```
DEBUG=False
SECRET_KEY=prod-secret-key-super-secure
ALLOWED_HOSTS=helpdesk-api.run.app
ENVIRONMENT=production

DB_NAME=helpdesk_prod
DB_USER=prod_user
DB_PASSWORD=prod_pass_super_secure_67890
DB_HOST=34.31.168.14
DB_PORT=5432

CORS_ALLOWED_ORIGINS=https://helpdesk-api.run.app
```

---

## 📡 API Endpoints

### V2 - Solicitantes

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v2/solicitantes/` | Listar todos |
| POST | `/api/v2/solicitantes/` | Crear nuevo |
| GET | `/api/v2/solicitantes/{id}/` | Obtener uno |
| PUT | `/api/v2/solicitantes/{id}/` | Reemplazar completo |
| PATCH | `/api/v2/solicitantes/{id}/` | Actualización parcial |
| DELETE | `/api/v2/solicitantes/{id}/` | Eliminar |
| GET | `/api/v2/solicitantes/activos/` | Solo activos |
| GET | `/api/v2/solicitantes/inactivos/` | Solo inactivos |

### V2 - Tickets

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v2/tickets/` | Listar todos |
| POST | `/api/v2/tickets/` | Crear nuevo |
| GET | `/api/v2/tickets/{id}/` | Obtener uno |
| PUT | `/api/v2/tickets/{id}/` | Reemplazar completo |
| PATCH | `/api/v2/tickets/{id}/` | Actualización parcial |
| DELETE | `/api/v2/tickets/{id}/` | Eliminar |
| GET | `/api/v2/tickets/por_estado/` | Agrupar por estado |
| GET | `/api/v2/tickets/por_prioridad/` | Agrupar por prioridad |
| GET | `/api/v2/tickets/?estado=abierto` | Filtrar por estado |
| GET | `/api/v2/tickets/?prioridad=alta` | Filtrar por prioridad |

### V2 - Comentarios

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v2/comentarios/` | Listar todos |
| POST | `/api/v2/comentarios/` | Crear nuevo |
| GET | `/api/v2/comentarios/{id}/` | Obtener uno |
| PUT | `/api/v2/comentarios/{id}/` | Reemplazar completo |
| PATCH | `/api/v2/comentarios/{id}/` | Actualización parcial |
| DELETE | `/api/v2/comentarios/{id}/` | Eliminar |
| GET | `/api/v2/comentarios/?ticket=1` | Filtrar por ticket |

### Documentación

| Endpoint | Descripción |
|----------|-------------|
| `GET /api/docs/` | Swagger UI |
| `GET /api/redoc/` | ReDoc |
| `GET /api/schema/` | OpenAPI Schema |

---

## 🌐 Despliegue en Google Cloud

### Requisitos
- Cuenta Google Cloud configurada
- Cloud Run habilitado
- Cloud SQL PostgreSQL creado
- Artifact Registry configurado

### Pasos

1. **Crear Artifact Registry**
```bash
gcloud artifacts repositories create helpdesk-repo \
  --repository-format=docker \
  --location=us-central1
```

2. **Configurar permisos para Cloud Run**
```bash
gcloud projects add-iam-policy-binding helpdesk-api-492703 \
  --member=serviceAccount:cloud-run-sa@helpdesk-api-492703.iam.gserviceaccount.com \
  --role=roles/cloudsql.client
```

3. **Crear secretos en Secret Manager** (para credenciales)
```bash
# Staging
echo -n "staging_pass_secure_12345" | gcloud secrets create staging_db_password --data-file=-
echo -n "staging-secret-key-change-this" | gcloud secrets create staging_secret_key --data-file=-

# Producción
echo -n "prod_pass_super_secure_67890" | gcloud secrets create prod_db_password --data-file=-
echo -n "prod-secret-key-super-secure" | gcloud secrets create prod_secret_key --data-file=-
```

4. **Despliegue manual (si CI/CD no está configurado)**
```bash
gcloud run deploy helpdesk-staging \
  --image us-central1-docker.pkg.dev/helpdesk-api-492703/helpdesk-repo/helpdesk-api:latest \
  --region us-central1 \
  --platform managed \
  --set-env-vars ENVIRONMENT=staging,DB_NAME=helpdesk_staging,DB_USER=staging_user,DB_HOST=34.31.168.14 \
  --set-secrets DB_PASSWORD=staging_db_password:latest,SECRET_KEY=staging_secret_key:latest
```

---

## 🔄 CI/CD Pipeline

El repositorio está configurado con GitHub Actions que:

1. **En PR o push a `develop` o `main`:**
   - Ejecuta tests automáticos (pytest)
   - Valida cobertura de código
   - Construye imagen Docker

2. **En push a `develop`:**
   - Despliega a Staging (helpdesk-staging.run.app)
   - Tests automáticos

3. **En push a `main`:**
   - Despliega a Producción (helpdesk-api.run.app)
   - Tests automáticos

### Ver estado del CI/CD
Ve a: GitHub → Actions → CI/CD Pipeline

---

## 🤝 Integración Multi-Cloud

### Arquitectura

```
API Anterior (Nube 1)
        ↓
    Tu API (Google Cloud - Nube 2)
        ↓
API Siguiente (Nube 3)
```

### Endpoints especiales para integración

**Recibir datos de API anterior:**
```bash
POST /api/v2/tickets/create_with_data/
{
  "datos_previos": {...},  # Datos de API anterior
  "solicitante": 1,
  "asunto": "...",
  ...
}
```

**Retornar datos agregados:**
```bash
GET /api/v2/tickets/1/retrieve_with_data/
{
  ...ticket data...,
  "datos_agregados": {
    "datos_previos": {...},
    "datos_locales": {...},
    "timestamp": "..."
  }
}
```

---

## 📊 Modelos de Datos

### Solicitante
```python
{
  "id": 1,
  "nombre": "Juan",
  "email": "juan@test.com",
  "telefono": "123456",
  "estado": "activo",  # activo, inactivo
  "created_at": "2026-04-07T...",
  "updated_at": "2026-04-07T...",
  "full_contact": {
    "email": "juan@test.com",
    "telefono": "123456"
  }
}
```

### Ticket
```python
{
  "id": 1,
  "solicitante": 1,
  "solicitante_nombre": "Juan",
  "asunto": "Error en login",
  "descripcion": "No puedo acceder...",
  "estado": "abierto",  # abierto, en_progreso, resuelto, cerrado
  "prioridad": "alta",  # baja, media, alta, critica
  "comentarios_count": 2,
  "created_at": "2026-04-07T...",
  "updated_at": "2026-04-07T...",
  "closed_at": null
}
```

### Comentario
```python
{
  "id": 1,
  "ticket": 1,
  "ticket_asunto": "Error en login",
  "autor": "agente",  # solicitante, agente
  "mensaje": "Estamos trabajando en esto...",
  "created_at": "2026-04-07T..."
}
```

---

## 🧪 Tests

### Ejecutar tests localmente
```bash
pytest

# Con cobertura
pytest --cov=soporte --cov-report=html
```

### Archivo de configuración pytest
Ver: `pytest.ini`

---

## 📚 Estructura del Proyecto

```
helpdesk-api/
├── helpdesk/
│   ├── settings.py         # Configuración Django
│   ├── urls.py             # Rutas v1 y v2
│   ├── wsgi.py
│   └── asgi.py
├── soporte/
│   ├── models.py           # Modelos de datos
│   ├── serializers.py      # Serializers v1 y v2
│   ├── views.py            # ViewSets v1 y v2
│   ├── tests.py            # Tests
│   └── admin.py
├── .github/workflows/
│   └── ci-cd.yml           # GitHub Actions
├── .env.example
├── .env.staging
├── .env.production
├── Dockerfile              # Multi-stage build
├── docker-compose.yml
├── cloudbuild.yaml         # Google Cloud Build
├── requirements.txt
├── manage.py
└── pytest.ini
```

---

## 🐛 Troubleshooting

### Error: "Database connection failed"
- Verificar que Cloud SQL está activo
- Verificar IP de Cloud SQL en .env
- Verificar credenciales de DB

### Error: "Secret not found"
- Crear secretos en Google Secret Manager
- Ver sección: Despliegue en Google Cloud

### Tests fallan localmente
```bash
# Usar SQLite para tests
export USE_SQLITE=true
pytest
```

---

## 📝 Licencia

MIT

---

## 👨‍💻 Autor

Sebastián Ruiz

---

## 🔗 Links útiles

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Google Cloud Run Docs](https://cloud.google.com/run/docs)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)

---

**Última actualización:** 7 de Abril de 2026
