variable "aws_region" {
  description = "AWS region for all resources."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Short name used to prefix/tag resources."
  type        = string
  default     = "bitcoin-pipeline"
}

variable "environment" {
  description = "Deployment environment name (e.g. dev, prod)."
  type        = string
  default     = "dev"
}

variable "s3_bucket_name" {
  description = <<-EOT
    Globally-unique S3 bucket name for raw/processed/archive data. Must match
    BITCOIN_S3_BUCKET in .env so the pipeline uploads to the bucket this
    module manages.
  EOT
  type        = string
}

variable "raw_data_transition_days" {
  description = "Days before raw/processed objects transition to STANDARD_IA."
  type        = number
  default     = 30
}

variable "raw_data_expiration_days" {
  description = "Days before raw/processed objects expire entirely."
  type        = number
  default     = 365
}
