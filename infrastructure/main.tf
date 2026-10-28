   provider "aws" {
     region = var.aws_region
   }

   # 1. Package the Python code automatically
   data "archive_file" "lambda_zip" {
     type        = "zip"
     source_dir  = "../src"
     output_path = "lambda_function_payload.zip"
   }

   # 2. IAM Role for Lambda (Least Privilege)
   resource "aws_iam_role" "lambda_role" {
     name = "cloud-janitor-lambda-role"
     assume_role_policy = jsonencode({
       Version = "2012-10-17"
       Statement = [{
         Action = "sts:AssumeRole"
         Effect = "Allow"
         Principal = { Service = "lambda.amazonaws.com" }
       }]
     })
   }

   # 3. IAM Policy granting only necessary permissions
   resource "aws_iam_role_policy" "lambda_policy" {
     name = "cloud-janitor-lambda-policy"
     role = aws_iam_role.lambda_role.id
     policy = jsonencode({
       Version = "2012-10-17"
       Statement = [
         {
           Effect = "Allow"
           Action = ["s3:ListAllMyBuckets", "s3:GetBucketPublicAccessBlock", "ec2:DescribeVolumes", "sns:Publish", "logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
           Resource = "*"
         }
       ]
     })
   }

   # 4. Lambda Function
   resource "aws_lambda_function" "janitor" {
     filename         = "lambda_function_payload.zip"
     function_name    = "aws-cloud-janitor"
     role             = aws_iam_role.lambda_role.arn
     handler          = "lambda_function.lambda_handler"
     source_code_hash = data.archive_file.lambda_zip.output_base64sha256
     runtime          = "python3.12"
     timeout          = 30
	
     environment {
       variables ={
	SNS_TOPIC_ARN = aws_sns_topic.alert_topic.arn
      }  
     }
  
     #runtime	= "python3.9"
     #timeout	= 30
   } 

   # 5. SNS Topic for Alerts
   resource "aws_sns_topic" "alert_topic" {
     name = "cloud-janitor-alerts"
   }

   # 6. EventBridge Rule (Daily at 08:00 UTC)
   resource "aws_cloudwatch_event_rule" "daily_trigger" {
     name                = "cloud-janitor-daily-trigger"
     schedule_expression = "cron(0 8 * * ? *)"
   }

   resource "aws_cloudwatch_log_group" "janitor_logs" {
     name              = "/aws/lambda/${aws_lambda_function.janitor.function_name}"
     retention_in_days = 30
   }

   resource "aws_cloudwatch_event_target" "lambda_target" {
     rule      = aws_cloudwatch_event_rule.daily_trigger.name
     target_id = "CloudJanitorLambda"
     arn       = aws_lambda_function.janitor.arn
   }

   resource "aws_lambda_permission" "allow_eventbridge" {
     statement_id  = "AllowExecutionFromEventBridge"
     action        = "lambda:InvokeFunction"
     function_name = aws_lambda_function.janitor.function_name
     principal     = "events.amazonaws.com"
     source_arn    = aws_cloudwatch_event_rule.daily_trigger.arn
   }
