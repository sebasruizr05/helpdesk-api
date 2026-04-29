INSERT INTO solicitantes_demo (nombre, email)
VALUES
    ('Ana Ruiz', 'ana@example.com'),
    ('Carlos Mesa', 'carlos@example.com')
ON CONFLICT (email) DO NOTHING;

INSERT INTO tickets_demo (solicitante_id, asunto, estado)
SELECT id, 'No puedo ingresar al portal', 'abierto'
FROM solicitantes_demo
WHERE email = 'ana@example.com'
ON CONFLICT DO NOTHING;

SELECT id, nombre, email
FROM solicitantes_demo
ORDER BY id;

SELECT t.id, s.nombre, t.asunto, t.estado
FROM tickets_demo t
JOIN solicitantes_demo s ON s.id = t.solicitante_id
ORDER BY t.id;
