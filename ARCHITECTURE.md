# Arquitectura del Backend Agape V3

## Principio Fundamental

**Este proyecto usa ARQUITECTURA DE CAPAS SIMPLE con separación de infraestructura.**

❌ **NO es arquitectura hexagonal**
❌ **NO es arquitectura por puertos y adaptadores**
✅ **SÍ es arquitectura de capas simple con ORM**

## Reglas Obligatorias

### 1. Siempre Usar SQLAlchemy ORM

**NUNCA usar raw SQL con `text()`:**

```python
# ❌ INCORRECTO - Raw SQL
result = await session.execute(
    text("SELECT * FROM users WHERE id = :id"),
    {"id": user_id}
)

# ✅ CORRECTO - ORM
result = await session.execute(
    select(User).where(User.id == user_id)
)
user = result.scalar_one_or_none()
```

### 2. Repositorios son OPCIONALES

En arquitectura de capas simple, **los repositorios NO son obligatorios**.

**Opción A - Queries directas en servicios (RECOMENDADO):**
```python
# /application/services/user_service.py
class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user(self, user_id: int) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
```

**Opción B - Con repositorio:**
```python
# /application/repositories/user_repository.py
class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

# /application/services/user_service.py
class UserService:
    def __init__(self, session: AsyncSession):
        self.user_repo = UserRepository(session)

    async def get_user(self, user_id: int) -> Optional[User]:
        return await self.user_repo.get_by_id(user_id)
```

**Ambas opciones son válidas. Elige UNA y mantenla consistente en el código nuevo.**

### 3. Separación de Capas

```
┌─────────────────────────────────────────┐
│  API Layer (FastAPI)                    │
│  /api/v1/                               │
│  - Endpoints                            │
│  - Request/Response handling            │
│  - HTTP status codes                    │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  Application Layer                      │
│  /application/                          │
│  - services/     (lógica de negocio)    │
│  - repositories/ (opcional)             │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  Domain Layer                           │
│  /domain/schemas/                       │
│  - Pydantic schemas (DTOs)              │
│  - Request/Response models              │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  Infrastructure Layer                   │
│  /infrastructure/database/models/       │
│  - SQLAlchemy models                    │
│  - Database schema definitions          │
└─────────────────────────────────────────┘
```

## ¿Qué va en cada capa?

### API Layer (`/api/v1/`)
- **Responsabilidad:** Manejo de HTTP requests y responses
- **Contiene:**
  - Endpoints FastAPI
  - Validación de request bodies
  - Manejo de status codes HTTP
  - Conversión de excepciones a responses HTTP

```python
# /api/v1/users.py
@router.get("/users/{user_id}")
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(get_session)
):
    service = UserService(session)
    user = await service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

### Application Layer (`/application/services/`)
- **Responsabilidad:** Lógica de negocio
- **Contiene:**
  - Servicios con lógica de negocio
  - Queries usando SQLAlchemy ORM
  - Transformación de datos
  - Validaciones de negocio

```python
# /application/services/user_service.py
class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user(self, user_id: int) -> Optional[UserResponse]:
        # Query usando ORM
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            return None

        # Transformar a DTO
        return UserResponse.model_validate(user)
```

### Domain Layer (`/domain/schemas/`)
- **Responsabilidad:** Definición de DTOs (Data Transfer Objects)
- **Contiene:**
  - Pydantic models para requests
  - Pydantic models para responses
  - Validaciones de datos

```python
# /domain/schemas/user.py
from pydantic import BaseModel, EmailStr

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    first_name: str
    last_name: str

    model_config = ConfigDict(from_attributes=True)
```

### Infrastructure Layer (`/infrastructure/database/models/`)
- **Responsabilidad:** Definición de esquema de base de datos
- **Contiene:**
  - SQLAlchemy models
  - Relaciones entre tablas
  - Columnas y tipos de datos

```python
# /infrastructure/database/models/user.py
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False, unique=True)
    first_name = Column(String(100))
    last_name = Column(String(100))

    # Relaciones
    posts = relationship("Post", back_populates="user")
```

## ¿Qué NO es mezcla de capas?

### ✅ CORRECTO - Servicios usando ORM

```python
# /application/services/channel_service.py
class ChannelService:
    async def get_channel(self, channel_id: int):
        # Esto es CORRECTO - el servicio usa ORM
        result = await self.session.execute(
            select(Channel)
            .options(selectinload(Channel.organization))
            .where(Channel.id == channel_id)
        )
        return result.scalar_one_or_none()
