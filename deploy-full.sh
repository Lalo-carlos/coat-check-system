#!/bin/bash

# Script de despliegue completo
# Uso: bash deploy-full.sh [render|railway|docker|vps]

set -e

echo "🚀 Guardarropía QR - Deploy completo v2.1"
echo ""

PLATFORM=${1:-docker}

case $PLATFORM in

  docker)
    echo "📦 Desplegando con Docker Compose..."
    docker-compose build
    docker-compose up -d
    echo "✅ Servicio iniciado en http://localhost:8000"
    echo "   Base de datos: PostgreSQL"
    echo "   Logs: docker-compose logs -f web"
    ;;

  render)
    echo "🌐 Desplegando a Render.com..."
    echo ""
    echo "1. Ir a https://render.com/dashboard"
    echo "2. Click en 'New' → 'Web Service'"
    echo "3. Conectar este repositorio"
    echo "4. Configurar:"
    echo "   Runtime: Python 3.11"
    echo "   Build: bash build.sh"
    echo "   Start: uvicorn app.server:app --host 0.0.0.0 --port 8000"
    echo "5. Variables de entorno:"
    echo "   JWT_SECRET=<tu-clave>"
    echo "   DATABASE_URL=<postgresql-desde-render>"
    echo ""
    echo "✅ Acceso: https://coat-check-system.onrender.com"
    ;;

  railway)
    echo "🚂 Desplegando a Railway.app..."
    echo ""
    echo "1. railway login"
    echo "2. railway init"
    echo "3. railway variables set JWT_SECRET 'tu-clave'"
    echo "4. railway up"
    echo ""
    echo "✅ Acceso: https://coat-check-system.railway.app"
    ;;

  vps)
    echo "🖥️  Configurando para VPS..."
    echo ""
    echo "Ejecutar en tu VPS (Ubuntu 22.04):"
    echo ""
    echo "cd /var/www"
    echo "git clone https://github.com/Lalo-carlos/coat-check-system.git"
    echo "cd coat-check-system"
    echo "bash setup-production.sh"
    echo ""
    echo "Luego seguir instrucciones de DEPLOYMENT.md sección 'VPS'"
    ;;

  *)
    echo "❌ Plataforma no reconocida"
    echo "Uso: bash deploy-full.sh [render|railway|docker|vps]"
    exit 1
    ;;

esac
