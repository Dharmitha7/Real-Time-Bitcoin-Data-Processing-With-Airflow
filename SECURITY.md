# Security

## Reporting a vulnerability

If you find a security issue in this project, please open a private security advisory on GitHub
(Security → Advisories → Report a vulnerability) rather than a public issue, so it can be fixed
before details are public.

## How secrets are handled

- **Never in the repo.** Only `.env.example` (placeholders) is committed. Real values live in a
  local `.env` (gitignored) or in AWS Secrets Manager - never in code, `docker-compose.yaml`, or
  Terraform `.tf` files.
- **AWS credentials** are supplied to containers via environment variables
  (`AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY`/`AWS_SESSION_TOKEN`), not a mounted `~/.aws`
  directory. Prefer short-lived/temporary credentials over long-lived access keys.
- **Airflow Connections/Variables** are resolved from AWS Secrets Manager
  (`airflow/connections/*`, `airflow/variables/*`) via the `SecretsManagerBackend`, falling back to
  `.env`/the metastore if a key isn't found there.
- **The Airflow admin password** has no insecure default - it's either set explicitly in `.env` or
  auto-generated and printed once to `airflow-init`'s logs. Rotate it with
  `airflow users reset-password`.
- **Terraform** never manages a secret's value, only the Secrets Manager container resource
  (`aws_secretsmanager_secret`) - values are set out-of-band via the AWS CLI/console, and
  `terraform apply` is never run automatically (see the README's Infrastructure as Code section).

## Historical note

An early commit's message ("Re-add clean docker-compose.yaml without Slack secrets") indicates a
Slack webhook URL was briefly committed and then scrubbed from this repo's history before this
version. No secret is present in the current git history, but the webhook was rotated as a
precaution in case it was ever pushed to a remote before being removed.
