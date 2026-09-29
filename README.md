# Guardarropía QR avanzada

Este proyecto es una versión profesional del MVP de guardarropía para discotecas. Incluye autenticación JWT, seguridad para QR, gestión de tickets y cierre de caja.

## Requisitos

- Python 3.11+
- PostgreSQL opcional para producción
- SQLite por defecto para arrancar rápido

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuración

Copia el archivo `.env.example` a `.env` y ajusta los valores.

```bash
cp .env.example .env
```

## Ejecutar

```bash
uvicorn app.main:app --reload
```

Abrir:
- http://localhost:8000
- Swagger: http://localhost:8000/docs

## Usuarios demo

Se puede crear un usuario con rol `cashier` y luego iniciar sesión por `/login`.

Ejemplo de usuario:
```
username: cashier1
password: 1234
```

## Funcionalidades

- Login con JWT
- Registro de empleados con roles
- Registro de prendas con percha, descripción, precio, pago y notas
- Generación de QR único de un solo uso
- Escaneo por token
- Entrega confirmada y invalidación del QR
- Tickets perdidos con aprobación de supervisor
- Historial de movimientos
- Cierre de caja por turno
- Resumen de caja

## Seguridad

- Las contraseñas se guardan con hash bcrypt
- El QR contiene un token aleatorio y se invalida al entregar la prenda
- Las operaciones sensibles requieren autenticación
- El estado `lost` exige validación de supervisor

## Próximos pasos

- PWA con cámara para escaneo real desde móvil
- PostgreSQL para producción
- impresión térmica
- panel administrativo completo
- control de puestos y casilleros
- modo sin internet / Wi‑Fi local
