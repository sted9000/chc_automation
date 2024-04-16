import datetime
import os
import sqlite3
import boto3
import yaml
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient, Mail, To
from process import process_hme, process_jolt, process_sales, process_till, process_timecard
from utils import create_database

load_dotenv()
config = yaml.safe_load(open("config.yml"))
db_path = config['db_path']
stores = list(config['stores'].keys())
reports = config['reports']
data_dir = config['data_dir']
yesterday_obj = datetime.datetime.now() - datetime.timedelta(days=1)
yesterday = yesterday_obj.strftime("%Y-%m-%d")


def download_s3_files():

    files_to_download = []

    # the keys of the reports dictionary are the names of the reports
    for report in reports.keys():

        # check that the reports are enabled
        if reports[report]['enabled']:

            # some reports are per store, some are not
            if reports[report]['per_store']:
                for store in stores:
                    files_to_download.append(f'{reports[report]["filename"]}-{store}-{yesterday}{reports[report]["file_extension"]}')
            else:
                files_to_download.append(f'{reports[report]["filename"]}-{yesterday}{reports[report]["file_extension"]}')

    downloaded = []
    failed = []

    # Download each file
    for file in files_to_download:

        # Set a place to store the file temporarily
        local_path = os.path.join(data_dir, file)

        # Download the file from S3
        try:
            s3 = boto3.client('s3')
            s3.download_file(os.getenv("S3_BUCKET"), file, local_path)
            downloaded.append(file)
            print(f'Downloaded {file}')
        except Exception as e:
            print(f'Failed to download {file}')
            print(e)
            failed.append(file)
            continue

    return downloaded, failed


def check_db():
    # Check if the database exists
    if not os.path.exists(db_path):
        # Create the database
        create_database()


def process_downloaded_files(files_to_process):
    # Process each file
    for file in files_to_process:

        # Set the path
        file = os.path.join(data_dir, file)

        # Open, parse and insert the values into the database
        if 'hme' in file:
            process_hme(file, yesterday)
        elif 'jolt' in file:
            process_jolt(file, yesterday)
        elif 'sales' in file:
            process_sales(file, yesterday)
        elif 'timecard' in file:
            process_timecard(file, yesterday)
        elif 'till' in file:
            process_till(file, yesterday)


def delete_downloaded_files(files_to_delete):
    # Delete each file
    for file in files_to_delete:
        # Delete the file
        os.remove(os.path.join(data_dir, file))


def query_db():
    # Dictionary to store the query results
    results = {}

    # Connect to the database
    conn = sqlite3.connect('db.db')
    cursor = conn.cursor()

    """Query database for yesterday's data"""
    for report in reports.keys():
        # report is enabled
        if reports[report]['enabled']:
            if report not in results:
                results[report] = {}
            for store in stores:
                if store not in results[report]:
                    results[report][store] = {}
                for metric in reports[report]['metrics']:
                    cursor.execute(
                        f"SELECT * FROM {report} WHERE date = '{yesterday}' AND store = '{store}' AND metric = '{metric}'")
                    result = cursor.fetchone()
                    if metric == 'refunds':
                        print(f'refunds: {result} store: {store}')
                    if result is None:
                        results[report][store][metric] = None
                    else:
                        results[report][store][metric] = result[3]

    # Close the connection
    conn.close()

    return results


