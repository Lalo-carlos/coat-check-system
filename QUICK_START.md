# Guardarropía QR v2.1 - Setup de Producción

## ⚡ Quick Start (30 segundos)

```bash
# 1. Clonar
git clone https://github.com/Lalo-carlos/coat-check-system.git
cd coat-check-system

# 2. Ejecutar setup automático
bash setup-production.sh

# 3. Iniciar servidor
source .venv/bin/activate
uvicorn app.server:app --reload
```

Acceso: **http://localhost:8000**

---

## 🐳 Docker (Recomendado para producción)

```bash
# Con PostgreSQL integrada
docker-compose up -d

# Acceso: http://localhost:8000
# DB: postgres:5432
```

### Variables de entorno (docker-compose.yml)

```yaml
environment:
  JWT_SECRET: tu-clave-super-secreta
  DATABASE_URL: postgresql+psycopg://coat_check:coat_check_pass@postgres:5432/coat_check
```

---

## 🌍 Opciones de despliegue

### Opción 1: Render.com (Lo más fácil)

```bash
bash deploy-full.sh render
```

✅ Gratis + DB Postgres incluida  
✅ Deploy automático desde GitHub  
✅ HTTPS automático  
✅ Logs en tiempo real  

### Opción 2: Railway.app

```bash
bash deploy-full.sh railway
```

✅ Gratis (primeros $5)  
✅ Interfaz visual  
✅ PostgreSQL integrada  
✅ Deploy automático  

### Opción 3: Docker en tu servidor

```bash
bash deploy-full.sh docker
```

✅ Control total  
✅ Costo bajo ($5-20/mes)  
✅ Escalable  
✅ Aislado  

### Opción 4: VPS (Ubuntu)

```bash
bash deploy-full.sh vps
```

✅ Máximo control  
✅ Costo variable  
✅ Nginx + Gunicorn  
✅ SSL automático  

---

## 🔧 Configuración local (desarrollo)

```bash
# 1. Entorno virtual
python3 -m venv .venv
source .venv/bin/activate

# 2. Instalar
pip install -r requirements.txt

# 3. .env
echo 'DATABASE_URL=sqlite:///./coat_check.db' > .env
echo 'JWT_SECRET=dev-secret' >> .env

# 4. Ejecutar
uvicorn app.server:app --reload
```

**URL:** http://localhost:8000  
**API Docs:** http://localhost:8000/docs  
**Admin:** http://localhost:8000/admin  

---

## 👤 Crear usuario admin

### Automático (setup-production.sh)

```bash
bash setup-production.sh
# Te pedirá usuario y contraseña interactivamente
```

### Manual con curl

```bash
curl -X POST http://localhost:8000/employees \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123&full_name=Admin&role=admin"
```

### Manual con Python

```bash
python3 << 'EOF'
from app.database import SessionLocal
from app.models import Employee
from app.security import hash_password

db = SessionLocal()
employee = Employee(
    username="admin",
    password=hash_password("admin123"),
    full_name="Administrador",
    role="admin",
    active=True
)
db.add(employee)
db.commit()
print("✓ Usuario 'admin' creado")
db.close()
EOF
```

---

## 📊 Base de datos

### SQLite (Desarrollo)

```bash
# Auto-crea coat_check.db
uvicorn app.server:app --reload
```

### PostgreSQL (Producción)

#### Opción A: Con Docker

```bash
docker-compose up -d postgres

# Esperar 10 segundos a que inicie
sleep 10

# Verificar conexión
docker exec coat_check_db psql -U coat_check -d coat_check -c "SELECT 1;"
```

#### Opción B: PostgreSQL local/VPS

```bash
# Instalar
sudo apt install -y postgresql postgresql-contrib

# Crear DB
sudo -u postgres psql << 'EOF'
CREATE DATABASE coat_check;
CREATE USER coat_check WITH PASSWORD 'coat_check_pass';
ALTER ROLE coat_check SET client_encoding TO 'utf8';
GRANT ALL PRIVILEGES ON DATABASE coat_check TO coat_check;
EOF

# Configurar en .env
echo 'DATABASE_URL=postgresql+psycopg://coat_check:coat_check_pass@localhost:5432/coat_check' >> .env
```

