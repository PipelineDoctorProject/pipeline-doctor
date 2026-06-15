# Deployment Layout

This folder contains production-oriented deployment assets that are not part of
the application source code.

```text
deploy/
  azure/      Azure Container Apps examples, parameters, and environment templates
  terraform/  Terraform source for Azure infrastructure
  ansible/    Ansible post-provision operations and verification
  nginx/      Runtime Nginx configuration for serving the built frontend SPA
```

Local development should continue to use `docker-compose.yml` and Vite dev
server. Production-like deployments should use immutable images, platform
secrets, managed backing services, and the migration job described in
`../docs/environment_modes.md`.

Terraform owns cloud resources. Ansible handles post-provision checks and
operational validation. Keep runtime secrets in GitHub Environments, Azure Key
Vault, or platform secret stores.
