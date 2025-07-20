#!/usr/bin/env python3
"""
EC2 Compliance Checker
----------------------
Checks EC2 instances for compliance with security best practices.
Exits 0 if compliant, 2 if violations found.
"""
import boto3
import pandas as pd
import logging
import sys
from datetime import datetime, timezone
from botocore.exceptions import ClientError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("ec2_audit.log"), logging.StreamHandler()],
)

def check_ec2_compliance():
    ec2 = boto3.client("ec2")
    non_compliant = []
    
    try:
        # Get all instances across all regions
        regions = [region['RegionName'] for region in ec2.describe_regions()['Regions']]
        
        for region in regions:
            ec2_region = boto3.client('ec2', region_name=region)
            paginator = ec2_region.get_paginator('describe_instances')
            
            for page in paginator.paginate():
                for reservation in page['Reservations']:
                    for instance in reservation['Instances']:
                        instance_id = instance['InstanceId']
                        issues = []
                        
                        # Skip terminated instances
                        if instance['State']['Name'] == 'terminated':
                            continue
                            
                        # Check 1: Termination protection
                        try:
                            attr = ec2_region.describe_instance_attribute(
                                InstanceId=instance_id,
                                Attribute='disableApiTermination'
                            )
                            if not attr['DisableApiTermination']['Value']:
                                issues.append("Termination protection disabled")
                        except ClientError as e:
                            issues.append(f"API error: {str(e)}")
                        
                        # Check 2: Public IP exposure
                        if instance.get('PublicIpAddress'):
                            # Check if public IP is required (e.g., for NAT gateways, etc.)
                            # This is a simple check; you might want to expand it
                            issues.append("Has public IP address")
                            
                        # Check 3: EBS volume encryption
                        for bdm in instance.get('BlockDeviceMappings', []):
                            if 'Ebs' in bdm:
                                vol_id = bdm['Ebs']['VolumeId']
                                vol = ec2_region.describe_volumes(VolumeIds=[vol_id])
                                if not vol['Volumes'][0]['Encrypted']:
                                    issues.append(f"Volume {vol_id} is not encrypted")
                            
                        if issues:
                            non_compliant.append({
                                "instance_id": instance_id,
                                "instance_type": instance.get('InstanceType', 'N/A'),
                                "state": instance['State']['Name'],
                                "region": region,
                                "launch_time": str(instance.get('LaunchTime')),
                                "issues": "; ".join(issues)
                            })
        
        return non_compliant
        
    except Exception as e:
        logging.error(f"Error checking EC2 compliance: {str(e)}")
        raise

def export_report(non_compliant, filename="ec2_compliance_report.xlsx"):
    """Export compliance issues to Excel with timestamp."""
    df = pd.DataFrame(non_compliant if non_compliant else 
                     [{"status": "All EC2 instances are compliant"}])
    df["report_generated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    df.to_excel(filename, index=False)
    logging.info(f"Report saved to {filename}")

def main():
    logging.info("=== Starting EC2 Compliance Check ===")
    try:
        non_compliant = check_ec2_compliance()
        export_report(non_compliant)
        
        if non_compliant:
            logging.warning(f"Found {len(non_compliant)} non-compliant EC2 instances")
            sys.exit(2)  # Non-zero exit for CI/CD pipelines
        else:
            logging.info("All EC2 instances are compliant")
            sys.exit(0)
            
    except Exception as e:
        logging.error(f"Compliance check failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
