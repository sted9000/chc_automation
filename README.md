# CHC Automation
## Warning
This is a work in progress. Use at your own risk.

## General
Python script to automate the process of downloading and parsing reports from vendors. Webhook to initiate the process is currently not set up. The webhook will include a file name to download, parse, and store in the local sqlite database. A cron job will be set up to run ```fetch_and_send.py``` every day at 5am to email a summary report to the client.

## Configuration File
Create a config.yml file in the root directory with the following format:
```yaml
# config.yml
sales_summary:
  ek: <PAGE_NUMBER_OF_EK_REPORT>
  bw: <PAGE_NUMBER_OF_BW_REPORT>
  sd: <PAGE_NUMBER_OF_SD_REPORT>
  vr: <PAGE_NUMBER_OF_VR_REPORT>

jolt_store_id:
  ek: '<STORE_ID>'
  bw: '<STORE_ID>'
  sd: '<STORE_ID>'
  vr: '<STORE_ID>'
```

## ENV Variables
Create a .env file in the root directory with the following format:

```bash
# .env
SENDGRID_API_KEY='<SENDGRID_API_KEY>'
SENDGRID_EMAIL='<SENDGRID_EMAIL>'
CLIENT_EMAIL='<CLIENT_EMAIL>'
S3_BUCKET='<S3_BUCKET>'
DATA_DIR='<DIRECTORY_TO_STORE_DATA_BEING_PARSED>
```

## TODO
- [ ] Add webhook
- [ ] Set up Raspberry Pi
- [ ] Set up cron job
- [ ] Test