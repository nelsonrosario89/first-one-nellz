#!/usr/bin/env python3
"""
Unused IAM Access Keys Checker
------------------------------
Flags active access keys that have not been used in the last 90 days.
Outputs Excel + audit log. Exit 2 if any unused keys detected.
"""
import boto3
import pandas as pd
import logging
from datetime import datetime, timedelta
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("iam_keys_audit.log"), logging.StreamHandler()],
)

def list_unused_keys(threshold_days: int = 90):
    iam = boto3.client("iam")
    paginator = iam.get_paginator("list_users")
    cutoff = datetime.utcnow() - timedelta(days=threshold_days)
    unused = []

    logging.info(f"Scanning IAM users for keys unused since {cutoff:%Y-%m-%d}")

    for page in paginator.paginate():
        for user in page["Users"]:
            username = user["UserName"]
            keys = iam.list_access_keys(UserName=username)["AccessKeyMetadata"]
            for key in keys:
                if key["Status"] != "Active":
                    continue  # ignore inactive keys
                last_used_resp = iam.get_access_key_last_used(AccessKeyId=key["AccessKeyId"])
                last_used = last_used_resp.get("AccessKeyLastUsed", {}).get("LastUsedDate")
                if last_used is None or last_used < cutoff:
                    unused.append(
                        {
                            "user_name": username,
                            "access_key_id": key["AccessKeyId"],
                            "create_date": key["CreateDate"],
                            "last_used": last_used,
                            "age_days": (datetime.utcnow() - key["CreateDate"]).days,
                        }
                    )
    return unused

def export_excel(data, filename="iam_unused_access_keys.xlsx"):
    df = pd.DataFrame(data)
    if df.empty:
        logging.info("No unused active keys detected – placeholder report created")
        df = pd.DataFrame(columns=["user_name", "access_key_id", "create_date", "last_used", "age_days"])
    else:
        # Remove timezone info for Excel compatibility
        df["create_date"] = pd.to_datetime(df["create_date"]).dt.tz_localize(None)
        if df["last_used"].notna().any():
            df["last_used"] = pd.to_datetime(df["last_used"]).dt.tz_localize(None)
    df["report_generated_at"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    df.to_excel(filename, index=False, sheet_name="Unused_Access_Keys")
    logging.info(f"Excel report saved: {filename}")

def main():
    logging.info("=== Unused IAM Access Keys Check ===")
    unused_keys = list_unused_keys()
    export_excel(unused_keys)
    violations = len(unused_keys)
    logging.info(f"Total unused active keys: {violations}")
    sys.exit(2 if violations else 0)

if __name__ == "__main__":
    main()
