import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from soporte.models import Solicitante


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

    response = client.get("/api/solicitantes/")

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

    response = client.post("/api/solicitantes/", data)

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

    response = client.post("/api/solicitantes/", data)

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

    response = client.get("/api/solicitantes/")

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

    response = client.delete(f"/api/solicitantes/{solicitante.id}/")

    assert response.status_code == 204

