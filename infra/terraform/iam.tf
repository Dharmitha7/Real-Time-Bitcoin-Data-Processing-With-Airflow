# Defines the policy only - deliberately does NOT attach it to any IAM user
# or role via Terraform. Managing your own interactively-used IAM identity
# through the same IaC that manages application infra is fragile (a bad
# apply could lock you out). Attach it yourself once:
#
#   aws iam attach-user-policy --user-name <you> --policy-arn <output below>
#   # or, for the pipeline's own execution role:
#   aws iam attach-role-policy --role-name <pipeline-role> --policy-arn <output below>

data "aws_caller_identity" "current" {}

data "aws_iam_policy_document" "bitcoin_pipeline" {
  statement {
    sid    = "S3ReadWriteBucket"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
    ]
    resources = ["${aws_s3_bucket.bitcoin_data.arn}/*"]
  }

  statement {
    sid       = "S3ListBucket"
    effect    = "Allow"
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.bitcoin_data.arn]
  }

  statement {
    sid    = "ReadPipelineSecrets"
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue",
    ]
    resources = [
      aws_secretsmanager_secret.slack_webhook.arn,
      aws_secretsmanager_secret.coingecko_api_key.arn,
    ]
  }

  statement {
    sid    = "GlueReadWriteCatalog"
    effect = "Allow"
    actions = [
      "glue:GetDatabase",
      "glue:GetTable",
      "glue:GetPartitions",
      "glue:BatchCreatePartition",
    ]
    resources = [
      "arn:aws:glue:${var.aws_region}:${data.aws_caller_identity.current.account_id}:catalog",
      aws_glue_catalog_database.bitcoin_db.arn,
      aws_glue_catalog_table.bitcoin_processed.arn,
    ]
  }
}

resource "aws_iam_policy" "bitcoin_pipeline" {
  name        = "${var.project_name}-${var.environment}-policy"
  description = "Least-privilege access for the Bitcoin pipeline: its own S3 bucket, its two secrets, its Glue catalog entries."
  policy      = data.aws_iam_policy_document.bitcoin_pipeline.json
}
