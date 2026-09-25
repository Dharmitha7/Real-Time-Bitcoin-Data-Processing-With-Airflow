terraform {
  # Left empty on purpose: the state-backend bucket/table are created by a
  # one-time manual bootstrap (see README.md's "Terraform Bootstrap" section)
  # before this bucket name is even known, so config is supplied at init time:
  #   terraform init -backend-config=backend.hcl
  # Copy backend.hcl.example to backend.hcl (gitignored) and fill in the
  # bucket/table names your bootstrap step created.
  backend "s3" {}
}
