#!/usr/bin/env python3
"""
S3 Bucket Listing Script for GRC Compliance
============================================
This script demonstrates Week 2 concepts from the Python GRC study plan:
- Using boto3 to interact with AWS APIs
- Processing data with pandas
- Exporting results to Excel for audit evidence
- Adding logging for compliance tracking
"""

import boto3  # AWS SDK for Python - handles authentication and API calls
import pandas as pd  # Data manipulation library for creating tables/DataFrames
import logging  # Built-in Python logging for audit trails
from datetime import datetime  # For timestamping our reports
import sys  # For system exit codes if errors occur

# Configure logging to create audit-quality evidence
# This creates a log file with timestamps showing what the script did
logging.basicConfig(
    level=logging.INFO,  # INFO level captures important events without debug noise
    format='%(asctime)s - %(levelname)s - %(message)s',  # Timestamp + level + message
    handlers=[
        logging.FileHandler('s3_audit.log'),  # Write to file for permanent record
        logging.StreamHandler()  # Also print to console for immediate feedback
    ]
)

def get_s3_buckets():
    """
    Retrieve all S3 buckets in the AWS account.
    
    Returns:
        list: List of bucket dictionaries with name and creation date
    """
    try:
        # Create S3 client using default credentials (from ~/.aws/credentials or IAM role)
        # boto3 automatically handles authentication, region selection, and retries
        s3_client = boto3.client('s3')
        
        logging.info("Connecting to AWS S3 service...")
        
        # Call the list_buckets API - this is the core AWS interaction
        # Returns metadata about all buckets the current user can access
        response = s3_client.list_buckets()
        
        # Extract the 'Buckets' list from the API response
        # AWS APIs return JSON with metadata; we only need the bucket data
        buckets = response['Buckets']
        
        logging.info(f"Successfully retrieved {len(buckets)} S3 buckets")
        
        # Transform AWS response into a cleaner format for pandas
        # Each bucket becomes a dictionary with standardized field names
        bucket_list = []
        for bucket in buckets:
            bucket_info = {
                'bucket_name': bucket['Name'],  # Human-readable bucket identifier
                'creation_date': bucket['CreationDate'],  # When bucket was created
                'creation_date_str': bucket['CreationDate'].strftime('%Y-%m-%d %H:%M:%S')  # Formatted for Excel
            }
            bucket_list.append(bucket_info)
            
        return bucket_list
        
    except Exception as e:
        # Log any errors for troubleshooting and compliance documentation
        logging.error(f"Failed to retrieve S3 buckets: {str(e)}")
        # Return empty list so script can continue and produce a report showing the error
        return []

def create_excel_report(bucket_data, filename='s3_buckets_report.xlsx'):
    """
    Create an Excel report from S3 bucket data.
    
    Args:
        bucket_data (list): List of bucket dictionaries
        filename (str): Output Excel file name
    """
    try:
        # Convert list of dictionaries to pandas DataFrame
        # DataFrame is like an Excel table - rows and columns with headers
        df = pd.DataFrame(bucket_data)
        
        if df.empty:
            # Handle case where no buckets were found or API call failed
            logging.warning("No bucket data to export - creating empty report")
            # Create a DataFrame with just headers to show the expected structure
            df = pd.DataFrame(columns=['bucket_name', 'creation_date', 'creation_date_str'])
        
        # Convert timezone-aware datetimes to timezone-naive so Excel (openpyxl) doesn’t error
        if 'creation_date' in df.columns and not df['creation_date'].empty:
            # Pandas helper: remove timezone info; keeps local (UTC) value
            df['creation_date'] = pd.to_datetime(df['creation_date']).dt.tz_localize(None)

        # Add metadata columns for audit purposes
        # These help auditors understand when and how the report was generated
        df['report_generated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        df['total_buckets_found'] = len(bucket_data)
        
        # Export to Excel file
        # Excel format is preferred by auditors and compliance teams
        df.to_excel(filename, index=False, sheet_name='S3_Buckets')
        
        logging.info(f"Excel report saved as: {filename}")
        logging.info(f"Report contains {len(bucket_data)} bucket records")
        
        # Display summary to console for immediate verification
        print(f"\n=== S3 Bucket Summary ===")
        print(f"Total buckets found: {len(bucket_data)}")
        print(f"Report saved to: {filename}")
        
        if bucket_data:
            print(f"\nSample buckets:")
            # Show first few buckets as a preview
            for i, bucket in enumerate(bucket_data[:3]):
                print(f"  {i+1}. {bucket['bucket_name']} (created: {bucket['creation_date_str']})")
            if len(bucket_data) > 3:
                print(f"  ... and {len(bucket_data) - 3} more")
        
    except Exception as e:
        logging.error(f"Failed to create Excel report: {str(e)}")
        print(f"Error creating report: {str(e)}")

def main():
    """
    Main execution function - orchestrates the entire process.
    """
    logging.info("=== Starting S3 Bucket Audit Script ===")
    
    # Record start time for performance tracking
    start_time = datetime.now()
    
    try:
        # Step 1: Retrieve bucket data from AWS
        logging.info("Step 1: Retrieving S3 bucket information...")
        buckets = get_s3_buckets()
        
        # Step 2: Create Excel report for auditors
        logging.info("Step 2: Generating Excel compliance report...")
        create_excel_report(buckets)
        
        # Calculate and log execution time for performance monitoring
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        logging.info(f"Script completed successfully in {execution_time:.2f} seconds")
        logging.info("=== S3 Bucket Audit Complete ===")
        
        # Exit with success code
        sys.exit(0)
        
    except Exception as e:
        # Handle any unexpected errors gracefully
        logging.error(f"Script failed with error: {str(e)}")
        print(f"Script failed: {str(e)}")
        # Exit with error code to indicate failure to calling systems
        sys.exit(1)

# Standard Python idiom - only run main() if script is executed directly
# This allows the script to be imported as a module without auto-execution
if __name__ == "__main__":
    main()
