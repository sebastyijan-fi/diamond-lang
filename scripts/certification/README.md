# Certification scripts

This directory holds the canonical executable scripts used by CI and reproducible
validation workflows.

- `scripts/certification/retry/*`
- `scripts/certification/iniconfig/*`
- `scripts/certification/tomli/*`
- `scripts/certification/dotenv/*`
- `scripts/certification/common/*`

Legacy entry points remain under `certification/real-repos/...` and delegate to
these scripts for command compatibility with historical runbooks.
