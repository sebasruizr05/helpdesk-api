from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
import requests
import logging
import os
import uuid
from copy import deepcopy
from django.utils import timezone

from .models import Solicitante, Ticket, Comentario, IntegracionEvento
from .serializers import (
    SolicitanteSerializer,
    TicketSerializer,
    ComentarioSerializer,
    SolicitanteSerializerV2,
    TicketSerializerV2,
    ComentarioSerializerV2,
    SolicitanteSerializerV2Agregado,
    TicketSerializerV2Agregado,
)

logger = logging.getLogger(__name__)
from django.db.models.deletion import ProtectedError


def _find_in_dict(data, candidate_keys):
    for key in candidate_keys:
        if key in data and data.get(key):
            return data.get(key)
    return None


def _normalize_integration_payload(raw_payload):
    if not isinstance(raw_payload, dict):
        return None

    payload = raw_payload.get("payload")
    data = payload if isinstance(payload, dict) else raw_payload

    solicitante_data = data.get("solicitante") if isinstance(data.get("solicitante"), dict) else {}
    ticket_data = data.get("ticket") if isinstance(data.get("ticket"), dict) else {}

    email = (_find_in_dict(solicitante_data, ["email", "correo"]) or _find_in_dict(data, ["email", "correo"]))
    if not email:
        return None

    nombre = (_find_in_dict(solicitante_data, ["nombre", "name", "full_name"]) or _find_in_dict(data, ["nombre", "name"]) or "Solicitante Externo")
    telefono = (_find_in_dict(solicitante_data, ["telefono", "phone"]) or _find_in_dict(data, ["telefono", "phone"]))

    asunto = (_find_in_dict(ticket_data, ["asunto", "subject", "title"]) or _find_in_dict(data, ["asunto", "subject", "title"]))
    descripcion = (_find_in_dict(ticket_data, ["descripcion", "description", "detalle", "detail"]) or _find_in_dict(data, ["descripcion", "description", "detalle"]))
    if not asunto or not descripcion:
        return None

    prioridad = (_find_in_dict(ticket_data, ["prioridad", "priority"]) or _find_in_dict(data, ["prioridad", "priority"]) or "media")
    if prioridad not in {"baja", "media", "alta", "critica"}:
        prioridad = "media"

    return {
        "solicitante": {
            "nombre": str(nombre).strip(),
            "email": str(email).strip().lower(),
            "telefono": str(telefono).strip() if telefono else None,
        },
        "ticket": {
            "asunto": str(asunto).strip(),
            "descripcion": str(descripcion).strip(),
            "prioridad": prioridad,
        },
    }


def _get_request_json(raw_payload):
    if isinstance(raw_payload, (dict, list)):
        return raw_payload
    return {"raw_value": raw_payload}


def _extract_chain_content(request_json):
    if isinstance(request_json, dict) and isinstance(request_json.get("payload"), dict):
        return deepcopy(request_json["payload"])
    if isinstance(request_json, dict):
        return {
            key: deepcopy(value)
            for key, value in request_json.items()
            if key != "meta"
        }
    return {"raw_value": request_json}


def _normalize_chain_content(chain_content):
    # Corrige payloads doblemente empaquetados y garantiza una estructura compartida editable.
    if not isinstance(chain_content, dict):
        return chain_content, False

    normalized = deepcopy(chain_content)
    edited = False

    while set(normalized.keys()) == {"payload"} and isinstance(normalized.get("payload"), dict):
        normalized = deepcopy(normalized["payload"])
        edited = True

    expected_sections = {
        "geografia": ["continent", "country", "city"],
        "soporte": ["solicitante", "ticket", "comentario"],
        "futbol": ["equipo", "jugador", "partido"],
    }

    if any(section in normalized for section in expected_sections):
        for section, keys in expected_sections.items():
            if not isinstance(normalized.get(section), dict):
                normalized[section] = {}
                edited = True
            for key in keys:
                if key not in normalized[section] or not isinstance(normalized[section][key], dict):
                    normalized[section][key] = {}
                    edited = True

    return normalized, edited


