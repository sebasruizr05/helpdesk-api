import pytest
from rest_framework.test import APIClient
from soporte.models import Solicitante, Ticket, IntegracionEvento


@pytest.mark.django_db
def test_crear_solicitante_modelo():
    solicitante = Solicitante.objects.create(
        nombre="Juan",
        email="juan@test.com",
        telefono="123456",
        estado="activo"
    )

    assert solicitante.id is not None
    assert solicitante.nombre == "Juan"


@pytest.mark.django_db
def test_listar_solicitantes_api():
    client = APIClient()

    Solicitante.objects.create(
        nombre="Ana",
        email="ana@test.com",
        telefono="111",
        estado="activo"
    )

    response = client.get("/api/v1/solicitantes/")

    assert response.status_code == 200
    assert len(response.data) >= 1


@pytest.mark.django_db
def test_crear_solicitante_api():
    client = APIClient()

    data = {
        "nombre": "Pedro",
        "email": "pedro@test.com",
        "telefono": "222",
        "estado": "activo"
    }

    response = client.post("/api/v1/solicitantes/", data)

    assert response.status_code == 201


@pytest.mark.django_db
def test_solicitante_guardado_en_bd():
    Solicitante.objects.create(
        nombre="Maria",
        email="maria@test.com",
        telefono="333",
        estado="activo"
    )

    assert Solicitante.objects.count() == 1


@pytest.mark.django_db
def test_crear_solicitante_sin_email():
    client = APIClient()

    data = {
        "nombre": "Error Test",
        "telefono": "123",
        "estado": "activo"
    }

    response = client.post("/api/v1/solicitantes/", data)

    assert response.status_code == 400

@pytest.mark.django_db
def test_buscar_solicitante():
    Solicitante.objects.create(
        nombre="Carlos",
        email="carlos@test.com",
        telefono="111",
        estado="activo"
    )

    solicitante = Solicitante.objects.get(nombre="Carlos")

    assert solicitante.email == "carlos@test.com"


@pytest.mark.django_db
def test_lista_solicitantes_vacia():
    client = APIClient()

    response = client.get("/api/v1/solicitantes/")

    assert response.status_code == 200


@pytest.mark.django_db
def test_eliminar_solicitante():
    client = APIClient()

    solicitante = Solicitante.objects.create(
        nombre="Eliminar",
        email="eliminar@test.com",
        telefono="999",
        estado="activo"
    )

    response = client.delete(f"/api/v1/solicitantes/{solicitante.id}/")

    assert response.status_code == 204


@pytest.mark.django_db
def test_integracion_ingreso_payload_desconocido():
    client = APIClient()

    response = client.post("/api/v2/integraciones/ingreso/", {"foo": "bar"}, format="json")

    assert response.status_code == 202
    assert response.data["normalizado"] is False
    assert IntegracionEvento.objects.count() == 1


@pytest.mark.django_db
def test_integracion_ingreso_crea_ticket_si_mapea():
    client = APIClient()
    payload = {
        "source_system": "nube-a",
        "payload": {
            "solicitante": {
                "nombre": "Integracion User",
                "email": "integracion@test.com"
            },
            "ticket": {
                "asunto": "Incidente",
                "descripcion": "Detalle incidente",
                "prioridad": "alta"
            }
        }
    }

    response = client.post("/api/v2/integraciones/ingreso/", payload, format="json")

    assert response.status_code == 202
    assert response.data["normalizado"] is True
    assert Ticket.objects.count() == 1


@pytest.mark.django_db
def test_chain_procesa_payload_y_no_reenvia_si_no_hay_siguiente(monkeypatch):
    client = APIClient()
    monkeypatch.delenv("NEXT_API_URL", raising=False)

    payload = {
        "meta": {
            "antes": None,
            "origen": "peer-a",
            "siguiente": None,
        },
        "payload": {
            "continent_id": 5,
            "country_id": 25,
            "city_id": 301,
        },
    }

    response = client.post("/api/v2/chain/", payload, format="json")

    assert response.status_code == 202
    assert response.data["forwarded"] is False
    assert response.data["content_keys"] == ["city_id", "continent_id", "country_id"]
    assert Ticket.objects.count() == 0
    assert IntegracionEvento.objects.filter(direccion="entrada").count() == 1
    assert IntegracionEvento.objects.filter(direccion="salida").count() == 0


