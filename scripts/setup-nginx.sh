#!/bin/bash

set -e

echo "🚀 Configurando Nginx + SSL para Tenant Master"
echo "=============================================="

DOMAIN_ADMIN="app.surgir.online"
EMAIL="admin@surgir.online"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo -e "${YELLOW}📋 Verificando requisitos...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker no está instalado${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker instalado${NC}"

if ! docker network inspect tenant-network &> /dev/null; then
    echo -e "${YELLOW}⚠️  Red tenant-network no existe, creándola...${NC}"
    docker network create tenant-network
    echo -e "${GREEN}✅ Red tenant-network creada${NC}"
else
    echo -e "${GREEN}✅ Red tenant-network existe${NC}"
fi

echo ""
echo -e "${YELLOW}📁 Creando directorios...${NC}"
mkdir -p nginx/config/conf.d
mkdir -p nginx/ssl
mkdir -p nginx/logs
mkdir -p nginx/www
echo -e "${GREEN}✅ Directorios creados${NC}"

echo ""
echo -e "${YELLOW}🛑 Deteniendo nginx anterior (si existe)...${NC}"
docker-compose -f nginx/docker-compose.yml down 2>/dev/null || true
echo -e "${GREEN}✅ Nginx anterior detenido${NC}"

echo ""
echo -e "${YELLOW}🚀 Levantando Nginx...${NC}"
cd nginx
docker-compose up -d
cd ..
echo -e "${GREEN}✅ Nginx levantado${NC}"

echo ""
echo -e "${YELLOW}⏳ Esperando a que Nginx esté listo...${NC}"
sleep 5

echo ""
echo -e "${YELLOW}🔒 Obteniendo certificados SSL...${NC}"
echo -e "${YELLOW}⚠️  IMPORTANTE: Asegúrate de que el DNS apunte a este servidor${NC}"
echo ""
echo "Dominios a certificar:"
echo "  - $DOMAIN_ADMIN"
echo "  - *.inv.surgir.online"
echo "  - *.erp.surgir.online"
echo "  - *.shop.surgir.online"
echo "  - *.web.surgir.online"
echo ""
read -p "¿DNS configurado correctamente? (s/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo -e "${RED}❌ Configura el DNS primero y vuelve a ejecutar este script${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}📜 Obteniendo certificado para $DOMAIN_ADMIN...${NC}"
docker-compose -f nginx/docker-compose.yml run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/html \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    -d $DOMAIN_ADMIN

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Certificado para $DOMAIN_ADMIN obtenido${NC}"
else
    echo -e "${RED}❌ Error obteniendo certificado${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}📜 Obteniendo certificados wildcard...${NC}"
echo -e "${YELLOW}⚠️  Los certificados wildcard requieren validación DNS manual${NC}"

for domain in "inv" "erp" "shop" "web"; do
    echo ""
    echo -e "${YELLOW}Certificado para *.${domain}.surgir.online${NC}"
    docker-compose -f nginx/docker-compose.yml run --rm certbot certonly \
        --manual \
        --preferred-challenges=dns \
        --email $EMAIL \
        --agree-tos \
        --no-eff-email \
        -d "${domain}.surgir.online" \
        -d "*.${domain}.surgir.online"
    
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}⚠️  Certificado para ${domain} no obtenido (configúralo después)${NC}"
    fi
done

echo ""
echo -e "${YELLOW}🔄 Reiniciando Nginx con SSL...${NC}"
docker-compose -f nginx/docker-compose.yml restart nginx
echo -e "${GREEN}✅ Nginx reiniciado${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Nginx + SSL configurado${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "URLs disponibles:"
echo "  - https://app.surgir.online (Panel Admin)"
echo "  - https://[cliente].inv.surgir.online (Inventario)"
echo "  - https://[cliente].erp.surgir.online (ERP)"
echo "  - https://[cliente].shop.surgir.online (Shop)"
echo "  - https://[cliente].web.surgir.online (Landing)"
echo ""
