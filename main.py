import os
import boto3
import sqlite3
import pdftotext
import yaml
from utils import parse_hme, parse_jolt, parse_sales_summary, insert_hme, insert_jolt, insert_sales_summary
from dotenv import load_dotenv
load_dotenv()
config = yaml.safe_load(open("config.yml"))

# Parse the webhook
file_name = 'hme.pdf'
local_path = os.path.join(os.getenv("DATA_DIR"), file_name)

# Download the file from S3
s3 = boto3.client('s3')
s3.download_file(os.getenv("S3_BUCKET"), file_name, local_path)

# Open the file
with open(local_path, "rb") as f:
    pdf = pdftotext.PDF(f)

# Parse the file
parsed_file = None
if 'hme' in file_name:
    parsed_file = parse_hme(pdf)
elif 'jolt' in file_name:
    parsed_file = parse_jolt(pdf)
elif 'sales' in file_name:
    parsed_file = parse_sales_summary(pdf)

# Connect to the database
conn = sqlite3.connect('db.db')
cursor = conn.cursor()

if 'hme' in file_name:
    insert_hme(parsed_file, cursor)
elif 'jolt' in file_name:
    insert_jolt(parsed_file, cursor)
elif 'sales' in file_name:
    insert_sales_summary(parsed_file, cursor)

# Close the connection
conn.commit()

# Delete the pdf file
os.remove(local_path)