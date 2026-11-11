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

    def check_open_security_groups():
        ec2_client = boto3.client('ec2')
        findings = []
        try:
            response = ec2_client.describe_security_groups()
            for sg in response['SecurityGroups']:
                sg_id = sg['GroupId']
                sg_name = sg['GroupName']
                # Check inbound rules for open access to the world
                for permission in sg['IpPermissions']:
                    for ip_range in permission.get('IpRanges', []):
                        if ip_range.get('CidrIp') == '0.0.0.0/0':
                            port = permission.get('FromPort', 'All')
                            findings.append(f"SECURITY RISK: Security Group '{sg_name}' ({sg_id}) has port {port} open to the world (0.0.0.0/0).")
        except Exception as e:
            findings.append(f"ERROR checking Security Groups: {str(e)}")
        return findings

def check_root_mfa():
    iam_client = boto3.client('iam')
    findings = []
    try:
        # Get summary of account
        summary = iam_client.get_account_summary()
        # If AccountMFAEnabled is 0, root has no MFA
        if summary['SummaryMap'].get('AccountMFAEnabled', 0) == 0:
            findings.append("CRITICAL SECURITY RISK: Root account does NOT have MFA enabled!")
    except Exception as e:
        # Note: This often fails in free tier accounts due to permissions, which is fine to catch
        findings.append(f"INFO: Could not verify Root MFA status (Expected in limited permission environments).")
    return findings

def lambda_handler(event, context):
    print("Starting AWS Cloud Janitor Audit...")
    all_findings = []

    # Run all checks
    all_findings.extend(check_s3_public_access())
    all_findings.extend(check_unattached_ebs_volumes())
    all_findings.extend(check_open_security_groups())
    all_findings.extend(check_root_mfa())

    # Create HTML Report
    if not all_findings:
        html_body = "<h2 style='color:green;'> SUCCESS: Your AWS environment is clean!</h2>"
        html_body += "<p>No security or cost misconfigurations found.</p>"
    else:
        html_body = "<h2 style='color:red;'> AUDIT FINDINGS:</h2>"
        html_body += "<ul>"
        for finding in all_findings:
            # Color code based on severity keywords
            if "SECURITY RISK" in finding:
                html_body += f"<li style='color:red; font-weight:bold;'>{finding}</li>"
            elif "COST WARNING" in finding:
                html_body += f"<li style='color:orange;'>{finding}</li>"
            else:
                html_body += f"<li style='color:blue;'>{finding}</li>"
        html_body += "</ul>"

    print("\n" + "="*50)
    print("Report generated. Sending via SNS...")

    # Send via SNS
    try:
        sns_client = boto3.client('sns')
        sns_client.publish(
            TopicArn=os.environ['SNS_TOPIC_ARN'],
            Message=html_body,
            Subject='AWS Cloud Janitor: Daily Audit Report',
            MessageAttributes={
                'AWS.SNS.SMS.SMSType': {
                    'DataType': 'String',
                    'StringValue': 'Transactional'
                }
            }
        )
        print("Alert successfully sent to SNS topic.")
    except Exception as e:
        print(f"Failed to send SNS alert: {str(e)}")

    return {'statusCode': 200, 'body': 'Report sent.'}
if __name__ == "__main__":
    lambda_handler({}, {})
