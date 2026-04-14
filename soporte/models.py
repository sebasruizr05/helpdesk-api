from django.db import models


class Solicitante(models.Model):
    ESTADOS = [
        ("activo", "activo"),
        ("inactivo", "inactivo"),
    ]

    nombre = models.CharField(max_length=120)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=30, null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default="activo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nombre} - {self.email}"


class Ticket(models.Model):
    ESTADOS = [
        ("abierto", "abierto"),
        ("en_progreso", "en_progreso"),
        ("resuelto", "resuelto"),
        ("cerrado", "cerrado"),
    ]

    PRIORIDADES = [
        ("baja", "baja"),
        ("media", "media"),
        ("alta", "alta"),
        ("critica", "critica"),
    ]

    solicitante = models.ForeignKey(
        Solicitante,
        on_delete=models.PROTECT,
        related_name="tickets"
    )
    asunto = models.CharField(max_length=200)
    descripcion = models.TextField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default="abierto")
    prioridad = models.CharField(max_length=20, choices=PRIORIDADES, default="media")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Ticket #{self.id} - {self.asunto}"


class Comentario(models.Model):
    AUTORES = [
        ("solicitante", "solicitante"),
        ("agente", "agente"),
    ]

    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name="comentarios"
    )
    autor = models.CharField(max_length=20, choices=AUTORES)
    mensaje = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comentario #{self.id} - Ticket #{self.ticket.id}"


class IntegracionEvento(models.Model):
    DIRECCIONES = [
        ("entrada", "entrada"),
        ("salida", "salida"),
    ]

    ESTADOS = [
        ("pendiente", "pendiente"),
        ("exitoso", "exitoso"),
        ("fallido", "fallido"),
    ]

    trace_id = models.CharField(max_length=120, db_index=True)
    direccion = models.CharField(max_length=20, choices=DIRECCIONES)
    sistema_origen = models.CharField(max_length=120, default="unknown")
    sistema_destino = models.CharField(max_length=120, null=True, blank=True)
    endpoint = models.CharField(max_length=255)
    metodo = models.CharField(max_length=10, default="POST")
    request_json = models.JSONField(default=dict)
    response_json = models.JSONField(null=True, blank=True)
    status_code = models.IntegerField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default="pendiente")
    error = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.direccion.upper()} - {self.trace_id} - {self.estado}"


