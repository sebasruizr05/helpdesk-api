from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
import requests
import logging

from .models import Solicitante, Ticket, Comentario
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
from rest_framework.exceptions import ValidationError

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
        except ProtectedError as e:
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
