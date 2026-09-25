resource "aws_glue_catalog_database" "bitcoin_db" {
  name = replace("${var.project_name}_${var.environment}", "-", "_")
}

# Over the processed/dt=YYYY-MM-DD/hour=HH/bitcoin_processed.parquet layout
# written by bitcoin_pipeline.storage (Phase 7). Add a matching table for
# raw/ the same way if you need to query raw data directly.
resource "aws_glue_catalog_table" "bitcoin_processed" {
  name          = "bitcoin_processed"
  database_name = aws_glue_catalog_database.bitcoin_db.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    classification = "parquet"
  }

  partition_keys {
    name = "dt"
    type = "string"
  }

  partition_keys {
    name = "hour"
    type = "string"
  }

  storage_descriptor {
    location      = "s3://${var.s3_bucket_name}/processed/"
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"

    ser_de_info {
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
    }

    columns {
      name = "timestamp"
      type = "string"
    }
    columns {
      name = "price_usd"
      type = "double"
    }
    columns {
      name = "change_1h"
      type = "double"
    }
    columns {
      name = "change_24h"
      type = "double"
    }
    columns {
      name = "price_ma"
      type = "double"
    }
    columns {
      name = "price_std"
      type = "double"
    }
  }
}
