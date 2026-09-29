#!/bin/bash

# Script para desplegar en Render.com
# 1. Crear proyecto en render.com
# 2. Conectar repo de GitHub
# 3. Este script se ejecutará automáticamente

set -e

echo "🚀 Instalando dependencias para Render..."
pip install --upgrade pip
pip install -r requirements.txt

echo "💾 Creando base de datos..."
python << 'EOF'
from app.database import Base, engine
Base.metadata.create_all(bind=engine)
print("✓ Base de datos inicializada")
EOF

echo "✅ Render setup completado"
