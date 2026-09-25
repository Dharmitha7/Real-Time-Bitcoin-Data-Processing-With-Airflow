resource "aws_s3_bucket" "bitcoin_data" {
  bucket = var.s3_bucket_name
}

resource "aws_s3_bucket_versioning" "bitcoin_data" {
  bucket = aws_s3_bucket.bitcoin_data.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "bitcoin_data" {
  bucket = aws_s3_bucket.bitcoin_data.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "bitcoin_data" {
  bucket = aws_s3_bucket.bitcoin_data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "bitcoin_data" {
  bucket = aws_s3_bucket.bitcoin_data.id

  rule {
    id     = "raw-processed-transition-and-expire"
    status = "Enabled"

    filter {} # applies to every object in the bucket

    transition {
      days          = var.raw_data_transition_days
      storage_class = "STANDARD_IA"
    }

    expiration {
      days = var.raw_data_expiration_days
    }

    noncurrent_version_expiration {
      noncurrent_days = var.raw_data_expiration_days
    }
  }
}
