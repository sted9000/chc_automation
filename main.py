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


def download_s3_files(files, date, temp_storage_dir):
    # Format the files to process
    files = [f"{x['prefix']}-{date}{x['extension']}" for x in files]

    # Download each file
    for file in files:

        # Set a place to store the file temporarily
        local_path = os.path.join(temp_storage_dir, file)

        # Download the file from S3
        try:
            s3 = boto3.client('s3')
            s3.download_file(os.getenv("S3_BUCKET"), file, local_path)
            print(f'Downloaded {file}')
        except Exception as e:
            print(f'File not found {file}')
            continue


def check_db(db_path):
    # Check if the database exists
    if not os.path.exists(db_path):
        # Create the database
        create_database()


def process_downloaded_files(temp_storage_dir):
    # get the file names from data_dir
    downloads = os.listdir(temp_storage_dir)

    # Process each file
    for download in downloads:

        # Set the path
        download = os.path.join(temp_storage_dir, download)

        # Open, parse and insert the values into the database
        if 'hme' in download:
            process_hme(download, yesterday)
        elif 'jolt' in download:
            process_jolt(download, yesterday)
        elif 'sales' in download:
            process_sales(download, yesterday)
        elif 'timecard' in download:
            process_timecard(download, yesterday)
        elif 'till-history' in download:
            process_till_history(download, yesterday)


def delete_downloaded_files(temp_storage_dir):
    # get the file names from data_dir
    downloads = os.listdir(temp_storage_dir)

    # Delete each file
    for download in downloads:
        # Set the path
        download = os.path.join(temp_storage_dir, download)
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
    till_history = cursor.fetchall()
    cursor.execute(f"SELECT * FROM timecard WHERE date = '{yesterday}'")
    timecard = cursor.fetchall()
    cursor.execute(f"SELECT * FROM jolt WHERE date = '{yesterday}'")
    jolt = cursor.fetchall()
    cursor.execute(f"SELECT * FROM hme WHERE date = '{yesterday}'")
    hme = cursor.fetchall()

    """Format Query Results"""
    # sales
    sales_dict = {'ek': {}, 'bw': {}, 'sd': {}, 'vr': {}}
    for index, store, metric, value, date, created_at in sales:
        sales_dict[store][metric] = value

    # till_history
    till_history_dict = {'ek': {}, 'bw': {}, 'sd': {}, 'vr': {}}
    for index, store, metric, value, date, created_at in till_history:
        till_history_dict[store][metric] = value

    # timecard
    timecard_dict = {'ek': 0, 'bw': 0, 'sd': 0, 'vr': 0}
    for index, store, employee, time, date, created_at in timecard:
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

    # Close the connection
    conn.close()

    return {'sales': sales_dict, 'till_history': till_history_dict, 'timecard': timecard_dict, 'jolt': jolt_dict, 'hme': hme_dict}


def set_computed_values(data_dict):
    """Computed values"""
    cmpd_dict = {'donation_rate': {}, 'customer_count': 0, 'sales': 0}

    # compute donation rate
    for store in data_dict['sales'].keys():
        donation_rate = data_dict['sales'][store]['donation_count'] / data_dict['sales'][store]['customer_count']
        cmpd_dict['donation_rate'][store] = "{:.0%}".format(donation_rate)

    # combined sales for all the stores
    cmpd_dict['sales'] = 0
    for store in data_dict['sales'].keys():
        sales = data_dict['sales'][store]['net_sales']
        cmpd_dict['sales'] += sales
    # format dollars with two decimal places
    cmpd_dict['sales'] = float("{:.2f}".format(cmpd_dict['sales']))

    # total for customer count for all stores
    cmpd_dict['customer_count'] = 0
    for store in data_dict['sales'].keys():
        cmpd_dict['customer_count'] += data_dict['sales'][store]['customer_count']

    return cmpd_dict