def compute_metrics():

    # compute donation rate
    donation_rate = {'ek': 0, 'bw': 0, 'sd': 0, 'vr': 0}
    for store in queries['sales'].keys():
        # make sure there are no division by zero errors
        if queries['sales'][store]['customer_count'] == 0:
            donation_rate[store] = 0
        # make sure none of the values are None
        elif None in [queries['sales'][store]['donation_count'],
                      queries['sales'][store]['customer_count']]:
            donation_rate[store] = None
        else:
            rate = queries['sales'][store]['donation_count'] / queries['sales'][store][
                'customer_count']
            donation_rate[store] = "{:.0%}".format(rate)

    # combined sales for all the stores
    combined_sales = 0
    for store in queries['sales'].keys():
        # make sure none of the values are None
        if queries['sales'][store]['net_sales'] is None:
            combined_sales = None
            break

        combined_sales += queries['sales'][store]['net_sales']
        # format dollars with two decimal places
        combined_sales = float("{:.2f}".format(combined_sales))

    # total for customer count for all stores
    combined_customer_count = 0
    for store in queries['sales'].keys():
        # make sure none of the values are '?'
        if queries['sales'][store]['customer_count'] is None:
            combined_customer_count = None
            break
        combined_customer_count += queries['sales'][store]['customer_count']

    # format hme from seconds to mm:ss
    for store in queries['hme'].keys():
        if queries['hme'][store]['ave_time'] is None:
            queries['hme'][store]['ave_time'] = None
        else:
            queries['hme'][store]['ave_time'] = str(datetime.timedelta(seconds=queries['hme'][store]['ave_time']))

    return {'donation_rate': donation_rate, 'combined_sales': combined_sales,
            'combined_customer_count': combined_customer_count}


def create_error_message(error_items):
    message = ''
    if len(error_items) > 0:
        message += 'The following files were not processed correctly:\n'
        for file in error_items:
            message += f'{file}\n'
    return message


