#!/usr/bin/env python3
"""
GuardDuty Findings Summary
-------------------------
This Week-3 extension collects active GuardDuty findings, groups them by severity,
and exports a summary Excel report for auditors.

Why each import is necessary:
- **boto3**: AWS SDK to query GuardDuty detectors and findings.
- **pandas**: Build tabular report and export to Excel.
- **logging**: Persist audit trail.
- **datetime**: Timestamping and 24-hour cutoff.
- **sys**: Exit codes for CI pipelines.
"""
import boto3
import pandas as pd
import logging
from datetime import datetime, timedelta
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("guardduty_audit.log"), logging.StreamHandler()],
)

def get_active_detector_ids():
    """Return list of GuardDuty detector IDs in the account/region."""
    gd = boto3.client("guardduty")
    response = gd.list_detectors()
    return response.get("DetectorIds", [])

def fetch_findings(detector_id):
    """Fetch findings from the given detector created in the last 24h."""
    gd = boto3.client("guardduty")
    start_time = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    finding_ids = gd.list_findings(
        DetectorId=detector_id,
        FindingCriteria={
            "Criterion": {
                "updatedAt": {
                    "Gte": int((datetime.utcnow() - timedelta(days=1)).timestamp())
                }
            }
        },
    )["FindingIds"]
    if not finding_ids:
        return []
    findings = gd.get_findings(DetectorId=detector_id, FindingIds=finding_ids)["Findings"]
    return findings

def summarise_findings(all_findings):
    """Return pandas DataFrame summarising by severity."""
    records = []
    for f in all_findings:
        records.append(
            {
                "finding_id": f["Id"],
                "type": f["Type"],
                "severity": f["Severity"],
                "title": f["Title"],
                "region": f["Region"],
                "created_at": f["CreatedAt"],
            }
        )
    df = pd.DataFrame(records)
    if df.empty:
        return df
    summary = (
        df.groupby(pd.cut(df["severity"], [0, 3.9, 6.9, 8.9, 10], labels=["Low", "Medium", "High", "Critical"]))
        .size()
        .reset_index(name="count")
    )
    return summary

def export_excel(df, filename="guardduty_findings_summary.xlsx"):
    """Export DataFrame to Excel with openpyxl backend."""
    if df.empty:
        logging.info("No recent findings – creating placeholder report")
        df = pd.DataFrame(columns=["severity", "count"])
    df["report_generated_at"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    df.to_excel(filename, index=False, sheet_name="GD_Findings_Summary")
    logging.info(f"Excel report saved: {filename}")

def main():
    logging.info("=== GuardDuty Findings Summary ===")
    detector_ids = get_active_detector_ids()
    all_findings = []
    for det in detector_ids:
        all_findings.extend(fetch_findings(det))
    summary_df = summarise_findings(all_findings)
    export_excel(summary_df)

    non_zero = summary_df["count"].sum() if not summary_df.empty else 0
    logging.info(f"Total findings last 24h: {non_zero}")
    sys.exit(2 if non_zero else 0)

if __name__ == "__main__":
    main()
