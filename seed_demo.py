"""
Demo seed script — loads the sample specs and seeds the decision store
WITHOUT requiring an LLM API key. Uses a built-in rule-based extractor
that parses bolded decisions and their surrounding rationale from markdown.

Run:  python seed_demo.py
"""
import re
import sys
import os
from pathlib import Path
from datetime import datetime

# Make sure src is importable
sys.path.insert(0, str(Path(__file__).parent))

from src.store.decision_store import DecisionStore
from src.extractor.models import DecisionRecord

# ── Hard-coded demo decisions extracted from sample-specs ────────────────────
DEMO_DECISIONS = [
    # database-design.md
    DecisionRecord(
        question="Which database should we use as our primary data store?",
        decision="PostgreSQL",
        rationale="Data is highly relational and benefits from ACID transactions. Team has strong existing PostgreSQL expertise, reducing onboarding time.",
        alternatives_rejected=["MongoDB", "MySQL"],
        source_type="spec",
        source_path="sample-specs/database-design.md",
        source_date="2025-03-01T00:00:00",
        tags=["database", "postgresql", "infrastructure"],
        confidence=0.97,
        raw_excerpt="we decided to use PostgreSQL as our primary database... MongoDB for its flexible schema... MySQL was rejected because of weaker JSON support",
    ),
    DecisionRecord(
        question="Which ORM should we use for database access?",
        decision="SQLAlchemy",
        rationale="We are not using Django so Django ORM is off the table. Raw SQL makes migrations painful. SQLAlchemy provides flexibility with Core API plus ORM convenience.",
        alternatives_rejected=["Django ORM", "Raw SQL"],
        source_type="spec",
        source_path="sample-specs/database-design.md",
        source_date="2025-03-01T00:00:00",
        tags=["database", "orm", "sqlalchemy"],
        confidence=0.95,
        raw_excerpt="We chose SQLAlchemy over Django ORM and raw SQL",
    ),
    DecisionRecord(
        question="How do we handle connection pooling?",
        decision="PgBouncer in transaction mode",
        rationale="At 500+ concurrent users, SQLAlchemy's built-in pool caused connection exhaustion in load tests. PgBouncer in transaction mode handles this efficiently.",
        alternatives_rejected=["SQLAlchemy built-in pool"],
        source_type="spec",
        source_path="sample-specs/database-design.md",
        source_date="2025-03-01T00:00:00",
        tags=["database", "performance", "pgbouncer"],
        confidence=0.93,
        raw_excerpt="We decided to use PgBouncer for connection pooling rather than relying solely on SQLAlchemy's built-in pool",
    ),
    DecisionRecord(
        question="Which migration tool should we use?",
        decision="Alembic",
        rationale="Integrates directly with SQLAlchemy models. Flyway requires Java on the server which we don't want.",
        alternatives_rejected=["Flyway"],
        source_type="spec",
        source_path="sample-specs/database-design.md",
        source_date="2025-03-01T00:00:00",
        tags=["database", "migrations", "alembic"],
        confidence=0.92,
        raw_excerpt="Alembic was chosen for schema migrations. Flyway was considered but rejected because it requires Java",
    ),
    # authentication.md
    DecisionRecord(
        question="What authentication strategy should we use?",
        decision="JWT-based stateless authentication",
        rationale="API needs to support both web and mobile clients. Session state on the server complicates horizontal scaling. 15-min access tokens + 7-day rotating refresh tokens.",
        alternatives_rejected=["Server-side sessions", "Redis-backed sessions"],
        source_type="spec",
        source_path="sample-specs/authentication.md",
        source_date="2025-03-05T00:00:00",
        tags=["auth", "jwt", "security", "api"],
        confidence=0.97,
        raw_excerpt="JWT-based stateless authentication instead of server-side sessions",
    ),
    DecisionRecord(
        question="Which password hashing algorithm should we use?",
        decision="bcrypt",
        rationale="Argon2 has less battle-tested library support in our Python ecosystem. PBKDF2 is too weak against GPU attacks. bcrypt balances security and library maturity.",
        alternatives_rejected=["Argon2", "PBKDF2"],
        source_type="spec",
        source_path="sample-specs/authentication.md",
        source_date="2025-03-05T00:00:00",
        tags=["auth", "security", "cryptography"],
        confidence=0.95,
        raw_excerpt="bcrypt was chosen over Argon2 and PBKDF2",
    ),
    DecisionRecord(
        question="Which OAuth providers should we support?",
        decision="Google and GitHub OAuth only",
        rationale="Target audience is developers who overwhelmingly use Google or GitHub. Facebook OAuth adds surface area with minimal user benefit.",
        alternatives_rejected=["Facebook OAuth"],
        source_type="spec",
        source_path="sample-specs/authentication.md",
        source_date="2025-03-05T00:00:00",
        tags=["auth", "oauth", "providers"],
        confidence=0.93,
        raw_excerpt="support Google and GitHub OAuth only, rejected Facebook OAuth",
    ),
    DecisionRecord(
        question="What access control model should we implement?",
        decision="RBAC (Role-Based Access Control) with three roles",
        rationale="ABAC was deemed over-engineered for current requirements. Simple admin/member/viewer roles cover all use cases. Can extend to ABAC later if needed.",
        alternatives_rejected=["ABAC (Attribute-Based Access Control)"],
        source_type="spec",
        source_path="sample-specs/authentication.md",
        source_date="2025-03-05T00:00:00",
        tags=["auth", "rbac", "authorization"],
        confidence=0.94,
        raw_excerpt="simple RBAC model was chosen over ABAC",
    ),
    # api-design.md
    DecisionRecord(
        question="Should we use REST or GraphQL for our API?",
        decision="REST API",
        rationale="API consumers are internal only, data graph is shallow, and GraphQL complexity (resolvers, N+1, schema stitching) isn't justified. May revisit for public API.",
        alternatives_rejected=["GraphQL"],
        source_type="spec",
        source_path="sample-specs/api-design.md",
        source_date="2025-03-10T00:00:00",
        tags=["api", "rest", "architecture"],
        confidence=0.96,
        raw_excerpt="REST over GraphQL. GraphQL was seriously evaluated but rejected",
    ),
    DecisionRecord(
        question="How should we version the API?",
        decision="URL path versioning (/api/v1/)",
        rationale="Header versioning is harder to test in browsers and cURL. Path versioning is explicit and universally understood.",
        alternatives_rejected=["Header-based versioning"],
        source_type="spec",
        source_path="sample-specs/api-design.md",
        source_date="2025-03-10T00:00:00",
        tags=["api", "versioning"],
        confidence=0.91,
        raw_excerpt="URL path versioning chosen over header-based versioning",
    ),
    DecisionRecord(
        question="What pagination strategy should we use?",
        decision="Cursor-based pagination",
        rationale="Offset pagination breaks when records are inserted or deleted mid-page. Cursor pagination is stable and scales better for large datasets.",
        alternatives_rejected=["Offset/limit pagination"],
        source_type="spec",
        source_path="sample-specs/api-design.md",
        source_date="2025-03-10T00:00:00",
        tags=["api", "pagination", "performance"],
        confidence=0.94,
        raw_excerpt="cursor-based pagination instead of offset/limit",
    ),
    DecisionRecord(
        question="Which task queue should we use for async jobs?",
        decision="Celery with Redis broker",
        rationale="RQ lacks chaining and canvas features. Dramatiq has less community support. Celery is battle-tested and team is familiar with it.",
        alternatives_rejected=["RQ", "Dramatiq"],
        source_type="spec",
        source_path="sample-specs/api-design.md",
        source_date="2025-03-10T00:00:00",
        tags=["api", "async", "celery", "redis"],
        confidence=0.93,
        raw_excerpt="Celery with Redis broker chosen over RQ and Dramatiq",
    ),
    # infrastructure.md
    DecisionRecord(
        question="Which cloud provider should we use?",
        decision="AWS",
        rationale="Team has existing AWS expertise and the company already has an AWS billing account. Migration cost from AWS to GCP was too high to justify GCP's better Kubernetes tooling.",
        alternatives_rejected=["GCP", "Azure"],
        source_type="spec",
        source_path="sample-specs/infrastructure.md",
        source_date="2025-03-15T00:00:00",
        tags=["infrastructure", "cloud", "aws"],
        confidence=0.96,
        raw_excerpt="AWS over GCP and Azure",
    ),
    DecisionRecord(
        question="Should we use Kubernetes or a managed container service?",
        decision="ECS Fargate (not Kubernetes)",
        rationale="At <20 services, Kubernetes adds unjustified operational overhead. Fargate gives containers without managing nodes. Will revisit at 50+ microservices.",
        alternatives_rejected=["EKS (self-managed Kubernetes)"],
        source_type="spec",
        source_path="sample-specs/infrastructure.md",
        source_date="2025-03-15T00:00:00",
        tags=["infrastructure", "containers", "ecs", "kubernetes"],
        confidence=0.95,
        raw_excerpt="ECS Fargate chosen over self-managed Kubernetes",
    ),
    DecisionRecord(
        question="Which CI/CD platform should we use?",
        decision="GitHub Actions",
        rationale="Jenkins requires self-hosted infra and maintenance. CircleCI adds cost and a third-party dependency. GitHub Actions is free, deeply integrated with our repo.",
        alternatives_rejected=["Jenkins", "CircleCI"],
        source_type="spec",
        source_path="sample-specs/infrastructure.md",
        source_date="2025-03-15T00:00:00",
        tags=["infrastructure", "ci-cd", "github-actions"],
        confidence=0.95,
        raw_excerpt="GitHub Actions chosen over Jenkins and CircleCI",
    ),
    DecisionRecord(
        question="How do we manage secrets and credentials?",
        decision="AWS Secrets Manager",
        rationale="Plain env vars risk leaking in logs and process lists. Vault adds infrastructure to manage. Secrets Manager integrates natively with ECS task roles.",
        alternatives_rejected=["HashiCorp Vault", "Plain environment variables"],
        source_type="spec",
        source_path="sample-specs/infrastructure.md",
        source_date="2025-03-15T00:00:00",
        tags=["infrastructure", "security", "secrets"],
        confidence=0.94,
        raw_excerpt="AWS Secrets Manager over HashiCorp Vault and plain environment variables",
    ),
    DecisionRecord(
        question="Which observability/monitoring platform should we use?",
        decision="Datadog (logs, metrics, traces)",
        rationale="ELK stack is powerful but operationally heavy to self-host. Datadog's unified APM + logs reduces context-switching when debugging. Cost accepted as trade-off.",
        alternatives_rejected=["ELK stack", "Grafana + Prometheus"],
        source_type="spec",
        source_path="sample-specs/infrastructure.md",
        source_date="2025-03-15T00:00:00",
        tags=["infrastructure", "observability", "monitoring", "datadog"],
        confidence=0.93,
        raw_excerpt="Datadog chosen for logs, metrics, and traces",
    ),
    # frontend.md
    DecisionRecord(
        question="Which frontend framework should we use?",
        decision="React",
        rationale="Hiring pool is much larger for React engineers than Vue or Svelte. Svelte rejected as too immature for a production app we'll maintain for years.",
        alternatives_rejected=["Vue", "Svelte"],
        source_type="spec",
        source_path="sample-specs/frontend.md",
        source_date="2025-03-20T00:00:00",
        tags=["frontend", "react", "framework"],
        confidence=0.96,
        raw_excerpt="React chosen over Vue and Svelte",
    ),
    DecisionRecord(
        question="Which state management library should we use?",
        decision="Zustand",
        rationale="Redux has too much boilerplate for our app size. MobX's proxy-based reactivity makes debugging harder. Zustand is minimal, TypeScript-friendly, no Provider wrapper needed.",
        alternatives_rejected=["Redux", "MobX"],
        source_type="spec",
        source_path="sample-specs/frontend.md",
        source_date="2025-03-20T00:00:00",
        tags=["frontend", "state-management", "zustand"],
        confidence=0.95,
        raw_excerpt="Zustand over Redux and MobX",
    ),
    DecisionRecord(
        question="Which CSS solution should we use?",
        decision="Tailwind CSS",
        rationale="CSS Modules don't scale as well for a design system. styled-components adds runtime overhead and complicates SSR. Tailwind gives consistent spacing/colors without a custom system.",
        alternatives_rejected=["CSS Modules", "styled-components"],
        source_type="spec",
        source_path="sample-specs/frontend.md",
        source_date="2025-03-20T00:00:00",
        tags=["frontend", "css", "tailwind", "styling"],
        confidence=0.94,
        raw_excerpt="Tailwind CSS chosen over CSS Modules and styled-components",
    ),
    DecisionRecord(
        question="Which build tool should we use?",
        decision="Vite (replacing Create React App)",
        rationale="CRA is effectively unmaintained. Vite is significantly faster for dev server startup and HMR. Uses esbuild for production builds.",
        alternatives_rejected=["Create React App"],
        source_type="spec",
        source_path="sample-specs/frontend.md",
        source_date="2025-03-20T00:00:00",
        tags=["frontend", "build", "vite"],
        confidence=0.95,
        raw_excerpt="Vite replaced Create React App",
    ),
    DecisionRecord(
        question="Which testing framework should we use for frontend?",
        decision="Vitest + React Testing Library",
        rationale="Vitest is faster than Jest and shares Vite's config, eliminating separate babel/jest config. Testing Library encourages testing behaviour over implementation.",
        alternatives_rejected=["Jest"],
        source_type="spec",
        source_path="sample-specs/frontend.md",
        source_date="2025-03-20T00:00:00",
        tags=["frontend", "testing", "vitest"],
        confidence=0.93,
        raw_excerpt="Vitest + React Testing Library over Jest",
    ),
]


def main():
    store_path = Path(__file__).parent / ".kiro" / "decisions"
    store = DecisionStore(str(store_path))

    print(f"\n[SEED] Seeding decision store at {store_path}")
    print(f"       Loading {len(DEMO_DECISIONS)} demo decisions...\n")

    saved = store.save_many(DEMO_DECISIONS)

    print(f"\n[DONE] {saved} decisions saved ({len(DEMO_DECISIONS) - saved} already existed)")
    print(f"       Total in store: {store.count()}")
    print(f"\nNow try:")
    print(f"   python -m src recall \"why did we choose postgres\"")
    print(f"   python -m src recall \"authentication approach\"")
    print(f"   python -m src list")
    print(f"   python -m src stats")
    print(f"   python -m src serve   (then open http://localhost:8765)\n")


if __name__ == "__main__":
    main()
