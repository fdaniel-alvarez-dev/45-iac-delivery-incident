# Security

## Controls Implemented (Demo Scope)
- **No secrets committed**: `.gitignore` blocks common secret files (`.env*`, keys, credentials, `*.tfstate`).
- **No token printing**: CLI avoids echoing environment variables and never reads `GITHUB_TOKEN`.
- **Least privilege by design (conceptual)**:
  - Delivery checks enforce separation: “plan” vs “apply”
  - Apply is gated behind approval-like signals in the example pipeline
- **Auditability**:
  - Report links findings to concrete inputs under `examples/`
  - Guardrails are implemented as deterministic checks that can run in CI

## Recommended Operational Guardrails
- Protect main branch; require PR reviews and status checks.
- Require a “plan” artifact and policy checks before any “apply”.
- Enforce tagging standards: `owner`, `environment`, `change_id`.
- Require postmortems for sev-1/sev-2 incidents and track follow-ups to closure.

## Secrets Handling
- Do not store secrets in `examples/`. Use redacted/sanitized values only.
- Use environment variables locally only (never commit `.env*`).
- Treat Terraform state as sensitive; do not commit it. Use remote state + encryption in real systems.
