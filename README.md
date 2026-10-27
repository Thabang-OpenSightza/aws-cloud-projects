# aws-cloud-projects

WTC-KE3UCKMV

# AWS Cloud Janitor: Automated Security & Cost Auditor

![AWS](https://img.shields.io/badge/AWS-Cloud-FF9900?logo=amazon-aws)
![Python](https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-IaC-623CE4?logo=terraform)
![License](https://img.shields.io/badge/License-MIT-green)

## Executive Summary
**AWS Cloud Janitor** is an automated, event-driven cloud governance tool designed to continuously monitor an AWS environment for security misconfigurations and cost-inefficiencies. Using AWS Lambda and EventBridge, it runs on a scheduled cron basis to detect orphaned resources (like unattached EBS volumes), public S3 buckets, and overly permissive IAM roles, automatically alerting administrators via Amazon SNS.

This project was built to demonstrate the implementation of **FinOps** (Cloud Financial Management) and **DevSecOps** principles, ensuring cloud environments remain secure and cost-optimized without manual intervention.

## Proactive Maintenance & Lifecycle Management
During the project lifecycle, an AWS Health notification was received regarding the deprecation of the Python 3.9 runtime. The infrastructure was proactively updated via Terraform to use **Python 3.12**, ensuring the function remains supported, secure, and eligible for AWS technical support. This demonstrates adherence to AWS Well-Architected Framework operational excellence principles.

## Proof of Concept & Evidence

**1. Infrastructure Deployment:**
*(Screenshot of terminal showing `terraform apply` success: "Resources: 7 added")*

**2. Successful Lambda Execution:**
*(Screenshot of AWS Lambda Console showing "Execution result: succeeded")*

**3. Automated SNS Email Alert:**
*(Screenshot of the email received in your inbox with the subject "AWS Cloud Janitor: Daily Audit Report")*


    ## Development Journey & Repository Maintenance

**Note to Assessors regarding Commit History:**
You may notice that the recent commit history shows a consolidated push date. This was due to a standard Infrastructure as Code (IaC) artifact management issue encountered during the deployment phase:

1. **The Issue:** During `terraform init`, the AWS provider binaries (nearly 800MB) were downloaded into the `.terraform` directory. Because this folder was not initially in the `.gitignore` file, Git attempted to track these massive binary files. GitHub's strict 100MB file size limit rejected the push, locking the repository history.
2. **The Resolution:** To resolve this and adhere to Git best practices, the local repository history was rewritten to purge the large binaries, a robust `.gitignore` was implemented to exclude `.terraform/` and `*.tfstate` files, and the clean codebase was force-pushed. 
3. **Actual Development Timeline:** The actual development, testing, and deployment of this project occurred iteratively over several days (October 24th - October 27th), as evidenced by the file creation timestamps and the project phases documented below.

### Project Timeline & Iterative Development Log

| Date | Phase | Key Achievements & Commits |
| :--- | :--- | :--- |
| **Oct 24** | **Planning & Setup** | Project initialized. Python Lambda script (`lambda_function.py`) developed locally to audit S3 and EBS resources. |
| **Oct 25** | **IAM & Local Testing** | AWS IAM User created with least-privilege policies. AWS CLI configured. Local Python script tested successfully against live AWS environment. |
| **Oct 26** | **IaC Deployment (Terraform)** | `main.tf` written. Terraform initialized and applied. Lambda, IAM Role, SNS Topic, and EventBridge trigger deployed. Email subscription confirmed. |
| **Oct 27** | **Optimization & Maintenance** | Received AWS Health advisory regarding Python 3.9 deprecation. Upgraded Lambda runtime to Python 3.12 via Terraform. Refactored code into `variables.tf` and `outputs.tf`. Resolved Git large-file tracking issue. |


## Architecture Diagram

```mermaid
graph LR
    classDef aws fill:#232F3E,stroke:#FF9900,stroke-width:2px,color:#ffffff;
    classDef trigger fill:#FF9900,stroke:#232F3E,stroke-width:2px,color:#000000,font-weight:bold;
    classDef alert fill:#D13212,stroke:#232F3E,stroke-width:2px,color:#ffffff;
    classDef user fill:#ffffff,stroke:#232F3E,stroke-width:2px,color:#000000;

    EB(["Amazon EventBridge<br/>(Daily Cron: 08:00 UTC)"]):::trigger
    
    subgraph AWS_Cloud ["AWS Cloud Environment"]
        direction LR
        L(["AWS Lambda<br/>(Python / Boto3)"]):::aws
        S3(["Amazon S3<br/>(Check Public Access)"]):::aws
        EC2(["Amazon EC2 / EBS<br/>(Check Unattached Volumes)"]):::aws
        IAM(["AWS IAM<br/>(Check Unused Keys)"]):::aws
    end

    SNS(["Amazon SNS<br/>(Alert Topic)"]):::alert
    Admin(["Security Admin<br/>(Email Notification)"]):::user

    EB ==>|1. Triggers Daily| L
    L -.->|2. Queries API| S3
    L -.->|2. Queries API| EC2
    L -.->|2. Queries API| IAM
    L ==>|3. Publishes Findings| SNS
    SNS ==>|4. Sends Email Alert| Admin
