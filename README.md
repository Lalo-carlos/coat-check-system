# Sistema de guardarropía con QR para discoteca

Este proyecto es un MVP funcional en Python con FastAPI para gestionar prendas.

## Qué incluye

- Login de empleados
- Registro de prendas
- Generación de QR único
- Búsqueda por token QR para devolución
- Lista de pendientes
- Cierre de caja
- Historial de movimientos
- Interfaz web simple en el navegador

## Ejecutar

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Abrir:
- http://localhost:8000
- Swagger: http://localhost:8000/docs

## Seguridad

Los QR usan un token aleatorio generado con `secrets.token_urlsafe(24)`. Al entregar la prenda, el token se invalida para evitar reutilización.

## Siguientes pasos recomendados

- JWT para autenticación real
- PostgreSQL en producción
- PWA para escaneo desde móvil
- impresión térmica
- control por caja y turno
- incidencias y supervisión
