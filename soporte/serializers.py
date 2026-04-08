from rest_framework import serializers
from .models import Solicitante, Ticket, Comentario


# ============ V1 SERIALIZERS - VERSIÓN ORIGINAL ============
# Estos serializers mantienen la estructura original sin cambios.
# Se usan en /api/v1/ para compatibilidad hacia atrás.

class SolicitanteSerializer(serializers.ModelSerializer):
    # Serializer simple: convierte el modelo Solicitante a JSON
    class Meta:
        model = Solicitante
        fields = "__all__"  # Incluye todos los campos del modelo


class TicketSerializer(serializers.ModelSerializer):
    # Serializer simple: convierte el modelo Ticket a JSON
    class Meta:
        model = Ticket
        fields = "__all__"  # Incluye todos los campos del modelo


class ComentarioSerializer(serializers.ModelSerializer):
    # Serializer simple: convierte el modelo Comentario a JSON
    class Meta:
        model = Comentario
        fields = "__all__"  # Incluye todos los campos del modelo


# ============ V2 SERIALIZERS - VERSIÓN MEJORADA CON VALIDACIONES ============
# Estos serializers agregan validaciones y campos personalizados.
# Se usan en /api/v2/ con PATCH support y mejor validación de datos.

class SolicitanteSerializerV2(serializers.ModelSerializer):
    # Serializer mejorado: agrega validaciones y calcula campos extras
    full_contact = serializers.SerializerMethodField()

    class Meta:
        model = Solicitante
        # Campos que se devuelven en la respuesta JSON
        fields = ['id', 'nombre', 'email', 'telefono', 'estado', 'full_contact', 'created_at', 'updated_at']
        # Estos campos no se pueden modificar desde la API
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_full_contact(self, obj):
        # Calcula un objeto con toda la información de contacto
        return {
            'email': obj.email,
            'telefono': obj.telefono or 'No especificado',
        }

    def validate_nombre(self, value):
        # Verifica que el nombre no esté vacío o solo con espacios
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("El nombre no puede estar vacío.")
        # Elimina espacios al principio y final
        return value.strip()

    def validate_email(self, value):
        # Verifica que no exista otro usuario con el mismo email
        instance = self.instance
        queryset = Solicitante.objects.filter(email=value)
        # Si estamos editando, excluye el registro actual
        if instance:
            queryset = queryset.exclude(pk=instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("Este email ya está registrado.")
        # Guarda el email en minúsculas
        return value.lower()


class TicketSerializerV2(serializers.ModelSerializer):
    # Serializer mejorado: agrega nombre del solicitante y cuenta de comentarios
    solicitante_nombre = serializers.CharField(source='solicitante.nombre', read_only=True)
    comentarios_count = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = [
            'id', 'solicitante', 'solicitante_nombre', 'asunto', 'descripcion',
            'estado', 'prioridad', 'comentarios_count', 'created_at', 'updated_at', 'closed_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_comentarios_count(self, obj):
        # Cuenta cuántos comentarios tiene este ticket
        return obj.comentarios.count()

    def validate_asunto(self, value):
        # Verifica que el asunto no esté vacío
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("El asunto no puede estar vacío.")
        return value.strip()

    def validate_descripcion(self, value):
        # Verifica que la descripción no esté vacía
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("La descripción no puede estar vacía.")
        return value.strip()


class ComentarioSerializerV2(serializers.ModelSerializer):
    # Serializer mejorado: agrega el asunto del ticket como referencia
    ticket_asunto = serializers.CharField(source='ticket.asunto', read_only=True)

    class Meta:
        model = Comentario
        fields = ['id', 'ticket', 'ticket_asunto', 'autor', 'mensaje', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_mensaje(self, value):
        # Verifica que el mensaje no esté vacío
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("El mensaje no puede estar vacío.")
        return value.strip()


# ============ V2 SERIALIZERS CON DATOS AGREGADOS - PARA MULTI-CLOUD ============
# Estos serializers heredan de V2 y agregan campos para integrar datos de otras APIs.
# Se usan cuando necesitamos combinar información de múltiples sistemas.

class SolicitanteSerializerV2Agregado(SolicitanteSerializerV2):
    # Hereda todo de V2 y agrega un campo para datos externos
    datos_agregados = serializers.SerializerMethodField()

    class Meta(SolicitanteSerializerV2.Meta):
        # Mantiene todos los campos de V2 + el nuevo campo
        fields = SolicitanteSerializerV2.Meta.fields + ['datos_agregados']

    def get_datos_agregados(self, obj):
        # Retorna estructura para datos que vendrán de APIs externas
        # La vista llenará estos datos cuando haya integración multi-cloud
        return {
            'datos_previos': None,  # Se llenará desde otra API
            'timestamp': None,      # Cuándo se obtuvieron los datos
        }


class TicketSerializerV2Agregado(TicketSerializerV2):
    # Hereda todo de V2 y agrega un campo para datos externos
    datos_agregados = serializers.SerializerMethodField()

    class Meta(TicketSerializerV2.Meta):
        # Mantiene todos los campos de V2 + el nuevo campo
        fields = TicketSerializerV2.Meta.fields + ['datos_agregados']

    def get_datos_agregados(self, obj):
        # Retorna estructura para combinar datos de múltiples APIs
        # Es útil para un flujo donde cada sistema procesa el ticket
        return {
            'datos_previos': None,  # Datos de la API anterior
            'datos_locales': {
                'id': obj.id,
                'asunto': obj.asunto,
                'prioridad': obj.prioridad,
            },
            'timestamp': None,
        }
