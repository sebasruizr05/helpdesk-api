from rest_framework import viewsets
from .models import Solicitante, Ticket, Comentario
from .serializers import (
    SolicitanteSerializer,
    TicketSerializer,
    ComentarioSerializer,
)


class SolicitanteViewSet(viewsets.ModelViewSet):
    queryset = Solicitante.objects.all()
    serializer_class = SolicitanteSerializer


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer


class ComentarioViewSet(viewsets.ModelViewSet):
    queryset = Comentario.objects.all()
    serializer_class = ComentarioSerializer

