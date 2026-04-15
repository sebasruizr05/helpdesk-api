"""
URL configuration for helpdesk project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from soporte.views import (
    # V1
    SolicitanteViewSet,
    TicketViewSet,
    ComentarioViewSet,
    # V2
    SolicitanteViewSetV2,
    TicketViewSetV2,
    ComentarioViewSetV2,
    IntegracionIngresoAPIView,
    ChainAPIView,
    IntegracionEventosAPIView,
)

# ============ V1 ROUTER ============
router_v1 = DefaultRouter()
router_v1.register(r"solicitantes", SolicitanteViewSet, basename="solicitante-v1")
router_v1.register(r"tickets", TicketViewSet, basename="ticket-v1")
router_v1.register(r"comentarios", ComentarioViewSet, basename="comentario-v1")

# ============ V2 ROUTER ============
router_v2 = DefaultRouter()
router_v2.register(r"solicitantes", SolicitanteViewSetV2, basename="solicitante-v2")
router_v2.register(r"tickets", TicketViewSetV2, basename="ticket-v2")
router_v2.register(r"comentarios", ComentarioViewSetV2, basename="comentario-v2")

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    
    # API v1 (Original)
    path("api/v1/", include(router_v1.urls)),
    
    # API v2 (Mejorada)
    path("api/v2/", include(router_v2.urls)),
    path("api/v2/integraciones/ingreso/", IntegracionIngresoAPIView.as_view(), name="integracion-ingreso"),
    path("api/v2/integraciones/eventos/", IntegracionEventosAPIView.as_view(), name="integracion-eventos"),
    path("api/v2/chain/", ChainAPIView.as_view(), name="chain"),
    
    # Documentación OpenAPI (Swagger)
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    
    # DRF Auth
    path("api-auth/", include("rest_framework.urls")),
]
