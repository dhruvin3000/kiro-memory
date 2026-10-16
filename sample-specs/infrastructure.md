# Infrastructure & Deployment

## Cloud Provider

We chose **AWS** over GCP and Azure. The team's existing AWS expertise and the 
company's existing AWS billing account made this the default. GCP was evaluated 
for its superior Kubernetes tooling, but migration cost was too high.

## Container Orchestration

**ECS Fargate** was chosen over self-managed Kubernetes (EKS). At our current scale 
(<20 services), Kubernetes adds operational overhead that isn't justified. Fargate 
gives us containers without managing nodes. We will revisit Kubernetes when we 
exceed 50 microservices.

## CI/CD Pipeline

**GitHub Actions** was chosen over Jenkins and CircleCI. Jenkins requires 
self-hosted infrastructure and maintenance. CircleCI is good but adds cost and 
a third-party dependency. GitHub Actions is free for public repos, deeply 
integrated with our repo, and sufficient for our pipeline complexity.

## Secrets Management

**AWS Secrets Manager** over HashiCorp Vault and plain environment variables. 
Plain env vars were rejected due to security risk (leaked in logs, process lists). 
Vault adds infrastructure we'd have to manage. Secrets Manager integrates natively 
with ECS task roles.

## Logging & Observability

**Datadog** was chosen for logs, metrics, and traces over the ELK stack and 
Grafana+Prometheus. ELK is powerful but operationally heavy to self-host. 
Grafana+Prometheus was seriously considered, but Datadog's unified APM + logs 
reduces context-switching when debugging. Cost was accepted as a trade-off.

## CDN

**CloudFront** for static assets and the SPA, over Fastly and Cloudflare. 
Already in our AWS account, no new vendor relationship required.
