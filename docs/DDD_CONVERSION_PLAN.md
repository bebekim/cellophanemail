# DDD Conversion Plan

> Research completed: 2026-01-06
> Reference repositories: `~/repositories/sumvibe`, `~/repositories/paymentreminder`

## Current Architecture

**Structure:** Hybrid layered + feature-based (not strict DDD)

```
src/cellophanemail/
├── config/           # Configuration (Pydantic settings)
├── models/           # Piccolo ORM models (mixed concerns)
├── core/             # Email parsing, delivery abstractions
├── features/         # Feature modules (email_protection, shield_addresses, etc.)
├── providers/        # Email provider implementations (SMTP, Postmark)
├── routes/           # Litestar API endpoints
├── services/         # Business logic (auth, billing, email routing)
├── middleware/       # JWT auth middleware
└── app.py            # Litestar application factory
```

**Key issues:**
- Database models are Piccolo ORM tables directly (not separated from domain)
- Business logic scattered between `services/`, `features/`, and `core/`
- No clear port/adapter pattern
- Good feature isolation but no domain layer

---

## Target DDD Architecture

Based on `sumvibe` and `paymentreminder` repositories:

```
app/
├── domain/                    # PURE BUSINESS LOGIC (no DB deps)
│   ├── entity.py              # Aggregate root (Pydantic)
│   ├── value_objects.py       # Immutable value objects
│   └── exceptions.py          # Domain exceptions
│
├── services/
│   ├── ports/                 # ABSTRACT INTERFACES
│   │   └── entity_repository.py   # IEntityRepository (ABC)
│   └── use_cases/             # APPLICATION SERVICES
│       └── entity_service.py  # Business orchestration
│
├── infrastructure/
│   ├── database/              # ORM models (Piccolo)
│   │   └── models.py
│   └── repositories/          # CONCRETE IMPLEMENTATIONS
│       └── entity_repository.py   # PiccoloEntityRepository
│
├── interfaces/                # API LAYER
│   └── web/
│       └── routes.py
│
├── schemas/                   # DTOs for API
└── config/                    # Settings
```

---

## Key DDD Patterns

| Pattern | Implementation |
|---------|---------------|
| **Domain Entity** | Pure Pydantic models with business methods, `create()` factory |
| **Value Object** | Immutable Pydantic models (`frozen=True`) embedded in entities |
| **Repository Port** | Abstract `ABC` interface defining CRUD contract |
| **Repository Adapter** | Concrete class converting domain ↔ ORM models |
| **Application Service** | Orchestrates use cases, receives repos via DI |
| **Domain Exception** | Business rule violations with structured details |

---

## Domain Boundaries

| Domain | Current Location | Entities |
|--------|-----------------|----------|
| **User** | `models/user.py`, `services/auth_service.py` | User, Subscription |
| **EmailProtection** | `features/email_protection/` | AnalysisResult, HorsemanDetection |
| **ShieldAddress** | `features/shield_addresses/`, `models/shield_address.py` | ShieldAddress |
| **EmailDelivery** | `core/email_delivery/`, `providers/` | EmailMessage, DeliveryResult |
| **Billing** | `services/stripe_service.py`, `models/subscription.py` | Subscription, PaymentMethod |

---

## Conversion Phases

### Phase 1: Create Domain Layer
- Extract pure Pydantic entities from current Piccolo models
- Define value objects (e.g., `EmailContent`, `ThreatAssessment`)
- Create domain exceptions

### Phase 2: Define Repository Ports
- Create `IUserRepository`, `IShieldAddressRepository`, etc.
- Define CRUD + domain-specific queries

### Phase 3: Implement Repository Adapters
- Create Piccolo-based implementations
- Handle domain ↔ ORM conversion

### Phase 4: Create Application Services
- Move business logic from `services/` into proper use case services
- Inject repository ports via Litestar DI

### Phase 5: Refactor API Layer
- Routes become thin, delegating to services
- Use schemas/DTOs for request/response

---

## Reference Files

### Domain Entity Example (paymentreminder)
`~/repositories/paymentreminder/app/domain/client.py`

