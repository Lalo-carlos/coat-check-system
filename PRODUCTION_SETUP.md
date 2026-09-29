# Guardarropía QR - Producción 2.1 (Lista para negocio)

Sistema completo y ejecutable para discotecas con reportes PDF, impresora térmica y sincronización offline.

## Inicio rápido

### 1. Crear entorno virtual
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar ambiente
```bash
cp .env.example .env
```

Editar `.env` si necesitas PostgreSQL:
```env
JWT_SECRET=tu-clave-segura-aqui
JWT_EXPIRE_MINUTES=480
DATABASE_URL=sqlite:///./coat_check.db
UPLOAD_DIR=uploads
```

### 4. Ejecutar el servidor
```bash
uvicorn app.server:app --host 0.0.0.0 --port 8000 --reload
```

Abre en navegador: **http://localhost:8000**

Desde móvil en la misma red: **http://IP-LOCAL:8000**

## Crear primer usuario admin

```bash
curl -X POST http://localhost:8000/employees \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123&full_name=Administrador&role=admin"
```

Luego inicia sesión con:
- Usuario: **admin**
- Contraseña: **admin123**

## Funcionalidades

### Operativa
✅ Escáner QR con cámara del móvil  
✅ Registro de prendas con foto opcional  
✅ Confirmación de entrega  
✅ Tickets perdidos (requiere supervisor)  
✅ Historial de movimientos  
✅ Lista de prendas pendientes  

### Administración
✅ Crear/desactivar empleados  
✅ Gestión de roles (cashier, supervisor, admin)  
✅ Reporte diario con PDF  
✅ Reporte por turno con PDF  
✅ Desglose por método de pago  
✅ Auditoría de tickets  

### Sistema
✅ Autenticación JWT + bcrypt  
✅ Apertura/cierre de caja  
✅ Almacenamiento de fotos  
✅ Sincronización offline  
✅ Generación de PDF  
✅ Soporte para impresora térmica  
✅ Responsive design (móvil-first)  

## Estructura de archivos

```
coat-check-system/
├── app/
│   ├── production.py      # API principal v2.1
│   ├── server.py          # Punto de entrada integrado
│   ├── main.py            # API base v1.0
│   ├── phase2.py          # API v2.0
│   ├── models.py          # Modelos SQLAlchemy
│   ├── schemas.py         # Schemas Pydantic
│   ├── security.py        # JWT + bcrypt
│   ├── services.py        # QR
│   └── database.py        # Conexión BD
├── static/
│   ├── index.html         # Dashboard PWA profesional
│   ├── dashboard.html     # Dashboard alternativo
│   ├── scan.html          # Escáner simple
│   ├── sw.js              # Service Worker
│   └── manifest.json      # Configuración PWA
├── uploads/               # Almacenamiento de fotos
├── requirements.txt
├── .env.example
└── README_PRODUCTION.md
```

## API Endpoints (v2.1)

### Autenticación
- `POST /login` - Iniciar sesión
- `GET /me` - Usuario actual

### Gestión de prendas
- `POST /tickets` - Crear prenda
- `GET /tickets` - Listar todas
- `GET /tickets/pending` - Solo pendientes
- `POST /tickets/scan` - Escanear QR
- `POST /tickets/{id}/return` - Confirmar entrega
- `POST /tickets/{id}/lost` - Marcar perdido (supervisor)
- `GET /tickets/{id}/audit` - Historial

### Caja
- `POST /cash-session/open` - Abrir caja
- `POST /cash-session/{id}/close` - Cerrar caja

### Reportes
- `GET /reports/daily` - Reporte diario JSON
- `GET /reports/daily/pdf` - Descargar PDF
- `GET /reports/shift?start=...&end=...` - Turno JSON
- `GET /reports/shift/pdf?start=...&end=...` - Turno PDF

### Admin
- `GET /admin/employees` - Listar empleados
- `PATCH /admin/employees/{id}/toggle` - Activar/desactivar
- `POST /employees` - Crear empleado

### Sincronización
- `POST /sync/upload` - Sincronizar datos offline
- `GET /sync/status` - Estado de conexión

### Fotos
- `POST /photos` - Subir foto
- `GET /photos/{filename}` - Descargar foto

## Seguridad

- Contraseñas hasheadas con **bcrypt**
- JWT con expiración configurable
- Validación de roles en endpoints sensibles
- QR único e invalidable
- CORS deshabilitado (cambiar si necesitas)
- Validación de archivos (JPG, PNG, WEBP)

## Producción

### PostgreSQL
```env
DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/coat_check
```

### Gunicorn + Nginx
```bash
pip install gunicorn
gunicorn app.server:app --workers 4 --bind 0.0.0.0:8000
```

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Impresora térmica

Para integrar con escáner/impresora:

```python
from python_escpos.printer import Usb

def print_ticket(ticket_id):
    printer = Usb(0x0416, 0x5011)  # Vendor, Product ID
    printer.text(f"Ticket #{ticket_id}\n")
    printer.qr(f"QR:{ticket.qr_token}")
    printer.cut()
```

## Troubleshooting

### No se abre la cámara
- Usar HTTPS o `localhost` / `127.0.0.1`
- Permitir permisos de cámara en navegador

### BD no sincroniza
- Cambiar a PostgreSQL en `.env`
- Resetear BD: eliminar `coat_check.db`

### Reportes PDF sin generar
- Instalar `apt-get install libpq-dev` (Linux)
- Verificar permisos en carpeta `uploads/`

## Soporte y customización

Esta es la **base profesional para guardarropía**. Personaliza según necesites:

- Agregar más métodos de pago
- Integrar con caja registradora
- Conectar con sistemas contables
- Reportes avanzados
- Multi-sucursal
- App nativa Android/iOS

¡Éxito con tu sistema! 🎉
