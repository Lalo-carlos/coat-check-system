#!/bin/bash

# Guardarropía QR - Setup para producción
# Ejecutar: bash setup-production.sh

set -e

echo "════════════════════════════════════════"
echo "Guardarropía QR v2.1 - Setup Producción"
echo "════════════════════════════════════════"
echo ""

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Validar Python
echo -e "${YELLOW}📦 Validando Python...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 no está instalado. Instálalo primero.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python $(python3 --version | cut -d' ' -f2) detectado${NC}"

# 2. Crear entorno virtual
echo ""
echo -e "${YELLOW}🔧 Creando entorno virtual...${NC}"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo -e "${GREEN}✓ Entorno virtual creado${NC}"
else
    echo -e "${GREEN}✓ Entorno virtual ya existe${NC}"
fi

# 3. Activar entorno
echo ""
echo -e "${YELLOW}🔌 Activando entorno virtual...${NC}"
source .venv/bin/activate
echo -e "${GREEN}✓ Activado${NC}"

# 4. Instalar dependencias
echo ""
echo -e "${YELLOW}📥 Instalando dependencias...${NC}"
pip install --upgrade pip setuptools wheel > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1
echo -e "${GREEN}✓ Dependencias instaladas${NC}"

# 5. Crear .env
echo ""
echo -e "${YELLOW}📝 Configurando .env...${NC}"
if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
# Guardarropía QR - Configuración de producción

# Base de datos SQLite (desarrollo) o PostgreSQL (producción)
DATABASE_URL=sqlite:///./coat_check.db
# DATABASE_URL=postgresql+psycopg://usuario:password@localhost:5432/coat_check

# JWT
JWT_SECRET=tu-clave-super-secreta-aqui-cambiala
JWT_EXPIRE_MINUTES=480

# Almacenamiento
UPLOAD_DIR=uploads

# Configuración de entorno
ENVIRONMENT=development
# ENVIRONMENT=production
EOF
    echo -e "${GREEN}✓ .env creado (modifica con tus valores)${NC}"
else
    echo -e "${GREEN}✓ .env ya existe${NC}"
fi

# 6. Crear carpeta uploads
echo ""
echo -e "${YELLOW}📁 Creando carpeta de almacenamiento...${NC}"
mkdir -p uploads
echo -e "${GREEN}✓ Carpeta 'uploads' lista${NC}"

# 7. Crear base de datos
echo ""
echo -e "${YELLOW}💾 Inicializando base de datos...${NC}"
python3 << 'PYEOF'
from app.database import Base, engine
Base.metadata.create_all(bind=engine)
print("✓ Tablas creadas")
PYEOF

# 8. Crear usuario admin
echo ""
echo -e "${YELLOW}👤 Crear usuario administrador${NC}"
read -p "Usuario (admin): " username
username=${username:-admin}
read -sp "Contraseña: " password
echo ""

if [ -z "$password" ]; then
    password="admin123"
fi

python3 << PYEOF
from app.database import get_db, SessionLocal
from app.models import Employee
from app.security import hash_password

db = SessionLocal()

# Verificar si el usuario ya existe
if db.query(Employee).filter(Employee.username == "$username").first():
    print(f"⚠️  Usuario '{$username}' ya existe")
else:
    employee = Employee(
        username="$username",
        password=hash_password("$password"),
        full_name="Administrador",
        role="admin",
        active=True
    )
    db.add(employee)
    db.commit()
    print(f"✓ Usuario '{$username}' creado correctamente")

db.close()
PYEOF

# 9. Resumen final
echo ""
echo "════════════════════════════════════════"
echo -e "${GREEN}✅ Setup completado${NC}"
echo "════════════════════════════════════════"
echo ""
echo -e "${YELLOW}Próximos pasos:${NC}"
echo ""
echo "1. Configurar variables en .env:"
echo "   nano .env"
echo ""
echo "2. Para desarrollo (SQLite):"
echo "   source .venv/bin/activate"
echo "   uvicorn app.server:app --reload"
echo ""
echo "3. Para producción (PostgreSQL + Docker):"
echo "   docker-compose up -d"
echo ""
echo "4. Acceder:"
echo "   Desarrollo: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo -e "${YELLOW}Credenciales:${NC}"
echo "   Usuario: $username"
echo "   Contraseña: (la que ingresaste)"
echo ""
