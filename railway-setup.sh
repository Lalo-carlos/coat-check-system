#!/bin/bash

# Deploy a Railway.app
# 1. Instalar CLI: npm i -g @railway/cli
# 2. railway login
# 3. railway init (en la carpeta del proyecto)
# 4. Este script configura el entorno

set -e

echo "🚂 Configurando para Railway..."

# Crear .env para producción
cat > .env.production << 'EOF'
DATABASE_URL=postgresql+psycopg://${{Postgres.PGUSER}}:${{Postgres.PGPASSWORD}}@${{Postgres.PGHOST}}:${{Postgres.PGPORT}}/${{Postgres.PGDATABASE}}
JWT_SECRET=${{JWT_SECRET}}
JWT_EXPIRE_MINUTES=480
UPLOAD_DIR=/app/uploads
ENVIRONMENT=production
EOF

echo "✅ railway.json y variables configuradas"
echo ""
echo "Próximos pasos:"
echo "1. railway variables set JWT_SECRET 'tu-clave-segura'"
echo "2. railway up"
