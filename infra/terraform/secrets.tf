# Resource-only: Terraform manages the secret *container*, never its value.
# These names must match what Phase 3's manual `aws secretsmanager
# create-secret` commands already created - import them instead of letting
# Terraform try (and fail) to create ones that already exist:
#
#   terraform import aws_secretsmanager_secret.slack_webhook \
#     airflow/variables/slack_webhook_url
#   terraform import aws_secretsmanager_secret.coingecko_api_key \
#     airflow/variables/coingecko_api_key
#
# lifecycle.ignore_changes on secret_string/version isn't needed since we
# never define an aws_secretsmanager_secret_version resource at all - the
# value is set out-of-band via the AWS CLI/console only.

resource "aws_secretsmanager_secret" "slack_webhook" {
  name        = "airflow/variables/slack_webhook_url"
  description = "Slack incoming webhook URL used for pipeline alerts."
}

resource "aws_secretsmanager_secret" "coingecko_api_key" {
  name        = "airflow/variables/coingecko_api_key"
  description = "Optional CoinGecko demo API key."
}