@pytest.mark.django_db
def test_chain_reenvia_payload_enriquecido_al_siguiente(monkeypatch):
    client = APIClient()
    captured = {}

    class DummyResponse:
        status_code = 200
        ok = True
        text = '{"status": "received"}'

        def json(self):
            return {"status": "received"}

    def fake_post(url, json, headers, timeout):
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        return DummyResponse()

    monkeypatch.setattr("soporte.views.requests.post", fake_post)
    monkeypatch.setenv("CHAIN_OUTBOUND_TOKEN", "secret-chain-token")

    solicitante = Solicitante.objects.create(
        nombre="Soporte Auto",
        email="auto@test.com",
        telefono="12345",
        estado="activo",
    )

    payload = {
        "meta": {
            "antes": None,
            "origen": "peer-a",
            "siguiente": "http://13.59.49.180:8000/api/v2/integracion/",
        },
        "payload": {
            "continent_id": 9,
            "country_id": 57,
            "city_id": 810,
        },
    }
    monkeypatch.setenv("NEXT_API_URL", "http://fallback-peer/api/v2/chain")

    response = client.post("/api/v2/chain/", payload, format="json")

    assert response.status_code == 200
    assert response.data["forwarded"] is True
    assert captured["url"] == "http://13.59.49.180:8000/api/v2/integracion/"
    assert captured["headers"]["X-Integration-Token"] == "secret-chain-token"
    assert captured["json"]["meta"]["origen"] == "helpdesk-api"
    assert captured["json"]["meta"]["antes"] == "peer-a"
    assert captured["json"]["payload"]["continent_id"] == 9
    assert captured["json"]["payload"]["soporte"]["solicitante"]["id"] == solicitante.id
    assert IntegracionEvento.objects.filter(direccion="entrada").count() == 1
    assert IntegracionEvento.objects.filter(direccion="salida").count() == 1


@pytest.mark.django_db
def test_chain_usa_next_api_url_como_respaldo(monkeypatch):
    client = APIClient()
    captured = {}

    class DummyResponse:
        status_code = 200
        ok = True
        text = '{"status": "received"}'

        def json(self):
            return {"status": "received"}

    def fake_post(url, json, headers, timeout):
        captured["url"] = url
        captured["json"] = json
        return DummyResponse()

    monkeypatch.setattr("soporte.views.requests.post", fake_post)
    monkeypatch.setenv("NEXT_API_URL", "http://fallback-peer/api/v2/chain")

    payload = {
        "meta": {
            "antes": None,
            "origen": "peer-a",
            "siguiente": None,
        },
        "payload": {
            "continent_id": 4,
            "country_id": 8,
            "city_id": 15,
        },
    }

    response = client.post("/api/v2/chain/", payload, format="json")

    assert response.status_code == 200
    assert response.data["next_url"] == "http://fallback-peer/api/v2/chain"
    assert response.data["forwarded"] is True
    assert captured["url"] == "http://fallback-peer/api/v2/chain"
    assert captured["json"]["payload"]["continent_id"] == 4


@pytest.mark.django_db
def test_integracion_eventos_lista_eventos_y_filtra_por_direccion():
    client = APIClient()

    IntegracionEvento.objects.create(
        trace_id="trace-entrada",
        direccion="entrada",
        sistema_origen="aws-futbol-api",
        sistema_destino="helpdesk-api",
        endpoint="/api/v2/chain/",
        metodo="POST",
        request_json={
            "meta": {
                "antes": "google-cloud-soporte",
                "origen": "aws-futbol-api",
                "siguiente": None,
            },
            "payload": {
                "geografia": {
                    "continent": {},
                    "country": {},
                    "city": {},
                },
                "soporte": {
                    "solicitante": {},
                    "ticket": {},
                    "comentario": {},
                },
                "futbol": {
                    "equipo": {},
                    "jugador": {},
                    "partido": {},
                },
            },
        },
        estado="exitoso",
    )

    IntegracionEvento.objects.create(
        trace_id="trace-salida",
        direccion="salida",
        sistema_origen="helpdesk-api",
        sistema_destino="aws-final-api",
        endpoint="http://13.59.49.180:8000/api/v2/integracion/",
        metodo="POST",
        request_json={"geografia": {}, "soporte": {}, "futbol": {}},
        estado="exitoso",
    )

    response = client.get("/api/v2/integraciones/eventos/?direccion=entrada&limit=10")

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["trace_id"] == "trace-entrada"
    assert response.data["results"][0]["direccion"] == "entrada"


@pytest.mark.django_db
def test_chain_corrige_payload_doble_y_lo_deja_editable(monkeypatch):
    client = APIClient()

    payload = {
        "meta": {
            "antes": "google-cloud-soporte",
            "origen": "aws-futbol-api",
            "siguiente": "http://fallback-peer/api/v2/chain",
        },
        "payload": {
            "payload": {
                "geografia": {
                    "continent": {},
                    "country": {},
                    "city": {},
                },
                "soporte": {
                    "solicitante": {},
                    "ticket": {},
                    "comentario": {},
                },
            }
        },
    }

    response = client.post("/api/v2/chain/", payload, format="json")

    assert response.status_code == 202
    assert response.data["payload_editado_localmente"] is True


