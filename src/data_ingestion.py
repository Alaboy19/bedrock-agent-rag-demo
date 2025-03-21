import boto3
import sys
import os

if len(sys.argv) < 2:
    print("Error: S3 bucket name not provided.")
    sys.exit(1)

bucket_name = sys.argv[1]
s3 = boto3.client("s3")

# Path to the data folder in the parent directory
data_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")

if not os.path.exists(data_folder):
    print(f"Error: Data folder '{data_folder}' does not exist.")
    sys.exit(1)

# Get all files in the data folder
files_to_upload = [os.path.join(data_folder, file) for file in os.listdir(data_folder) if os.path.isfile(os.path.join(data_folder, file))]

if not files_to_upload:
    print(f"Error: No files found in the '{data_folder}' folder.")
    sys.exit(1)

# Upload each file to S3
for file in files_to_upload:
    file_name = os.path.basename(file)  # Get the file name without the path
    s3.upload_file(file, bucket_name, file_name)
    print(f"✅ Uploaded {file_name} to {bucket_name}")