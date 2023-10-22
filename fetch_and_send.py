import datetime
import os
import sqlite3
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv
from utils import format_html

load_dotenv()

"""Get info from db"""
conn = sqlite3.connect('db.db')
cursor = conn.cursor()

# date to query is yesterday
yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')

# sales
cursor.execute(f"SELECT * FROM sales WHERE date = '{yesterday}'")
sales = cursor.fetchall()
sales_dict = {'ek': {}, 'bw': {}, 'sd': {}, 'vr': {}}
for index, store, metric, value, date, created_at in sales:
    sales_dict[store][metric] = value
# compute donation rate
for store in sales_dict.keys():
    sales_dict[store]['donation_rate'] = sales_dict[store]['donation_count'] / sales_dict[store]['customer_count']


# till_history
cursor.execute(f"SELECT * FROM till_history WHERE date = '{yesterday}'")
till_history = cursor.fetchall()
till_history_dict = {'ek': {}, 'bw': {}, 'sd': {}, 'vr': {}}
for index, store, metric, value, date, created_at in till_history:
    till_history_dict[store][metric] = value

# timecard
cursor.execute(f"SELECT * FROM timecard WHERE date = '{yesterday}'")
timecard = cursor.fetchall()
timecard_dict = {'ek': 0, 'bw': 0, 'sd': 0, 'vr': 0}
for index, store, employee, time, date, created_at in timecard:
    timecard_dict[store] += 1

# jolt
cursor.execute(f"SELECT * FROM jolt WHERE date = '{yesterday}'")
jolt = cursor.fetchall()
jolt_dict = {'ek': {}, 'bw': {}, 'sd': {}, 'vr': {}}
for index, store, metric, value, date, created_at in jolt:
    jolt_dict[store][metric] = value

# hme
cursor.execute(f"SELECT * FROM hme WHERE date = '{yesterday}'")
hme = cursor.fetchall()
hme_dict = {'ek': {}, 'bw': {}, 'sd': {}, 'vr': {}}
for index, store, metric, value, date, created_at in hme:
    hme_dict[store][metric] = value

# Close db connection
conn.close()

# Send email
message = Mail(
    from_email=os.getenv("SENDGRID_EMAIL"),
    to_emails=os.getenv("CLIENT_EMAIL"),
    subject=f'CHC Daily Report -- {datetime.datetime.now().strftime("%b %d, %Y")}',
    html_content=format_html(sales_dict, till_history_dict, timecard_dict, jolt_dict, hme_dict))
try:
    sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
    response = sg.send(message)
    print(response.status_code)
    print(response.body)
    print(response.headers)
except Exception as e:
    print(e.message)

print("Email sent successfully!")
