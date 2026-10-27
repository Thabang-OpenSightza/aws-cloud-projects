import boto3
import json
import os

def check_s3_public_access():
    s3_client = boto3.client('s3')
    findings = []
    try:
        response = s3_client.list_buckets()
        for bucket in response['Buckets']:
            bucket_name = bucket['Name']
            try:
                bpa = s3_client.get_public_access_block(Bucket=bucket_name)
                block_public_acls = bpa['PublicAccessBlockConfiguration'].get('BlockPublicAcls', False)
                block_public_policy = bpa['PublicAccessBlockConfiguration'].get('BlockPublicPolicy', False)
                if not (block_public_acls and block_public_policy):
                    findings.append(f"WARNING: S3 Bucket '{bucket_name}' does not have full Block Public Access enabled.")
            except s3_client.exceptions.ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchPublicAccessBlockConfiguration':
                    findings.append(f"WARNING: S3 Bucket '{bucket_name}' has NO Public Access Block configuration.")
    except Exception as e:
        findings.append(f"ERROR checking S3: {str(e)}")
    return findings

def check_unattached_ebs_volumes():
    ec2_client = boto3.client('ec2')
    findings = []
    try:
        response = ec2_client.describe_volumes(Filters=[{'Name': 'status', 'Values': ['available']}])
        for volume in response['Volumes']:
            vol_id = volume['VolumeId']
            size = volume['Size']
            findings.append(f"COST WARNING: Unattached EBS Volume '{vol_id}' ({size} GB) is incurring charges.")
    except Exception as e:
        findings.append(f"ERROR checking EBS: {str(e)}")
    return findings

def lambda_handler(event, context):
    print("Starting AWS Cloud Janitor Audit...")
    all_findings = []
    s3_findings = check_s3_public_access()
    ebs_findings = check_unattached_ebs_volumes()
    all_findings.extend(s3_findings)
    all_findings.extend(ebs_findings)
    
    if not all_findings:
        report = "SUCCESS: No security or cost misconfigurations found. Your AWS environment is clean!"
    else:
        report = "AUDIT FINDINGS:\n" + "\n".join(all_findings)
        
    print("\n" + "="*50)
    print(report)
    print("="*50 + "\n")
    return {'statusCode': 200, 'body': json.dumps(report)}

# SEND THE EMAIL ALERT VIA SNS
    try:
        sns_client = boto3.client('sns')
        sns_client.publish(
            TopicArn=os.environ['SNS_TOPIC_ARN'],
            Message=report,
            Subject='AWS Cloud Janitor: Daily Audit Report'
        )
        print("Alert successfully sent to SNS topic.")
    except Exception as e:
        print(f"Failed to send SNS alert: {str(e)}")

    return {'statusCode': 200, 'body': json.dumps(report)}


if __name__ == "__main__":
    lambda_handler({}, {})
