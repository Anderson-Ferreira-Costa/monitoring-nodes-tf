resource "aws_dynamodb_table" "this" {
  name                        = "InstanceAlertStateTable"
  billing_mode                = "PAY_PER_REQUEST"
  read_capacity               = null
  write_capacity              = null
  hash_key                    = "InstanceId"
  deletion_protection_enabled = true

  server_side_encryption {
    enabled = true
  }

  point_in_time_recovery {
    enabled = false
  }

  attribute {
    name = "InstanceId"
    type = "S"
  }
}