@pytest.mark.django_db
def test_editar_payload_no_agrega_dominios_ausentes():
    client = APIClient()

    IntegracionEvento.objects.create(
        trace_id="trace-no-domains",
        direccion="entrada",
        sistema_origen="api-geografia",
        sistema_destino="helpdesk-api",
        endpoint="/api/v2/chain/",
        metodo="POST",
        request_json={
            "meta": {
                "antes": None,
                "origen": "api-geografia",
                "siguiente": None,
            },
            "payload": {
                "geografia": {
                    "continent": {"id": 1, "name": "Europe"},
                }
            },
        },
        estado="exitoso",
    )

    response = client.patch(
        "/api/v2/integraciones/editar/",
        {
            "trace_id": "trace-no-domains",
            "payload": {
                "geografia": {
                    "country": {"id": 1, "name": "France"},
                }
            },
        },
        format="json",
    )

    assert response.status_code == 200
    assert "futbol" not in response.data["payload"]
    assert "soporte" not in response.data["payload"]
    assert response.data["payload"]["geografia"]["country"]["name"] == "France"


@pytest.mark.django_db
def test_integracion_enviar_hace_merge_y_envia_manual(monkeypatch):
    client = APIClient()

    captured = {}

    class DummyResponse:
        status_code = 200
        ok = True
        text = '{"status": "received"}'

        def json(self):
            return {"status": "received"}

    def fake_post(url, json, headers, timeout):
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        return DummyResponse()

    monkeypatch.setattr("soporte.views.requests.post", fake_post)
    monkeypatch.setenv("CHAIN_OUTBOUND_TOKEN", "secret-chain-token")

    IntegracionEvento.objects.create(
        trace_id="trace-manual",
        direccion="entrada",
        sistema_origen="aws-futbol-api",
        sistema_destino="helpdesk-api",
        endpoint="/api/v2/chain/",
        metodo="POST",
        request_json={
            "meta": {
                "antes": "google-cloud-soporte",
                "origen": "aws-futbol-api",
                "siguiente": "http://13.59.49.180:8000/api/v2/integracion/",
            },
            "payload": {
                "geografia": {
                    "continent": {
                        "continent_id": 1,
                    },
                    "country": {},
                    "city": {},
                }
            },
        },
        estado="exitoso",
    )

    response = client.post(
        "/api/v2/integraciones/enviar/",
        {
            "trace_id": "trace-manual",
            "payload": {
                "soporte": {
                    "ticket": {
                        "ticket_id": 77,
                    }
                }
            },
        },
        format="json",
    )

    assert response.status_code == 200
    assert response.data["forwarded"] is True
    assert captured["url"] == "http://13.59.49.180:8000/api/v2/integracion/"
    assert captured["headers"]["X-Integration-Token"] == "secret-chain-token"
    assert captured["json"]["meta"]["origen"] == "helpdesk-api"
    assert captured["json"]["meta"]["antes"] == "aws-futbol-api"
    assert captured["json"]["meta"]["siguiente"] is None
    assert captured["json"]["payload"]["geografia"]["continent"]["continent_id"] == 1
    assert captured["json"]["payload"]["soporte"]["ticket"]["ticket_id"] == 77
    assert response.data["payload_cadena"]["mi_aporte"]["payload_agregado_manual"]["soporte"]["ticket"]["ticket_id"] == 77


@pytest.mark.django_db
def test_integracion_editar_actualiza_payload_por_trace_id():
    client = APIClient()

    IntegracionEvento.objects.create(
        trace_id="trace-edit",
        direccion="entrada",
        sistema_origen="api-geografia",
        sistema_destino="helpdesk-api",
        endpoint="/api/v2/chain/",
        metodo="POST",
        request_json={
            "meta": {
                "antes": None,
                "origen": "api-geografia",
                "siguiente": None,
            },
            "payload": {
                "geografia": {
                    "continent": {"id": 1, "name": "Europe"},
                    "country": {},
                    "city": {},
                }
            },
        },
        estado="exitoso",
    )

    response = client.patch(
        "/api/v2/integraciones/editar/",
        {
            "trace_id": "trace-edit",
            "payload": {
                "soporte": {
                    "solicitante": {
                        "id": 99,
                        "nombre": "Editado",
                    }
                }
            },
        },
        format="json",
    )

    assert response.status_code == 200
    assert response.data["trace_id"] == "trace-edit"
    assert response.data["payload"]["soporte"]["solicitante"]["nombre"] == "Editado"