def format_html(db, computed):
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
            "                <th {styles[th]}>Late Clock Outs (#)</th>\n"
            "            </tr>\n"
            "        </thead>\n"
            "        <tbody>\n"
            "            <tr>\n"
            "                <th {styles[th]}>BW</th>\n"
            "                <td {styles[td]}>{db[sales][bw][net_sales]}</td>\n"
            "                <td {styles[td]}>{db[sales][bw][customer_count]}</td>\n"
            "                <td {styles[td]}>{db[sales][bw][labor]}</td>\n"
            "                <td {styles[td]}>{db[sales][bw][sales_labor]}</td>\n"
            "                <td {styles[td]}>{db[till_history][bw][over_short]}</td>\n"
            "                <td {styles[td]}>{db[jolt][bw][complete]}</td>\n"
            "                <td {styles[td]}>{db[hme][bw][ave_time]}</td>\n"
            "                <td {styles[td]}>{computed[donation_rate][bw]}</td>\n"
            "                <td {styles[td]}>{db[timecard][bw]}</td>\n"
            "            </tr>\n"
            "            <tr>\n"
            "                <th {styles[th]}>SD</th>\n"
            "                <td {styles[td]}>{db[sales][sd][net_sales]}</td>\n"
            "                <td {styles[td]}>{db[sales][sd][customer_count]}</td>\n"
            "                <td {styles[td]}>{db[sales][sd][labor]}</td>\n"
            "                <td {styles[td]}>{db[sales][sd][sales_labor]}</td>\n"
            "                <td {styles[td]}>{db[till_history][sd][over_short]}</td>\n"
            "                <td {styles[td]}>{db[jolt][sd][complete]}</td>\n"
            "                <td {styles[td]}>{db[hme][sd][ave_time]}</td>\n"
            "                <td {styles[td]}>{computed[donation_rate][sd]}</td>\n"
            "                <td {styles[td]}>{db[timecard][sd]}</td>\n"
            "            </tr>\n"
            "            <tr>\n"
            "                <th {styles[th]}>EK</th>\n"
            "                <td {styles[td]}>{db[sales][ek][net_sales]}</td>\n"
            "                <td {styles[td]}>{db[sales][ek][customer_count]}</td>\n"
            "                <td {styles[td]}>{db[sales][ek][labor]}</td>\n"
            "                <td {styles[td]}>{db[sales][ek][sales_labor]}</td>\n"
            "                <td {styles[td]}>{db[till_history][ek][over_short]}</td>\n"
            "                <td {styles[td]}>{db[jolt][ek][complete]}</td>\n"
            "                <td {styles[td]}>{db[hme][ek][ave_time]}</td>\n"
            "                <td {styles[td]}>{computed[donation_rate][ek]}</td>\n"
            "                <td {styles[td]}>{db[timecard][ek]}</td>\n"
            "            </tr>\n"
            "            <tr>\n"
            "                <th {styles[th]}>VR</th>\n"
            "                <td {styles[td]}>{db[sales][vr][net_sales]}</td>\n"
            "                <td {styles[td]}>{db[sales][vr][customer_count]}</td>\n"
            "                <td {styles[td]}>{db[sales][vr][labor]}</td>\n"
            "                <td {styles[td]}>{db[sales][vr][sales_labor]}</td>\n"
            "                <td {styles[td]}>{db[till_history][vr][over_short]}</td>\n"
            "                <td {styles[td]}>{db[jolt][vr][complete]}</td>\n"
            "                <td {styles[td]}>{db[hme][vr][ave_time]}</td>\n"
            "                <td {styles[td]}>{computed[donation_rate][vr]}</td>\n"
            "                <td {styles[td]}>{db[timecard][vr]}</td>\n"
            "            </tr>\n"
            "            <tr>\n"
            "                <th {styles[th]}>Total</th>\n"
            "                <td {styles[td]}>{computed[sales]}</td>\n"
            "                <td {styles[td]}>{computed[customer_count]}</td>\n"
            "            </td>\n"
            "        </tbody>\n"
            "    </table>\n"
            "    ").format(styles=styles, db=db, computed=computed)

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
    download_s3_files(files_to_process, yesterday, data_dir)
    check_db('db.db')
    process_downloaded_files(data_dir)
    delete_downloaded_files(data_dir)
    db_dict = query_db()
    computed_dict = set_computed_values(db_dict)
    email_body = format_html(db_dict, computed_dict)
    send_email(email_body)