def format_html(error_msg):
    # Set styles
    styles = {
        'table': 'style="border-collapse: collapse; width: 100%;"',
        'th': 'style="border: 1px solid black; padding: 8px; text-align: left; background-color: #f2f2f2;"',
        'td': 'style="border: 1px solid black; padding: 8px; text-align: left;"'
    }

    # Create HTML table
    html = ("\n"
            "    <table {styles[table]}>\n"
            "        <thead>\n"
            "            <tr>\n"
            "                <th {styles[th]}></th>\n"
            "                <th {styles[th]}>Net Sales ($)</th>\n"
            "                <th {styles[th]}>Customer Count (#)</th>\n"
            "                <th {styles[th]}>Labor (%)</th>\n"
            "                <th {styles[th]}>SPLH ($)</th>\n"
            "                <th {styles[th]}>Over/Short ($)</th>\n"
            "                <th {styles[th]}>Jolt Complete (%)</th>\n"
            "                <th {styles[th]}>HME Average (mm:ss)</th>\n"
            "                <th {styles[th]}>Donation (%)</th>\n"
            "                <th {styles[th]}>Refunds ($)</th>\n"
            # "                <th {styles[th]}>Late Clock Outs (#)</th>\n"
            "            </tr>\n"
            "        </thead>\n"
            "        <tbody>\n"
            "            <tr>\n"
            "                <th {styles[th]}>BW</th>\n"
            "                <td {styles[td]}>{sales[bw][net_sales]}</td>\n"
            "                <td {styles[td]}>{sales[bw][customer_count]}</td>\n"
            "                <td {styles[td]}>{sales[bw][labor]}</td>\n"
            "                <td {styles[td]}>{sales[bw][sales_labor]}</td>\n"
            "                <td {styles[td]}>{till[bw][over_short]}</td>\n"
            "                <td {styles[td]}>{jolt[bw][complete]}</td>\n"
            "                <td {styles[td]}>{hme[bw][ave_time]}</td>\n"
            "                <td {styles[td]}>{donation_rate[bw]}</td>\n"
            "                <td {styles[td]}>{sales[bw][refunds]}</td>\n"
            #             "                <td {styles[td]}>{timecard[bw]}</td>\n"
            "            </tr>\n"
            "            <tr>\n"
            "                <th {styles[th]}>SD</th>\n"
            "                <td {styles[td]}>{sales[sd][net_sales]}</td>\n"
            "                <td {styles[td]}>{sales[sd][customer_count]}</td>\n"
            "                <td {styles[td]}>{sales[sd][labor]}</td>\n"
            "                <td {styles[td]}>{sales[sd][sales_labor]}</td>\n"
            "                <td {styles[td]}>{till[sd][over_short]}</td>\n"
            "                <td {styles[td]}>{jolt[sd][complete]}</td>\n"
            "                <td {styles[td]}>{hme[sd][ave_time]}</td>\n"
            "                <td {styles[td]}>{donation_rate[sd]}</td>\n"
            "                <td {styles[td]}>{sales[sd][refunds]}</td>\n"
            #             "                <td {styles[td]}>{timecard[sd]}</td>\n"
            "            </tr>\n"
            "            <tr>\n"
            "                <th {styles[th]}>EK</th>\n"
            "                <td {styles[td]}>{sales[ek][net_sales]}</td>\n"
            "                <td {styles[td]}>{sales[ek][customer_count]}</td>\n"
            "                <td {styles[td]}>{sales[ek][labor]}</td>\n"
            "                <td {styles[td]}>{sales[ek][sales_labor]}</td>\n"
            "                <td {styles[td]}>{till[ek][over_short]}</td>\n"
            "                <td {styles[td]}>{jolt[ek][complete]}</td>\n"
            "                <td {styles[td]}>{hme[ek][ave_time]}</td>\n"
            "                <td {styles[td]}>{donation_rate[ek]}</td>\n"
            "                <td {styles[td]}>{sales[ek][refunds]}</td>\n"
            #             "                <td {styles[td]}>{timecard[ek]}</td>\n"
            "            </tr>\n"
            "            <tr>\n"
            "                <th {styles[th]}>VR</th>\n"
            "                <td {styles[td]}>{sales[vr][net_sales]}</td>\n"
            "                <td {styles[td]}>{sales[vr][customer_count]}</td>\n"
            "                <td {styles[td]}>{sales[vr][labor]}</td>\n"
            "                <td {styles[td]}>{sales[vr][sales_labor]}</td>\n"
            "                <td {styles[td]}>{till[vr][over_short]}</td>\n"
            "                <td {styles[td]}>{jolt[vr][complete]}</td>\n"
            "                <td {styles[td]}>{hme[vr][ave_time]}</td>\n"
            "                <td {styles[td]}>{donation_rate[vr]}</td>\n"
            "                <td {styles[td]}>{sales[vr][refunds]}</td>\n"
            #             "                <td {styles[td]}>{timecard[vr]}</td>\n"
            "            </tr>\n"
            "            <tr>\n"
            "                <th {styles[th]}>Total</th>\n"
            "                <td {styles[td]}>{combined_sales}</td>\n"
            "                <td {styles[td]}>{combined_customer_count}</td>\n"
            "            </td>\n"
            "        </tbody>\n"
            "    </table>\n"
            "\n"
            "\n"
            "<p>{errorMsg}</p>\n"
            "\n"
            "\n"
            "<p>These figures are for {yesterday}</p>\n"
            "<p>Processed by CHC Daily Report Bot</p>\n"
            "<p>Thank you, Come again</p>\n"
            "    ").format(styles=styles, sales=queries['sales'], till=queries['till'], jolt=queries['jolt'],
                           hme=queries['hme'], donation_rate=computed_metrics['donation_rate'],
                           combined_sales=computed_metrics['combined_sales'],
                           combined_customer_count=computed_metrics['combined_customer_count'], errorMsg=error_msg,
                           yesterday=yesterday_obj.strftime("%b %d, %Y"))

    return html


def send_email(html_content):
    # Send email
    message = Mail(
        from_email=os.getenv("SENDGRID_EMAIL"),
        to_emails=[To(os.getenv("CLIENT_EMAIL")), To(os.getenv("SENDGRID_EMAIL"))],
        subject=f'CHC Daily Report -- {yesterday_obj.strftime("%b %d, %Y")}',
        html_content=html_content
    )
    try:
        sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e)


if __name__ == "__main__":

    # download the files from s3
    downloads, failed_downloads = download_s3_files()

    # check to see if the database exists
    check_db()

    # process the downloaded files
    process_downloaded_files(downloads)

    # delete the downloaded files
    delete_downloaded_files(downloads)

    # query the database
    queries = query_db()

    # computed metrics
    computed_metrics = compute_metrics()

    # error message
    error_message = create_error_message(failed_downloads)

    # format the html
    email_body = format_html(error_message)

    print(email_body)
    #
    # # send the email
    # send_email(email_body)
