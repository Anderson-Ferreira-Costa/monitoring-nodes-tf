data "archive_file" "this" {
  type        = "zip"
  source_file = "files/codigo.py"
  output_path = "files/codigo.zip"
}
resource "aws_lambda_function" "this" {

  function_name    = var.function_name
  filename         = data.archive_file.this.output_path
  source_code_hash = data.archive_file.this.output_base64sha256

  role    = aws_iam_role.role_for_lambda.arn
  runtime = "python3.12"
  handler = "codigo.lambda_handler"
  timeout = 60
}


