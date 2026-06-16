# Ansible Operations

Ansible is used after Terraform has created infrastructure. In this project it is best used for operational checks, release verification, and environment-specific configuration validation.

Terraform owns Azure resources. Ansible should not duplicate Terraform resource creation.

## Layout

- `inventories/dev`: Development inventory.
- `inventories/prod`: Production inventory.
- `playbooks/site.yml`: Default post-provision operational playbook.
- `playbooks/verify.yml`: Safe verification playbook for CI/CD.
- `roles/opssight_runtime`: Shared runtime validation tasks.

## Local Commands

```bash
ansible-playbook deploy/ansible/playbooks/verify.yml -i deploy/ansible/inventories/dev/hosts.ini
ansible-playbook deploy/ansible/playbooks/site.yml -i deploy/ansible/inventories/prod/hosts.ini
```

For Azure Container Apps, most actions should eventually call Azure CLI/API from GitHub Actions or use Terraform outputs. Keep this layer focused on repeatable operational checks.
