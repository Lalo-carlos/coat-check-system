# Guardarropía QR v2.1 - Despliegue en Producción

## 🚀 Opción 1: Docker Compose (Local o VPS)

### Instalación rápida:

```bash
# 1. Clonar y entrar
git clone https://github.com/Lalo-carlos/coat-check-system.git
cd coat-check-system

# 2. Crear .env
cp .env.example .env

# Editar .env con tus valores
nano .env

# 3. Ejecutar con Docker
docker-compose up -d
```

**Acceso:** http://localhost:8000

### Actualizar código:

```bash
git pull origin main
docker-compose up -d --build
```

### Ver logs:

```bash
docker-compose logs -f web
```

### Detener:

```bash
docker-compose down
```

---

## 🌐 Opción 2: Render.com (Gratis con DB)

### Paso 1: Preparar repositorio

```bash
git add .
git commit -m "Production ready"
git push origin main
```

### Paso 2: Crear en Render

1. Ir a [render.com](https://render.com)
2. Click en "New" → "Web Service"
3. Conectar GitHub
4. Seleccionar este repositorio
5. Configurar:
   - **Name:** coat-check-system
   - **Runtime:** Python 3.11
   - **Build Command:** `bash build.sh`
   - **Start Command:** `uvicorn app.server:app --host 0.0.0.0 --port 8000`

### Paso 3: Variables de entorno

```
JWT_SECRET=tu-clave-segura-aqui
JWT_EXPIRE_MINUTES=480
UPLOAD_DIR=/tmp/uploads
```

### Paso 4: Agregar PostgreSQL

1. Crear nuevo "PostgreSQL" en Render
2. Copiar Database URL
3. Agregar como variable:
   ```
   DATABASE_URL=<URL desde Render>
   ```

### Acceso:

```
https://coat-check-system.onrender.com
```

---

## 🚂 Opción 3: Railway.app (Fácil)

### Instalación:

```bash
# 1. Instalar CLI
npm i -g @railway/cli

# 2. Login
railway login

# 3. Inicializar proyecto
railway init

# 4. Seleccionar Python

# 5. Ejecutar setup
bash railway-setup.sh

# 6. Configurar variables
railway variables set JWT_SECRET "tu-clave-segura"

# 7. Deploy
railway up
```

### Acceso:

```
https://coat-check-system.railway.app
```

---

## 🖥️ Opción 4: VPS (AWS, DigitalOcean, Linode)

### Setup en VPS Ubuntu 22.04:

```bash
# 1. Actualizar sistema
sudo apt update && sudo apt upgrade -y

# 2. Instalar dependencias
sudo apt install -y python3.11 python3-pip python3-venv postgresql nginx supervisor

# 3. Clonar proyecto
cd /var/www
sudo git clone https://github.com/Lalo-carlos/coat-check-system.git
cd coat-check-system

# 4. Crear entorno virtual
python3 -m venv .venv
source .venv/bin/activate

# 5. Instalar dependencias
pip install -r requirements.txt

# 6. Configurar PostgreSQL
sudo -u postgres psql << 'EOF'
CREATE DATABASE coat_check;
CREATE USER coat_check WITH PASSWORD 'tu-password-aqui';
ALTER ROLE coat_check SET client_encoding TO 'utf8';
ALTER ROLE coat_check SET default_transaction_isolation TO 'read committed';
ALTER ROLE coat_check SET default_transaction_deferrable TO on;
GRANT ALL PRIVILEGES ON DATABASE coat_check TO coat_check;
EOF

# 7. Crear .env
cp .env.example .env
nano .env  # Editar con PostgreSQL URL

# 8. Inicializar BD
python3 << 'EOF'
from app.database import Base, engine
Base.metadata.create_all(bind=engine)
EOF

# 9. Configurar Supervisor
sudo tee /etc/supervisor/conf.d/coat-check.conf > /dev/null << 'EOF'
[program:coat-check]
directory=/var/www/coat-check-system
command=/var/www/coat-check-system/.venv/bin/uvicorn app.server:app --host 127.0.0.1 --port 8000
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/coat-check.err.log
stdout_logfile=/var/log/coat-check.out.log
EOF

# 10. Configurar Nginx
sudo tee /etc/nginx/sites-available/coat-check > /dev/null << 'EOF'
server {
    listen 80;
    server_name tu-dominio.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /var/www/coat-check-system/static/;
    }

    location /uploads/ {
        alias /var/www/coat-check-system/uploads/;
    }
}
EOF

# 11. Activar sitio
sudo ln -s /etc/nginx/sites-available/coat-check /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# 12. Iniciar supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start coat-check
```

### SSL con Let's Encrypt:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d tu-dominio.com
```

---

## 📊 Monitoreo en producción

### Logs

```bash
# Docker
docker-compose logs -f web

# Systemd
sudo journalctl -u supervisor -f

# VPS directo
tail -f /var/log/coat-check.out.log
```

### Backup de BD PostgreSQL

```bash
# Backup manual
pg_dump coat_check > backup-$(date +%Y%m%d).sql

# Restaurar
psql coat_check < backup-20240101.sql
```

### Backup automático (cron)

```bash
crontab -e

# Añadir:
0 2 * * * pg_dump coat_check | gzip > /backups/coat_check_$(date +\%Y\%m\%d).sql.gz
```

---

## 🔐 Checklist de seguridad para producción

✅ **JWT_SECRET** - Cambiado a una clave segura  
✅ **HTTPS** - Certificado SSL activo  
✅ **Database** - PostgreSQL en producción  
✅ **Backups** - Configurados automáticos  
✅ **CORS** - Restricciones apropiadas  
✅ **Rate limiting** - Si es necesario  
✅ **Logs** - Configurados y monitoreados  
✅ **Updates** - Dependencias actualizadas  
✅ **Firewall** - Solo puertos necesarios  
✅ **Health checks** - Monitoreo activo  

---

## 🆘 Troubleshooting producción

### Error: "Database connection refused"

```bash
# Verificar PostgreSQL
sudo systemctl status postgresql

# Verificar DATABASE_URL en .env
cat .env | grep DATABASE_URL

# Probar conexión
psql -U coat_check -d coat_check -h localhost
```

### Error: "Permission denied on uploads"

```bash
chmod -R 755 uploads/
chown -R www-data:www-data uploads/
```

### Servidor lento

```bash
# Aumentar workers en Gunicorn
gunicorn app.server:app --workers 4 --threads 2 --worker-class gthread

# O en uvicorn
uvicorn app.server:app --workers 4
```

---

## 📱 PWA en producción

La app es instalable en móvil automáticamente:

1. Abrir desde navegador móvil
2. Menú → "Instalar app" o "Agregar a pantalla de inicio"
3. Acceso directo sin navegador

---

## 🎯 Resumen

| Opción | Precio | Facilidad | Escalabilidad |
|--------|--------|-----------|---------------|
| Docker | $5-20/mes | ⭐⭐⭐ | ⭐⭐⭐ |
| Render | Gratis-$7 | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| Railway | Gratis-$10 | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| VPS | $5-50/mes | ⭐⭐ | ⭐⭐⭐⭐ |

**Recomendación:** Render para comenzar, VPS si necesitas control total.
