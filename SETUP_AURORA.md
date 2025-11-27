# Configurar Acceso a Aurora MySQL

Este documento explica cómo configurar Aurora MySQL para ser accesible desde tu máquina local.

## Información del Cluster

- **Endpoint (Writer)**: `database-2.cluster-csf25ija4rhk.eu-south-2.rds.amazonaws.com:3306`
- **Endpoint (Reader)**: `database-2.cluster-ro-csf25ija4rhk.eu-south-2.rds.amazonaws.com:3306`
- **Usuario**: `admin`
- **Región**: `eu-south-2` (Europe - Milan)
- **Base de datos**: `agape_v3`

## Paso 1: Hacer Aurora Públicamente Accesible

1. Ir a **AWS Console → RDS → Databases**
2. Clic en **database-2**
3. Clic en **Modify**
4. En **Connectivity**:
   - **Public access** → Seleccionar **Yes**
5. Clic en **Continue**
6. Seleccionar **Apply immediately**
7. Clic en **Modify DB cluster**

⏱️ Este cambio tarda 5-10 minutos en aplicarse.

## Paso 2: Configurar Security Group

1. En la página del cluster, ir a **Connectivity & security**
2. Clic en el **Security group** (ejemplo: `sg-xxxxx`)
3. Clic en **Edit inbound rules**
4. Clic en **Add rule**:

   | Type | Protocol | Port | Source | Description |
   |------|----------|------|--------|-------------|
   | MySQL/Aurora | TCP | 3306 | My IP | Agape v3 development |

5. Clic en **Save rules**

### Opciones de Source

- **My IP** (Recomendado): Solo tu IP actual puede conectar
- **Custom**: Especificar un rango CIDR específico
- **0.0.0.0/0** (No recomendado): Cualquier IP puede conectar - solo para desarrollo

## Paso 3: Verificar Conectividad

Después de completar los pasos anteriores, ejecutar:

```bash
# Activar entorno virtual
source venv/bin/activate

# Crear base de datos
python create_database.py
```

Si la conexión es exitosa, verás:
```
✓ Database 'agape_v3' created successfully (or already exists)
📋 Available databases:
  - information_schema
  - mysql
  - performance_schema
  - agape_v3
✓ Successfully connected to Aurora MySQL
```

## Paso 4: Ejecutar Migraciones

```bash
# Crear migración inicial
alembic revision --autogenerate -m "Initial migration - users table"

# Aplicar migraciones
alembic upgrade head
```

## Paso 5: Iniciar la Aplicación

```bash
# Modo desarrollo con auto-reload
uvicorn app.main:app --reload

# Modo producción
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

La API estará disponible en:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health

## Troubleshooting

### Error: "Can't connect to MySQL server (timed out)"

**Causas posibles**:
1. Security group no permite tu IP → Revisar regla de entrada
2. Aurora no es públicamente accesible → Revisar configuración
3. Endpoint incorrecto → Verificar endpoint en RDS console

### Error: "Access denied for user 'admin'"

**Causas posibles**:
1. Contraseña incorrecta → Verificar credenciales
2. Usuario no tiene permisos → Verificar permisos en Aurora

### Verificar Security Group desde CLI

```bash
aws ec2 describe-security-groups \
  --region eu-south-2 \
  --filters "Name=group-name,Values=tu-security-group" \
  --query "SecurityGroups[0].IpPermissions"
```

### Verificar tu IP pública

```bash
curl ifconfig.me
```

## Consideraciones de Seguridad

**Para Desarrollo**:
- ✅ Permitir solo tu IP en security group
- ✅ Usar contraseñas fuertes
- ✅ Cambiar `SECRET_KEY` en `.env`

**Para Producción**:
- ❌ NO hacer Aurora públicamente accesible
- ✅ Usar VPC privada con bastion host o VPN
- ✅ Usar AWS Secrets Manager para credenciales
- ✅ Habilitar encryption at rest y in transit
- ✅ Configurar CloudWatch alarms
- ✅ Habilitar backups automáticos

## Script de Setup Completo

Una vez que Aurora sea accesible, ejecutar:

```bash
./setup_production.sh
```

Este script:
1. Crea la base de datos `agape_v3`
2. Genera la migración inicial
3. Aplica migraciones
4. Verifica la conexión

## Revertir Cambios (Hacer Aurora Privado)

Para volver a hacer Aurora privado:

1. **RDS → database-2 → Modify**
2. **Public access** → Seleccionar **No**
3. **Apply immediately**

Y remover la regla del security group que permite puerto 3306 desde internet.
