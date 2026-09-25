output "bucket_name" {
  description = "S3 bucket for raw/processed/archive data. Set this as BITCOIN_S3_BUCKET in .env."
  value       = aws_s3_bucket.bitcoin_data.id
}

output "iam_policy_arn" {
  description = "Least-privilege policy ARN - attach it to the identity the pipeline runs as."
  value       = aws_iam_policy.bitcoin_pipeline.arn
}

output "secret_arns" {
  description = "ARNs of the two Secrets Manager entries (values are set out-of-band)."
  value = {
    slack_webhook_url = aws_secretsmanager_secret.slack_webhook.arn
    coingecko_api_key = aws_secretsmanager_secret.coingecko_api_key.arn
  }
}

output "glue_database_name" {
  description = "Glue Catalog database name, for Athena queries."
  value       = aws_glue_catalog_database.bitcoin_db.name
}

output "glue_table_name" {
  description = "Glue Catalog table name over the partitioned processed/ data."
  value       = aws_glue_catalog_table.bitcoin_processed.name
}
