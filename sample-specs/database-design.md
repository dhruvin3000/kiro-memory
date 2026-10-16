# Database Design

## Database Selection

After evaluating multiple options, we decided to use **PostgreSQL** as our primary database.

We considered MongoDB for its flexible schema, but our data is highly relational and 
benefits from ACID transactions. The team also has strong existing PostgreSQL expertise, 
which reduces onboarding time. MySQL was rejected because of weaker JSON support and 
licensing concerns.

## ORM Choice

We chose **SQLAlchemy** over Django ORM and raw SQL. The rationale:
- We are not using Django, so Django ORM is off the table.
- Raw SQL was rejected because it makes migrations painful at scale.
- SQLAlchemy gives us the flexibility of the Core API when needed plus the convenience 
  of the ORM for standard CRUD.

## Connection Pooling

We decided to use **PgBouncer** for connection pooling rather than relying solely on 
SQLAlchemy's built-in pool. At our expected load (500+ concurrent users), SQLAlchemy's 
pool alone caused connection exhaustion in load tests. PgBouncer in transaction mode 
handles this efficiently.

## Schema Migrations

**Alembic** was chosen for schema migrations. Flyway was considered but rejected because 
it requires Java on the server. Alembic integrates directly with SQLAlchemy models, 
making it the natural choice.