---

## 🔐 Seguridad para producción

### JWT Secret

```bash
# Generar clave segura
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Copiar resultado a .env
JWT_SECRET=<tu-clave-aqui>
```

### Cambiar credenciales PostgreSQL

```bash
# En docker-compose.yml
services:
  postgres:
    environment:
      POSTGRES_PASSWORD: <tu-password-fuerte>

# En .env
DATABASE_URL=postgresql+psycopg://coat_check:<tu-password>@postgres:5432/coat_check
```

### HTTPS

```bash
# Render/Railway: automático
# Docker: agregar reverse proxy con Let's Encrypt
# VPS: certbot automatizado en setup-production.sh
```

---

## 📈 Monitoreo

### Health check

```bash
curl http://localhost:8000/health
# {"status":"ok","version":"2.1"}
```

### Logs en tiempo real

```bash
# Docker
docker-compose logs -f web

# VPS/Local
tail -f /var/log/coat-check.log
```

### Base de datos

```bash
# Conectar a PostgreSQL
psql postgresql://coat_check:pass@localhost:5432/coat_check

# Contar tickets
SELECT COUNT(*) FROM ticket;

# Ingreso total
SELECT SUM(price) FROM ticket WHERE status='retired';
```

---

## 🚀 Despliegue paso a paso

### 1. Desarrollo local

```bash
bash setup-production.sh
uvicorn app.server:app --reload
```

### 2. Testing

```bash
# Acceder a http://localhost:8000
# Crear usuario
# Registrar prendas
# Escanear QR
# Generar reportes
```

### 3. Producción (elegir uno)

```bash
# Render (lo más fácil)
bash deploy-full.sh render

# O Docker
bash deploy-full.sh docker

# O Railway
bash deploy-full.sh railway

# O VPS
bash deploy-full.sh vps
```

### 4. Verificar

```bash
# Ir a tu URL
https://tu-dominio.com

# Iniciar sesión
Username: admin
Password: (tu contraseña)

# Probar funciones
# - Escanear QR
# - Registrar prendas
# - Generar reportes
```

---

## 📱 Acceso móvil

### En la misma red Wi-Fi

```
http://IP-DEL-PC:8000
```

### Por internet (producción)

```
https://tu-dominio.com
```

### Instalar como app

1. Abrir en navegador móvil
2. Menú → "Instalar app" o "Agregar a pantalla de inicio"
3. ¡Listo!

---

## 🆘 Problemas comunes

### Port 8000 en uso

```bash
# Ver qué está usando el puerto
lsof -i :8000

# Cambiar puerto
uvicorn app.server:app --port 8001
```

### Base de datos no conecta

```bash
# Verificar DATABASE_URL en .env
cat .env | grep DATABASE

# Probar conexión
psql $DATABASE_URL
```

### Cámara QR no funciona

```
✓ Debe estar en HTTPS o localhost
✓ Permitir permisos de cámara
✓ Usar navegador moderno (Chrome, Firefox)
```

### Fotos no se guardan

```bash
# Crear carpeta uploads
mkdir -p uploads
chmod 755 uploads

# Docker: usar volumen en docker-compose.yml
volumes:
  - ./uploads:/app/uploads
```

---

## 📞 Soporte

- **Documentación:** [GitHub Wiki](https://github.com/Lalo-carlos/coat-check-system/wiki)
- **Issues:** [Crear issue](https://github.com/Lalo-carlos/coat-check-system/issues)
- **API Docs:** http://localhost:8000/docs

---

## ✅ Checklist antes de producción

- [ ] JWT_SECRET cambiado
- [ ] Database configurada (PostgreSQL recomendado)
- [ ] Dominio configurado
- [ ] SSL/HTTPS activo
- [ ] Backups configurados
- [ ] Admin user creado
- [ ] Email de recuperación agregado
- [ ] Logs monitoreados
- [ ] Health checks activos
- [ ] Backup base de datos hecho

---

¡Tu guardarropía QR está lista! 🎉
