## Fase 2: operación móvil, fotos y administración

La fase 2 se ejecuta como una aplicación separada para no romper la versión anterior:

```bash
uvicorn app.phase2:app --reload
```

Abre `http://localhost:8000`. En un teléfono, usa HTTPS o `localhost`; los navegadores bloquean la cámara en páginas HTTP inseguras.

### Funciones nuevas

- Escáner QR con cámara mediante `html5-qrcode`.
- Subida de fotografías desde móvil.
- Reporte diario: `/phase2/reports/daily`.
- Auditoría de ticket: `/phase2/tickets/{id}/audit`.
- Administración de empleados: `/phase2/admin/employees` (requiere rol `admin`).
- Activar o desactivar empleado: `PATCH /phase2/admin/employees/{id}/active?active=false`.

### Crear un usuario administrador

La creación de usuarios existente sigue disponible en la aplicación principal. Para una instalación nueva, crea el administrador mediante Swagger (`/docs`) usando `POST /employees` con:

```json
{
  "username": "admin",
  "password": "cambia-esta-clave",
  "full_name": "Administrador",
  "role": "admin"
}
```

Después inicia sesión en la interfaz móvil con ese usuario. Las contraseñas se almacenan con bcrypt y las rutas protegidas utilizan JWT.

### PostgreSQL

En `.env` puedes cambiar:

```env
DATABASE_URL=postgresql+psycopg://usuario:clave@localhost:5432/coat_check
UPLOAD_DIR=uploads
```

La versión actual mantiene SQLite como opción por defecto para pruebas locales.
