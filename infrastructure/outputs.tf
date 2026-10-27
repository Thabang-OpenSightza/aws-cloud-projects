output "lambda_function_name" {
  description = "Name of the deployed Lambda function"
  value       = aws_lambda_function.janitor.function_name
}

output "sns_topic_arn" {
  description = "ARN of the SNS topic for alerts"
  value       = aws_sns_topic.alert_topic.arn
}
