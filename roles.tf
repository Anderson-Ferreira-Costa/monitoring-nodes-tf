# Role for lambda
resource "aws_iam_role" "role_for_lambda" {
  name = "role_monitoring_nodes_eks"

  assume_role_policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Sid" : "",
        "Effect" : "Allow",
        "Principal" : {
          "Service" : "lambda.amazonaws.com"
        },
        "Action" : "sts:AssumeRole"
      }
    ]
  })
}

# Policy for lambda
resource "aws_iam_policy" "policy_for_lambda" {
  name = "policy_monitoring_nodes_eks"
  path = "/"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "ec2:DescribeInstances",
          "cloudwatch:GetMetricData",
          "SNS:Publish",
          "dynamodb:GetItem",
          "dynamodb:PutItem"
        ]
        Effect   = "Allow"
        Resource = "*"
      },
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach_lambda" {
  role       = aws_iam_role.role_for_lambda.name
  policy_arn = aws_iam_policy.policy_for_lambda.arn
}