```

**Por qué es correcto:**
- El servicio usa la **abstracción del ORM** (SQLAlchemy)
- NO accede directamente a SQL
- Los modelos están en infraestructura
- Las queries están en aplicación

### ❌ INCORRECTO - Raw SQL en servicios

```python
# /application/services/channel_service.py
class ChannelService:
    async def get_channel(self, channel_id: int):
        # Esto es INCORRECTO - raw SQL
        result = await self.session.execute(
            text("SELECT * FROM channels WHERE id = :id"),
            {"id": channel_id}
        )
        return result.fetchone()
```

### ❌ INCORRECTO - Modelos en servicios

```python
# /application/services/channel_service.py

# Esto es INCORRECTO - modelo definido en servicio
class Channel(Base):
    __tablename__ = "channels"
    id = Column(Integer, primary_key=True)
```

## Flujo de Datos

### Request → Response Flow

```
1. Cliente hace request HTTP
   ↓
2. API Layer recibe request
   - Valida formato
   - Extrae parámetros
   ↓
3. API Layer crea Service
   - Pasa AsyncSession al servicio
   ↓
4. Service ejecuta lógica de negocio
   - Hace queries con ORM
   - Transforma datos
   ↓
5. Service retorna DTO (Pydantic model)
   ↓
6. API Layer retorna response HTTP
   - Status code
   - JSON serializado
```

### Ejemplo Completo

```python
# 1. Domain Layer - DTO
# /domain/schemas/channel.py
class ChannelResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]

    model_config = ConfigDict(from_attributes=True)

# 2. Infrastructure Layer - Database Model
# /infrastructure/database/models/channel.py
class Channel(Base):
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)

# 3. Application Layer - Service
# /application/services/channel_service.py
class ChannelService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_channel(self, channel_id: int) -> Optional[ChannelResponse]:
        result = await self.session.execute(
            select(Channel).where(Channel.id == channel_id)
        )
        channel = result.scalar_one_or_none()

        if not channel:
            return None

        return ChannelResponse.model_validate(channel)

# 4. API Layer - Endpoint
# /api/v1/channels.py
@router.get("/channels/{channel_id}", response_model=ChannelResponse)
async def get_channel(
    channel_id: int,
    session: AsyncSession = Depends(get_session)
):
    service = ChannelService(session)
    channel = await service.get_channel(channel_id)

    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    return channel
```

## Creación de Tablas

### ✅ CORRECTO - Usar ORM

```python
from sqlalchemy.ext.asyncio import create_async_engine
from app.infrastructure.database.models import Base

async def create_tables():
    DATABASE_URL = "mysql+aiomysql://..."
    engine = create_async_engine(DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await engine.dispose()
```

### ❌ INCORRECTO - Raw SQL

```python
# NO hacer esto
async def create_tables():
    await session.execute(text("""
        CREATE TABLE channels (
            id INT PRIMARY KEY,
            name VARCHAR(255)
        )
    """))
```

## Migraciones

Para cambios de esquema, usa Alembic:

```bash
# Crear migración
alembic revision --autogenerate -m "Add monthly_donation field"

# Aplicar migración
alembic upgrade head
```

## Checklist para Nuevo Código

Antes de escribir código, verifica:

- [ ] ¿Estoy usando SQLAlchemy ORM? (NO raw SQL)
- [ ] ¿Los modelos están en `/infrastructure/database/models/`?
- [ ] ¿Los DTOs están en `/domain/schemas/`?
- [ ] ¿La lógica de negocio está en `/application/services/`?
- [ ] ¿Los endpoints están en `/api/v1/`?
- [ ] ¿Estoy siendo consistente con el código existente?

## Resumen

| Capa | Ubicación | Responsabilidad | Ejemplo |
|------|-----------|-----------------|---------|
| **API** | `/api/v1/` | HTTP requests/responses | Endpoints FastAPI |
| **Application** | `/application/services/` | Lógica de negocio | Services con queries ORM |
| **Domain** | `/domain/schemas/` | DTOs | Pydantic models |
| **Infrastructure** | `/infrastructure/database/models/` | Database schema | SQLAlchemy models |

**Regla de oro:** Usa SQLAlchemy ORM siempre. Los repositorios son opcionales.
