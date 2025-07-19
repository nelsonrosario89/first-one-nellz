#!/usr/bin/env python3
"""
AWS Config Non-Compliant Rules Report
-------------------------------------
Queries AWS Config for all rules whose compliance status is NON_COMPLIANT,
then exports an Excel report. CI exit code 2 if any violations exist.
"""
import boto3
import pandas as pd
import logging
from datetime import datetime
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("config_audit.log"), logging.StreamHandler()],
)

def fetch_noncompliant_rules():
    cfg = boto3.client("config")
    paginator = cfg.get_paginator("describe_compliance_by_config_rule")
    results = []
    for page in paginator.paginate(ComplianceTypes=["NON_COMPLIANT"]):
        for rule in page.get("ComplianceByConfigRules", []):
            results.append(
                {
                    "config_rule": rule["ConfigRuleName"],
                    "compliance_type": rule["Compliance"]["ComplianceType"],
                    "noncompliant_count": rule["Compliance"]["NonCompliantResourceCount"]["CappedCount"],
                }
            )
    return results

def export_excel(data, filename="config_noncompliant_rules.xlsx"):
    df = pd.DataFrame(data)
    if df.empty:
        logging.info("All Config rules compliant – placeholder report created")
        df = pd.DataFrame(columns=["config_rule", "compliance_type", "noncompliant_count"])
    df["report_generated_at"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    df.to_excel(filename, index=False, sheet_name="Config_NonCompliant")
    logging.info(f"Excel report saved: {filename}")

def main():
    logging.info("=== AWS Config Non-Compliant Rules Check ===")
    records = fetch_noncompliant_rules()
    export_excel(records)
    violations = len(records)
    logging.info(f"Total non-compliant rules: {violations}")
    sys.exit(2 if violations else 0)

if __name__ == "__main__":
    main()