def _build_chain_payload(previous_payload, trace_id, next_url, chain_content):
    previous_meta = previous_payload.get("meta", {}) if isinstance(previous_payload, dict) else {}
    previous_origin = previous_meta.get("origen") if isinstance(previous_meta, dict) else None
    previous_before = previous_meta.get("antes") if isinstance(previous_meta, dict) else None
    before_value = previous_payload
    if next_url and "/integracion/" in next_url:
        before_value = previous_origin or previous_before or "unknown"

    outgoing_payload = deepcopy(previous_payload)
    outgoing_payload["meta"] = {
        "trace_id": trace_id,
        "antes": before_value,
        "origen": "helpdesk-api",
        "siguiente": next_url,
    }
    outgoing_payload["payload"] = chain_content

    outgoing_payload["mi_aporte"] = {
        "api": "helpdesk-api",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "processed_at": timezone.now().isoformat(),
        "keys_recibidas": sorted(chain_content.keys()) if isinstance(chain_content, dict) else [],
        "payload_recibido": chain_content,
    }
    return outgoing_payload


def _build_forward_payload(next_url, chain_payload, chain_content):
    # Para esta integración compartida, el contrato de salida es siempre meta + payload.
    return chain_payload


def _deep_merge_dicts(base, incoming):
    if not isinstance(base, dict) or not isinstance(incoming, dict):
        return deepcopy(incoming)

    result = deepcopy(base)
    for key, value in incoming.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge_dicts(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def _build_send_response(inbound_response, external_response, next_response_json, forward_payload, outgoing_payload):
    inbound_response.update(
        {
            "forwarded": external_response.ok,
            "status_code": external_response.status_code,
            "target_response": next_response_json,
            "payload_enviado": forward_payload,
            "payload_cadena": outgoing_payload,
        }
    )
    return inbound_response


def _send_to_next(trace_id, next_url, outgoing_payload, forward_payload):
    outbound_event = IntegracionEvento.objects.create(
        trace_id=trace_id,
        direccion="salida",
        sistema_origen="helpdesk-api",
        sistema_destino="chain-next",
        endpoint=next_url,
        metodo="POST",
        request_json=forward_payload,
        estado="pendiente",
    )

    headers = {"Content-Type": "application/json"}
    outbound_token = os.getenv("CHAIN_OUTBOUND_TOKEN") or os.getenv("OUTBOUND_TOKEN")
    if outbound_token:
        headers["X-Integration-Token"] = outbound_token

    try:
        timeout_seconds = int(os.getenv("TARGET_TIMEOUT_SECONDS", "10"))
    except (TypeError, ValueError):
        timeout_seconds = 10

    response_payload = {
        "status": "accepted",
        "trace_id": trace_id,
        "next_url": next_url,
        "forwarded": False,
    }

    try:
        external_response = requests.post(
            next_url,
            json=forward_payload,
            headers=headers,
            timeout=timeout_seconds,
        )
        try:
            next_response_json = external_response.json()
        except ValueError:
            next_response_json = {"raw_response": external_response.text}

        outbound_event.status_code = external_response.status_code
        outbound_event.response_json = next_response_json
        outbound_event.estado = "exitoso" if external_response.ok else "fallido"
        outbound_event.save(update_fields=["status_code", "response_json", "estado", "updated_at"])

        response_payload = _build_send_response(
            response_payload,
            external_response,
            next_response_json,
            forward_payload,
            outgoing_payload,
        )
        response_status = status.HTTP_200_OK if external_response.ok else status.HTTP_502_BAD_GATEWAY
        return response_payload, response_status

    except requests.RequestException as exc:
        response_payload.update(
            {
                "error": "Error de comunicación con el siguiente nodo",
                "detalle": str(exc),
                "payload_enviado": forward_payload,
                "payload_cadena": outgoing_payload,
            }
        )
        outbound_event.estado = "fallido"
        outbound_event.status_code = status.HTTP_502_BAD_GATEWAY
        outbound_event.error = str(exc)
        outbound_event.save(update_fields=["estado", "status_code", "error", "updated_at"])
        return response_payload, status.HTTP_502_BAD_GATEWAY


def _persist_normalized_payload(normalized):
    if not normalized:
        return None

    solicitante_data = normalized["solicitante"]
    ticket_data = normalized["ticket"]

    solicitante, _ = Solicitante.objects.get_or_create(
        email=solicitante_data["email"],
        defaults={
            "nombre": solicitante_data["nombre"],
            "telefono": solicitante_data["telefono"],
            "estado": "activo",
        },
    )

    return Ticket.objects.create(
        solicitante=solicitante,
        asunto=ticket_data["asunto"],
        descripcion=ticket_data["descripcion"],
        prioridad=ticket_data["prioridad"],
    )


class IntegracionIngresoAPIView(APIView):
    # Endpoint flexible para recibir JSON desde otra nube sin contrato rígido.
    # Si no se puede normalizar a ticket, igual registra el payload y responde 202.

    def post(self, request):
        inbound_token = os.getenv("INBOUND_TOKEN")
        provided_token = request.headers.get("X-Integration-Token")
        if inbound_token and inbound_token != provided_token:
            return Response(
                {"error": "Token de integración inválido"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        raw_payload = request.data
        request_json = _get_request_json(raw_payload)

        trace_id = None
        source_system = "unknown"
        if isinstance(raw_payload, dict):
            trace_id = raw_payload.get("trace_id")
            source_system = raw_payload.get("source_system") or raw_payload.get("source") or "unknown"

        trace_id = trace_id or f"trace-{uuid.uuid4()}"

        evento = IntegracionEvento.objects.create(
            trace_id=trace_id,
            direccion="entrada",
            sistema_origen=source_system,
            sistema_destino="helpdesk-api",
            endpoint=request.path,
            metodo=request.method,
            request_json=request_json,
            estado="pendiente",
        )

        normalized = _normalize_integration_payload(raw_payload)
        if not normalized:
            evento.estado = "exitoso"
            evento.status_code = status.HTTP_202_ACCEPTED
            evento.response_json = {
                "status": "accepted",
                "trace_id": trace_id,
                "normalizado": False,
                "message": "Payload recibido. Pendiente de mapeo específico.",
            }
            evento.save(update_fields=["estado", "status_code", "response_json", "updated_at"])
            return Response(evento.response_json, status=status.HTTP_202_ACCEPTED)

        ticket = _persist_normalized_payload(normalized)

        response_payload = {
            "status": "accepted",
            "trace_id": trace_id,
            "normalizado": True,
            "ticket_id": ticket.id,
        }

        evento.estado = "exitoso"
        evento.status_code = status.HTTP_202_ACCEPTED
        evento.response_json = response_payload
        evento.save(update_fields=["estado", "status_code", "response_json", "updated_at"])

        return Response(response_payload, status=status.HTTP_202_ACCEPTED)


class ChainAPIView(APIView):
    # Endpoint para recibir, enriquecer y reenviar un JSON encadenado.
    # Si meta.siguiente tiene una URL, el reenvio ocurre en este mismo handler.

    def post(self, request):
        inbound_token = os.getenv("CHAIN_INBOUND_TOKEN") or os.getenv("INBOUND_TOKEN")
        provided_token = request.headers.get("X-Integration-Token")
        if inbound_token and inbound_token != provided_token:
            return Response(
                {"error": "Token de integración inválido"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        raw_payload = request.data
        request_json = _get_request_json(raw_payload)
        meta = request_json.get("meta", {}) if isinstance(request_json, dict) else {}

        configured_previous_url = os.getenv("PREVIOUS_API_URL")
        configured_next_url = os.getenv("NEXT_API_URL")
        trace_id = (
            meta.get("trace_id")
            or request_json.get("trace_id")
            or f"trace-{uuid.uuid4()}"
        )
        source_system = (
            meta.get("origen")
            or request_json.get("source_system")
            or request_json.get("source")
            or "unknown"
        )
        next_url = meta.get("siguiente") or configured_next_url

        inbound_event = IntegracionEvento.objects.create(
            trace_id=trace_id,
            direccion="entrada",
            sistema_origen=source_system,
            sistema_destino="helpdesk-api",
            endpoint=request.path,
            metodo=request.method,
            request_json=request_json,
            estado="pendiente",
        )

        extracted_content = _extract_chain_content(request_json)
        chain_content, payload_edited = _normalize_chain_content(extracted_content)
        outgoing_payload = _build_chain_payload(request_json, trace_id, next_url, chain_content)
        forward_payload = _build_forward_payload(next_url, outgoing_payload, chain_content)
        if configured_previous_url:
            outgoing_payload["meta"]["nodo_anterior_configurado"] = configured_previous_url
        if isinstance(outgoing_payload.get("mi_aporte"), dict):
            outgoing_payload["mi_aporte"]["payload_editado_localmente"] = payload_edited
            outgoing_payload["mi_aporte"]["payload_original"] = extracted_content

        inbound_response = {
            "status": "accepted",
            "trace_id": trace_id,
            "forwarded": False,
            "content_keys": sorted(chain_content.keys()) if isinstance(chain_content, dict) else [],
            "payload_editado_localmente": payload_edited,
            "previous_url": configured_previous_url,
            "next_url": next_url,
            "message": "Payload recibido y almacenado localmente.",
        }

        if next_url:
            send_response, response_status = _send_to_next(
                trace_id,
                next_url,
                outgoing_payload,
                forward_payload,
            )
            inbound_response.update(send_response)
            inbound_response["message"] = "Payload recibido y reenviado automaticamente al siguiente nodo."
            inbound_event.estado = "exitoso" if inbound_response.get("forwarded") else "fallido"
            inbound_event.status_code = inbound_response.get("status_code", response_status)
            inbound_event.response_json = inbound_response
            inbound_event.save(update_fields=["estado", "status_code", "response_json", "updated_at"])
            return Response(inbound_response, status=response_status)

        inbound_event.estado = "exitoso"
        inbound_event.status_code = status.HTTP_202_ACCEPTED
        inbound_event.response_json = inbound_response
        inbound_event.save(update_fields=["estado", "status_code", "response_json", "updated_at"])
        return Response(inbound_response, status=status.HTTP_202_ACCEPTED)


class IntegracionEventosAPIView(APIView):
    # Permite consultar lo recibido y enviado por la API.
    # Filtros disponibles: ?direccion=entrada|salida y ?trace_id=...

    def get(self, request):
        queryset = IntegracionEvento.objects.all().order_by("-created_at")

        direccion = request.query_params.get("direccion")
        if direccion:
            queryset = queryset.filter(direccion=direccion)

        trace_id = request.query_params.get("trace_id")
        if trace_id:
            queryset = queryset.filter(trace_id=trace_id)

        limit = request.query_params.get("limit", "20")
        try:
            limit = max(1, min(int(limit), 100))
        except (TypeError, ValueError):
            limit = 20

        eventos = []
        for evento in queryset[:limit]:
            eventos.append(
                {
                    "id": evento.id,
                    "trace_id": evento.trace_id,
                    "direccion": evento.direccion,
                    "estado": evento.estado,
                    "sistema_origen": evento.sistema_origen,
                    "sistema_destino": evento.sistema_destino,
                    "endpoint": evento.endpoint,
                    "metodo": evento.metodo,
                    "status_code": evento.status_code,
                    "request_json": evento.request_json,
                    "response_json": evento.response_json,
                    "error": evento.error,
                    "created_at": evento.created_at,
                    "updated_at": evento.updated_at,
                }
            )

        return Response(
            {
                "count": len(eventos),
                "results": eventos,
            },
            status=status.HTTP_200_OK,
        )


class IntegracionEnviarAPIView(APIView):
    # Envio manual: toma lo recibido, lo mezcla con tu aporte local y lo envia cuando tu decidas.

    def post(self, request):
        trace_id = request.data.get("trace_id")
        if not trace_id:
            return Response({"error": "Se requiere trace_id"}, status=status.HTTP_400_BAD_REQUEST)

        incoming_event = IntegracionEvento.objects.filter(
            trace_id=trace_id,
            direccion="entrada",
        ).order_by("-created_at").first()
        if not incoming_event:
            return Response({"error": "No existe un evento de entrada para ese trace_id"}, status=status.HTTP_404_NOT_FOUND)

        original_request = incoming_event.request_json if isinstance(incoming_event.request_json, dict) else {}
        original_meta = original_request.get("meta", {}) if isinstance(original_request.get("meta"), dict) else {}
        extracted_content = _extract_chain_content(original_request)
        base_content, base_edited = _normalize_chain_content(extracted_content)

        local_payload = request.data.get("payload", {})
        local_payload = local_payload if isinstance(local_payload, dict) else {}
        merged_content = _deep_merge_dicts(base_content, local_payload)

        next_url = request.data.get("siguiente") or original_meta.get("siguiente") or os.getenv("NEXT_API_URL")
        if not next_url:
            return Response({"error": "Se requiere siguiente o NEXT_API_URL"}, status=status.HTTP_400_BAD_REQUEST)

        outgoing_payload = _build_chain_payload(original_request, trace_id, next_url, merged_content)
        if isinstance(outgoing_payload.get("mi_aporte"), dict):
            outgoing_payload["mi_aporte"]["payload_editado_localmente"] = base_edited or bool(local_payload)
            outgoing_payload["mi_aporte"]["payload_original"] = extracted_content
            outgoing_payload["mi_aporte"]["payload_agregado_manual"] = local_payload

        forward_payload = _build_forward_payload(next_url, outgoing_payload, merged_content)

        response_payload, response_status = _send_to_next(
            trace_id,
            next_url,
            outgoing_payload,
            forward_payload,
        )
        return Response(response_payload, status=response_status)

# ============ V1 VIEWSETS - VERSIÓN ORIGINAL ============
# Estos viewsets manejan las solicitudes HTTP de la API v1.
# Mantienen la estructura original sin cambios.

class SolicitanteViewSet(viewsets.ModelViewSet):
    # CRUD básico: GET, POST, PUT, DELETE
    queryset = Solicitante.objects.all()
    serializer_class = SolicitanteSerializer


class TicketViewSet(viewsets.ModelViewSet):
    # CRUD básico: GET, POST, PUT, DELETE
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer


class ComentarioViewSet(viewsets.ModelViewSet):
    # CRUD básico: GET, POST, PUT, DELETE
    queryset = Comentario.objects.all()
    serializer_class = ComentarioSerializer


# ============ V2 VIEWSETS - VERSIÓN MEJORADA CON PATCH Y FILTROS ============
# Estos viewsets agregan soporte para PATCH (actualización parcial),
# filtros, y métodos personalizados para casos especiales.

class SolicitanteViewSetV2(viewsets.ModelViewSet):
    # ViewSet mejorado para Solicitante
    # - ModelViewSet proporciona automáticamente: GET, POST, PUT, PATCH, DELETE
    # - Agregamos métodos personalizados (@action) para casos especiales
    
    queryset = Solicitante.objects.all()
    serializer_class = SolicitanteSerializerV2

    def get_serializer_class(self):
        # Dependiendo de la acción, usa diferentes serializers
        if self.action == 'retrieve_with_data':
            # Para obtener datos agregados de otras APIs
            return SolicitanteSerializerV2Agregado
        # Por defecto, usa el serializer normal
        return SolicitanteSerializerV2

    @action(detail=True, methods=['get'])
    def retrieve_with_data(self, request, pk=None):
        # Endpoint personalizado: /api/v2/solicitantes/{id}/retrieve_with_data/
        # Retorna el solicitante con campos para datos de otras APIs
        solicitante = self.get_object()
        serializer = self.get_serializer(solicitante)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def activos(self, request):
        # Endpoint personalizado: /api/v2/solicitantes/activos/
        # Retorna solo los solicitantes con estado='activo'
        activos = self.queryset.filter(estado='activo')
        serializer = self.get_serializer(activos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def inactivos(self, request):
        # Endpoint personalizado: /api/v2/solicitantes/inactivos/
        # Retorna solo los solicitantes con estado='inactivo'
        inactivos = self.queryset.filter(estado='inactivo')
        serializer = self.get_serializer(inactivos, many=True)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """Maneja eliminación con validación de integridad referencial."""
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            # Obtiene los tickets asociados al solicitante
            instance = self.get_object()
            tickets_asociados = instance.tickets.all()
            return Response(
                {
                    'error': 'No se puede eliminar el solicitante porque tiene tickets asociados',
                    'detalles': {
                        'cantidad_tickets': tickets_asociados.count(),
                        'tickets': [{'id': t.id, 'asunto': t.asunto} for t in tickets_asociados]
                    }
                },
                status=status.HTTP_409_CONFLICT
            )


class TicketViewSetV2(viewsets.ModelViewSet):
    # ViewSet mejorado para Ticket
    # Agrega filtros por estado/prioridad y acciones personalizadas
    
    queryset = Ticket.objects.all().order_by('-created_at')
    serializer_class = TicketSerializerV2

    def get_serializer_class(self):
        # Usa serializer con datos agregados para acciones especiales
        if self.action in ['retrieve_with_data', 'create_with_data']:
            return TicketSerializerV2Agregado
        return TicketSerializerV2

    def get_queryset(self):
        # Permite filtrar por parámetros en la URL: ?estado=abierto&prioridad=alta
        queryset = Ticket.objects.all().order_by('-created_at')
        
        # Filtro por estado si se proporciona: ?estado=abierto
        estado = self.request.query_params.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
        
        # Filtro por prioridad si se proporciona: ?prioridad=alta
        prioridad = self.request.query_params.get('prioridad')
        if prioridad:
            queryset = queryset.filter(prioridad=prioridad)
        
        return queryset

    @action(detail=True, methods=['get'])
    def retrieve_with_data(self, request, pk=None):
        # Endpoint personalizado: /api/v2/tickets/{id}/retrieve_with_data/
        # Retorna el ticket con campos para datos de otras APIs
        ticket = self.get_object()
        serializer = self.get_serializer(ticket)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def create_with_data(self, request):
        # Endpoint personalizado: /api/v2/tickets/create_with_data/
        # Crea un ticket con datos que vienen de otra API
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=['post'])
    def reenviar_externo(self, request, pk=None):
        # Reenvía un ticket local a una nube externa y guarda trazabilidad completa.
        ticket = self.get_object()
        target_url = os.getenv("TARGET_API_URL")
        if not target_url:
            return Response(
                {"error": "TARGET_API_URL no está configurado"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        trace_id = None
        target_system = "unknown"
        if isinstance(request.data, dict):
            trace_id = request.data.get("trace_id")
            target_system = request.data.get("target_system") or "unknown"
        trace_id = trace_id or f"trace-{uuid.uuid4()}"

        payload = {
            "trace_id": trace_id,
            "source_system": "helpdesk-api",
            "target_system": target_system,
            "operation": "ticket.forward",
            "payload": {
                "ticket_id": ticket.id,
                "asunto": ticket.asunto,
                "descripcion": ticket.descripcion,
                "prioridad": ticket.prioridad,
                "estado": ticket.estado,
                "solicitante": {
                    "id": ticket.solicitante_id,
                    "nombre": ticket.solicitante.nombre,
                    "email": ticket.solicitante.email,
                },
            },
        }

        evento = IntegracionEvento.objects.create(
            trace_id=trace_id,
            direccion="salida",
            sistema_origen="helpdesk-api",
            sistema_destino=target_system,
            endpoint=target_url,
            metodo="POST",
            request_json=payload,
            estado="pendiente",
        )

        headers = {"Content-Type": "application/json"}
        outbound_token = os.getenv("OUTBOUND_TOKEN")
        if outbound_token:
            headers["Authorization"] = f"Bearer {outbound_token}"

        timeout_seconds = 10
        try:
            timeout_seconds = int(os.getenv("TARGET_TIMEOUT_SECONDS", "10"))
        except (TypeError, ValueError):
            timeout_seconds = 10

        try:
            external_response = requests.post(
                target_url,
                json=payload,
                headers=headers,
                timeout=timeout_seconds,
            )
            try:
                response_json = external_response.json()
            except ValueError:
                response_json = {"raw_response": external_response.text}

            evento.status_code = external_response.status_code
            evento.response_json = response_json
            evento.estado = "exitoso" if external_response.ok else "fallido"
            evento.save(update_fields=["status_code", "response_json", "estado", "updated_at"])

            response_payload = {
                "trace_id": trace_id,
                "forwarded": external_response.ok,
                "status_code": external_response.status_code,
                "target_url": target_url,
                "target_response": response_json,
            }
            if external_response.ok:
                return Response(response_payload, status=status.HTTP_200_OK)
            return Response(response_payload, status=status.HTTP_502_BAD_GATEWAY)

        except requests.RequestException as exc:
            evento.estado = "fallido"
            evento.status_code = status.HTTP_502_BAD_GATEWAY
            evento.error = str(exc)
            evento.save(update_fields=["estado", "status_code", "error", "updated_at"])
            return Response(
                {
                    "trace_id": trace_id,
                    "forwarded": False,
                    "error": "Error de comunicación con la nube destino",
                    "detalle": str(exc),
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

    @action(detail=False, methods=['get'])
    def por_estado(self, request):
        # Endpoint personalizado: /api/v2/tickets/por_estado/
        # Agrupa y cuenta tickets por su estado
        estados = {
            'abierto': self.queryset.filter(estado='abierto'),
            'en_progreso': self.queryset.filter(estado='en_progreso'),
            'resuelto': self.queryset.filter(estado='resuelto'),
            'cerrado': self.queryset.filter(estado='cerrado'),
        }
        
        # Construye respuesta con count y lista de tickets por estado
        resultado = {}
        for estado, tickets in estados.items():
            resultado[estado] = {
                'cantidad': tickets.count(),
                'tickets': TicketSerializerV2(tickets, many=True).data
            }
        
        return Response(resultado)

    @action(detail=False, methods=['get'])
    def por_prioridad(self, request):
        # Endpoint personalizado: /api/v2/tickets/por_prioridad/
        # Agrupa y cuenta tickets por su prioridad
        prioridades = {
            'baja': self.queryset.filter(prioridad='baja'),
            'media': self.queryset.filter(prioridad='media'),
            'alta': self.queryset.filter(prioridad='alta'),
            'critica': self.queryset.filter(prioridad='critica'),
        }
        
        # Construye respuesta con count y lista de tickets por prioridad
        resultado = {}
        for prioridad, tickets in prioridades.items():
            resultado[prioridad] = {
                'cantidad': tickets.count(),
                'tickets': TicketSerializerV2(tickets, many=True).data
            }
        
        return Response(resultado)


class ComentarioViewSetV2(viewsets.ModelViewSet):
    # ViewSet mejorado para Comentario
    # Agrega filtros por ticket y acciones personalizadas
    
    queryset = Comentario.objects.all().order_by('-created_at')
    serializer_class = ComentarioSerializerV2

    def get_queryset(self):
        # Permite filtrar comentarios por ticket: ?ticket=5
        queryset = Comentario.objects.all().order_by('-created_at')
        
        # Filtro por ticket si se proporciona: ?ticket=5
        ticket_id = self.request.query_params.get('ticket')
        if ticket_id:
            queryset = queryset.filter(ticket_id=ticket_id)
        
        return queryset

    @action(detail=False, methods=['get'])
    def por_ticket(self, request):
        # Endpoint personalizado: /api/v2/comentarios/por_ticket/?ticket=5
        # Retorna comentarios de un ticket específico
        ticket_id = request.query_params.get('ticket')
        if not ticket_id:
            # Si no se proporciona ticket, retorna error 400
            return Response(
                {'error': 'Se requiere parámetro ticket'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Filtra comentarios del ticket específico
        comentarios = self.queryset.filter(ticket_id=ticket_id)
        serializer = self.get_serializer(comentarios, many=True)
        return Response(serializer.data)