```python
# ABOUTME: Client domain entity - represents a debtor who owes money to an SMB user
# ABOUTME: Pure Pydantic model with business validation, no database dependencies

class ClientData(BaseModel):
    """Value object containing client's core data."""
    name: str = Field(..., min_length=1, max_length=255)
    phone: str = Field(..., min_length=5, max_length=20)
    # ... validation methods

class Client(BaseModel):
    """Client aggregate - a debtor who owes money to an SMB user."""
    id_: int = Field(default=None)
    user_id: int = Field(...)
    data: ClientData = Field(...)
    created_at: datetime
    is_active: bool = Field(default=True)

    # Business logic methods
    def mark_do_not_call(self) -> None: ...
    def deactivate(self) -> None: ...

    @classmethod
    def create(cls, user_id: int, name: str, phone: str, ...) -> "Client":
        """Factory method to create a new Client."""
        ...
```

### Repository Port Example (paymentreminder)
`~/repositories/paymentreminder/app/services/ports/client_repository.py`

```python
# ABOUTME: Client repository port - abstract interface for client data access

class IClientRepository(ABC):
    """Abstract interface for Client data access."""

    @abstractmethod
    def add(self, client: Client) -> Client: ...

    @abstractmethod
    def get(self, client_id: int) -> Optional[Client]: ...

    @abstractmethod
    def get_by_user(self, user_id: int, include_inactive: bool = False) -> List[Client]: ...

    @abstractmethod
    def update(self, client: Client) -> Client: ...

    @abstractmethod
    def delete(self, client_id: int) -> bool: ...
```

### Repository Implementation Example (paymentreminder)
`~/repositories/paymentreminder/app/infrastructure/repositories/client_repository.py`

```python
# ABOUTME: Client repository adapters - SQLAlchemy and InMemory implementations

class SQLAlchemyClientRepository(IClientRepository):
    """SQLAlchemy implementation of IClientRepository."""

    def _to_entity(self, model: ClientModel) -> Client:
        """Convert SQLAlchemy model to domain entity."""
        ...

    def _to_model(self, entity: Client, model: ClientModel = None) -> ClientModel:
        """Convert domain entity to SQLAlchemy model."""
        ...

    def add(self, client: Client) -> Client:
        model = self._to_model(client)
        db.session.add(model)
        db.session.commit()
        return self._to_entity(model)
```

### Application Service Example (paymentreminder)
`~/repositories/paymentreminder/app/services/invoice_management/client_service.py`

```python
# ABOUTME: ClientService - business logic for managing clients (debtors)

class ClientService:
    """Service for managing clients (debtors)."""

    def __init__(self, client_repo: IClientRepository):
        self._client_repo = client_repo  # Dependency injection

    def create_client(self, user_id: int, name: str, phone: str, ...) -> Client:
        client = Client.create(user_id=user_id, name=name, phone=phone, ...)
        return self._client_repo.add(client)

    def get_client(self, client_id: int) -> Client:
        client = self._client_repo.get(client_id)
        if client is None:
            raise EntityNotFoundException("Client", client_id)
        return client
```

### Value Objects Example (sumvibe)
`~/repositories/sumvibe/src/sumvibe/domain/value_objects.py`

```python
# ABOUTME: Value objects for domain entities - immutable data containers

class Emotion(BaseModel):
    """Value object representing an emotion."""
    core: str = Field(..., min_length=1, max_length=50)
    sub: Optional[str] = Field(None, max_length=50)
    intensity: int = Field(..., ge=0, le=10)

    model_config = {"frozen": True}  # Immutable
```

### Domain Exceptions Example (paymentreminder)
`~/repositories/paymentreminder/app/domain/exceptions.py`

```python
# ABOUTME: Domain exceptions - custom exceptions for business rule violations

class DomainException(Exception):
    """Base exception for all domain errors."""
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}

class EntityNotFoundException(DomainException):
    """Raised when a requested entity does not exist."""

class ValidationException(DomainException):
    """Raised when domain validation fails."""
```

---

## Notes

- Both reference repos use Pydantic v2 for domain models
- Repository ports are in `services/ports/` (not `domain/`)
- sumvibe uses async repositories, paymentreminder uses sync
- Both provide `InMemoryRepository` implementations for testing
- Domain entities have `ABOUTME:` comments explaining purpose
