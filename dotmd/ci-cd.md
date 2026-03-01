# CI/CD Pipeline Instructions

## Build Steps

Always ensure all build steps are fully automated and reproducible. You must never rely on manual intervention for any part of the build process.

### Dependency Management

Always declare all project dependencies explicitly in a manifest file (e.g., `package.json`, `requirements.txt`, `pom.xml`). You must never use implicit or globally installed dependencies.

**Good:**
```json
{
  "name": "my-app",
  "version": "1.0.0",
  "dependencies": {
    "express": "^4.17.1",
    "lodash": "^4.17.21"
  }
}
```

**Bad:**
```javascript
// Implicitly relies on a globally installed 'express' package
const express = require('express');
```

### Build Artifacts

Always produce immutable build artifacts. Once an artifact is built, you must never modify it. Promote the same artifact through all environments.

When building Docker images, always tag them with a unique, immutable identifier (e.g., Git commit SHA, build number). You must never use mutable tags like `latest` for production deployments.

**Good:**
```bash
docker build -t myapp:$(git rev-parse HEAD) .
docker push myapp:$(git rev-parse HEAD)
```

**Bad:**
```bash
docker build -t myapp:latest .
docker push myapp:latest
```

### Unit and Integration Tests

Always execute all unit and integration tests as part of the build pipeline. You must never allow a build to pass if tests fail.

When writing tests, ensure they are deterministic and do not rely on external services unless properly mocked or managed within a test environment.

## Environment Promotion

Always promote code through a defined sequence of environments (e.g., Development -> Staging -> Production). You must never deploy directly to production from development.

### Automated Deployment

Always automate deployments to all environments. You must never perform manual deployments.

When deploying, use infrastructure-as-code (IaC) principles to define and manage environment configurations. You must never configure environments manually.

### Configuration Management

Always separate configuration from code. You must never hardcode environment-specific values in the application codebase.

When configuring applications, use environment variables, configuration files, or a dedicated configuration service. You must never commit sensitive configuration data to version control.

**Good:**
```javascript
// Accessing configuration via environment variable
const DATABASE_URL = process.env.DATABASE_URL;
```

**Bad:**
```javascript
// Hardcoding sensitive configuration
const DATABASE_URL = "jdbc:postgresql://localhost:5432/prod_db";
```

## Secrets Management

Always manage secrets securely. You must never store secrets directly in code, configuration files, or version control.

### Secret Storage

When handling secrets, use a dedicated secrets management solution (e.g., HashiCorp Vault, AWS Secrets Manager, Kubernetes Secrets). You must never store secrets in plain text.

### Access Control

Always implement strict access control for secrets. You must never grant unnecessary permissions to access secrets.

When applications require access to secrets, use identity-based access (e.g., IAM roles, service accounts) with the principle of least privilege. You must never use long-lived static credentials.

## Rollback Strategy

Always have a well-defined and automated rollback strategy for every deployment. You must never deploy without a plan to revert to a previous stable state.

### Fast Rollback

When a deployment fails or introduces critical issues, you must be able to roll back to the previous stable version quickly and automatically. You must never rely on manual steps for rollback.

### Immutable Infrastructure

Always deploy new versions by provisioning new infrastructure or containers and then switching traffic. You must never update existing infrastructure in place, as this complicates rollbacks.

## Zero-Downtime Deployment Patterns

Always implement zero-downtime deployment patterns for production environments. You must never cause service interruptions during deployments.

### Blue/Green Deployment

When deploying critical services, use a Blue/Green deployment strategy. Deploy the new version (Green) alongside the old version (Blue), then switch traffic. You must never directly replace the running application.

### Canary Deployment

When introducing significant changes or new features, use a Canary deployment strategy. Gradually roll out the new version to a small subset of users, monitor its performance, and then proceed with a full rollout. You must never expose all users to a new version simultaneously without prior testing.

### Database Migrations

When performing database schema changes, ensure they are backward-compatible. You must never deploy a new application version that breaks compatibility with the old database schema, especially during a Blue/Green or Canary deployment.

Always separate database schema migrations from application deployments. You must never bundle destructive database changes with application code deployments that require immediate rollback capabilities.

**Good:**
```sql
-- Backward-compatible schema change: add a nullable column
ALTER TABLE users ADD COLUMN email VARCHAR(255);
```

**Bad:**
```sql
-- Destructive schema change: rename a column without backward compatibility
ALTER TABLE users RENAME COLUMN email TO user_email;
```
