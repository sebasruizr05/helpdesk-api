from django.contrib import admin
from .models import Solicitante, Ticket, Comentario, IntegracionEvento

admin.site.register(Solicitante)
admin.site.register(Ticket)
admin.site.register(Comentario)


@admin.register(IntegracionEvento)
class IntegracionEventoAdmin(admin.ModelAdmin):
	list_display = ("id", "trace_id", "direccion", "estado", "status_code", "created_at")
	search_fields = ("trace_id", "sistema_origen", "sistema_destino", "endpoint")
	list_filter = ("direccion", "estado", "created_at")
