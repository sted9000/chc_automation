import datetime
import os
import sqlite3
import boto3
import yaml
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient, Mail
from process import process_hme, process_jolt, process_sales, process_timecard, process_till_history
from utils import create_database

load_dotenv()
config = yaml.safe_load(open("config.yml"))
files_to_process = config['files_to_process']
data_dir = config['data_dir']
yesterday_obj = datetime.datetime.now() - datetime.timedelta(days=1)
yesterday = yesterday_obj.strftime("%Y-%m-%d")


def download_s3_files(file_names, date, temp_storage_dir):
    # Format the files to process
    files = [f"{x['prefix']}-{date}{x['extension']}" for x in file_names]

    # Download each file
    downloaded = []
    for file in files:

        # Set a place to store the file temporarily
        local_path = os.path.join(temp_storage_dir, file)

        # Download the file from S3
        try:
            s3 = boto3.client('s3')
            s3.download_file(os.getenv("S3_BUCKET"), file, local_path)
            downloaded.append(file)
            print(f'Downloaded {file}')
        except Exception as e:
            print(f'File not found {file}')
            continue

    return downloaded


def check_db(db_path):
    # Check if the database exists
    if not os.path.exists(db_path):
        # Create the database
        create_database()


def process_downloaded_files(files, temp_storage_dir):
    # Process each file
    for file in files:

        # Set the path
        file = os.path.join(temp_storage_dir, file)

        # Open, parse and insert the values into the database
        if 'hme' in file:
            process_hme(file, yesterday)
        elif 'jolt' in file:
            process_jolt(file, yesterday)
        elif 'sales' in file:
            process_sales(file, yesterday)
        elif 'timecard' in file:
            process_timecard(file, yesterday)
        elif 'till-history' in file:
            process_till_history(file, yesterday)


def delete_downloaded_files(files, temp_storage_dir):
    # Delete each file
    for file in files:
        # Set the path
        download = os.path.join(temp_storage_dir, file)
        # Delete the file
        os.remove(download)


def query_db():
    # Connect to the database
    conn = sqlite3.connect('db.db')
    cursor = conn.cursor()

    """Query the database"""
    cursor.execute(f"SELECT * FROM sales WHERE date = '{yesterday}'")
    sales = cursor.fetchall()
    cursor.execute(f"SELECT * FROM till_history WHERE date = '{yesterday}'")
    till = cursor.fetchall()
    cursor.execute(f"SELECT * FROM timecard WHERE date = '{yesterday}'")
    timecard = cursor.fetchall()
    cursor.execute(f"SELECT * FROM jolt WHERE date = '{yesterday}'")
    jolt = cursor.fetchall()
    cursor.execute(f"SELECT * FROM hme WHERE date = '{yesterday}'")
    hme = cursor.fetchall()

    # Close the connection
    conn.close()

    return {'sales': sales, 'till': till, 'timecard': timecard, 'jolt': jolt, 'hme': hme}


def format_queries(query_results):

    sales = query_results['sales']
    till = query_results['till']
    timecard = query_results['timecard']
    jolt = query_results['jolt']
    hme = query_results['hme']

    """Format Query Results"""
    # sales
    sales_dict = {'ek': {}, 'bw': {}, 'sd': {}, 'vr': {}}
    for index, store, metric, value, date, created_at in sales:
        sales_dict[store][metric] = value

    # till
    till_dict = {'ek': {}, 'bw': {}, 'sd': {}, 'vr': {}}
    for index, store, metric, value, date, created_at in till:
        till_dict[store][metric] = value

    # timecard
    timecard_dict = {'ek': 0, 'bw': 0, 'sd': 0, 'vr': 0}
    print(f'timecard: {timecard}')
    for index, store, employee, time, date, created_at in timecard:
        print(f'store: {store}')
        timecard_dict[store] += 1

    # jolt
    jolt_dict = {'ek': {}, 'bw': {}, 'sd': {}, 'vr': {}}
    for index, store, metric, value, date, created_at in jolt:
        jolt_dict[store][metric] = value

    # hme
    hme_dict = {'ek': {}, 'bw': {}, 'sd': {}, 'vr': {}}
    for index, store, metric, value, date, created_at in hme:
        # format seconds to minutes and seconds (mm:ss)
        if metric == 'ave_time':
            value = str(datetime.timedelta(seconds=value))
        hme_dict[store][metric] = value

    return {'sales': sales_dict, 'till': till_dict, 'timecard': timecard_dict, 'jolt': jolt_dict, 'hme': hme_dict}


def format_html(queries):

    # first format the queries into a dictionary
    formatted_queries = format_queries(queries)

    # computed values from the queries
    # compute donation rate
    donation_rate = {'ek': 0, 'bw': 0, 'sd': 0, 'vr': 0}
    for store in formatted_queries['sales'].keys():
        rate = formatted_queries['sales'][store]['donation_count'] / formatted_queries['sales'][store]['customer_count']
        donation_rate[store] = "{:.0%}".format(rate)

    # combined sales for all the stores
    combined_sales = 0
    for store in formatted_queries['sales'].keys():
        combined_sales += formatted_queries['sales'][store]['net_sales']
    # format dollars with two decimal places
    combined_sales = float("{:.2f}".format(combined_sales))

    # total for customer count for all stores
    combined_customer_count = 0
    for store in formatted_queries['sales'].keys():
        combined_customer_count += formatted_queries['sales'][store]['customer_count']

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
            # "                <td {styles[td]}>{timecard[bw]}</td>\n"
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
            # "                <td {styles[td]}>{timecard[sd]}</td>\n"
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
            # "                <td {styles[td]}>{timecard[ek]}</td>\n"
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
            # "                <td {styles[td]}>{timecard[vr]}</td>\n"
            "            </tr>\n"
            "            <tr>\n"
            "                <th {styles[th]}>Total</th>\n"
            "                <td {styles[td]}>{combined_sales}</td>\n"
            "                <td {styles[td]}>{combined_customer_count}</td>\n"
            "            </td>\n"
            "        </tbody>\n"
            "    </table>\n"
            "    ").format(styles=styles, sales=formatted_queries['sales'], till=formatted_queries['till'], timecard=formatted_queries['timecard'], jolt=formatted_queries['jolt'], hme=formatted_queries['hme'], donation_rate=donation_rate, combined_sales=combined_sales, combined_customer_count=combined_customer_count)

    return html


def send_email(html_content):
    # Send email
    message = Mail(
        from_email=os.getenv("SENDGRID_EMAIL"),
        to_emails=os.getenv("CLIENT_EMAIL"),
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
        print(e.message)


if __name__ == "__main__":
    downloads = download_s3_files(files_to_process, yesterday, data_dir)
    check_db('db.db')
    process_downloaded_files(downloads, data_dir)
    delete_downloaded_files(downloads, data_dir)

    # check to see if all the desired files were downloaded and processed
    if len(downloads) != len(files_to_process):
        email_body = f'Not all files were downloaded and processed.\n\nThe following files were not processed ' \
                        f'correctly:\n'
        for file in files_to_process:
            if file['prefix'] not in downloads:
                email_body += f"{file['prefix']}-{yesterday}{file['extension']}\n"
        # add my name to the end of the message
        email_body += '\n\n--\n\nThis message was sent by the CHC Daily Report Bot.'
        send_email(email_body)

    else:
        queries = query_db()
        email_body = format_html(queries)
        send_email(email_body)
