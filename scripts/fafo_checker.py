#!/usr/bin/env python3
"""
FAFO Checker – IAM Users Without MFA
====================================
Week-3 capstone for the Python-for-GRC study plan.

Purpose
-------
1. Demonstrate an end-to-end compliance control: "All IAM users must have MFA enabled".
2. Produce auditor-friendly evidence (Excel + log) with explanatory comments.
3. Showcase error handling and timestamped logging for GRC requirements.

Why each import is necessary
---------------------------
- **boto3** – AWS SDK to query IAM API.
- **pandas** – Build tabular report and export to XLSX.
- **logging** – Persist evidence of the run (who, when, result).
- **datetime** – Timestamping for audit trails.
- **sys** – Exit codes for CI pipelines.
"""

import boto3
import pandas as pd
import logging
from datetime import datetime
import sys

# Configure logging: writes BOTH to console and a file `fafo_audit.log`.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("fafo_audit.log"),
        logging.StreamHandler()
    ]
)


def list_users_without_mfa():
    """Return a list of IAM users that have *zero* MFA devices."""
    iam = boto3.client("iam")
    paginator = iam.get_paginator("list_users")
    users_no_mfa = []

    logging.info("Fetching IAM user list via pagination …")

    try:
        for page in paginator.paginate():
            for user in page["Users"]:
                user_name = user["UserName"]
                logging.debug(f"Checking MFA for user: {user_name}")

                mfa_response = iam.list_mfa_devices(UserName=user_name)
                if len(mfa_response["MFADevices"]) == 0:
                    # Record non-compliant user details
                    users_no_mfa.append(
                        {
                            "user_name": user_name,
                            "user_arn": user["Arn"],
                            "create_date": user["CreateDate"],
                            "create_date_str": user["CreateDate"].strftime("%Y-%m-%d %H:%M:%S"),
                        }
                    )

        logging.info(f"Total IAM users without MFA: {len(users_no_mfa)}")
        return users_no_mfa

    except Exception as error:
        logging.error(f"Failed to evaluate MFA status: {error}")
        return []


def export_excel(data: list, filename: str = "iam_users_without_mfa.xlsx"):
    """Export list of dicts to an Excel file with pandas/openpyxl."""
    # DataFrame construction – safe even if list is empty.
    df = pd.DataFrame(data)

    if df.empty:
        logging.warning("No non-compliant users found – Excel will contain headers only.")
        df = pd.DataFrame(columns=[
            "user_name",
            "user_arn",
            "create_date",
            "create_date_str",
            "report_generated_at",
            "total_non_compliant_users",
        ])
    else:
        # Remove timezone from datetimes (Excel limitation)
        df["create_date"] = pd.to_datetime(df["create_date"]).dt.tz_localize(None)

    # Add metadata columns
    df["report_generated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df["total_non_compliant_users"] = len(data)

    # Write to Excel
    df.to_excel(filename, index=False, sheet_name="IAM_Users_No_MFA")
    logging.info(f"Excel report saved: {filename}")


def main():
    logging.info("=== Starting FAFO MFA Compliance Check ===")
    start = datetime.now()

    users_no_mfa = list_users_without_mfa()
    export_excel(users_no_mfa)

    duration = (datetime.now() - start).total_seconds()
    logging.info(f"Completed in {duration:.2f} seconds")
    logging.info("=== FAFO Compliance Check Complete ===")

    # Exit code 0 if compliant, 2 if violations found (convention for CI pipelines)
    if users_no_mfa:
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
