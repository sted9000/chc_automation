import datetime
import os
import boto3
import yaml
from dotenv import load_dotenv
from process import process_hme, process_jolt, process_sales, process_timecard, process_till_history

load_dotenv()
config = yaml.safe_load(open("config.yml"))
files_to_process = config['files_to_process']
data_dir = config['data_dir']
yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
yesterday = yesterday.strftime("%Y-%m-%d")


def download_s3_files(files, date, temp_storage_dir):
    # Format the files to process
    files = [f"{x['prefix']}-{date}.{x['extension']}" for x in files]

    # Download each file
    for file in files:
        # Set a place to store the file temporarily
        local_path = os.path.join(temp_storage_dir, file)

        # Download the file from S3
        # Todo: Add try catch block here
        s3 = boto3.client('s3')
        s3.download_file(os.getenv("S3_BUCKET"), file, local_path)


def process_downloaded_files(temp_storage_dir):
    # get the file names from data_dir
    downloads = os.listdir(temp_storage_dir)

    # Process each file
    for download in downloads:

        # Set the path
        download = os.path.join(temp_storage_dir, download)

        # Open, parse and insert the values into the database
        if 'hme' in download:
            process_hme(download)
        elif 'jolt' in download:
            process_jolt(download)
        elif 'sales' in download:
            process_sales(download)
        elif 'timecard' in download:
            process_timecard(download)
        elif 'till-history' in download:
            process_till_history(download)


def delete_downloaded_files(temp_storage_dir):
    # get the file names from data_dir
    downloads = os.listdir(temp_storage_dir)

    # Delete each file
    for download in downloads:
        # Set the path
        download = os.path.join(temp_storage_dir, download)
        # Delete the file
        os.remove(download)


if __name__ == "__main__":
    download_s3_files(files_to_process, yesterday, data_dir)
    process_downloaded_files(data_dir)
    delete_downloaded_files(data_dir)
