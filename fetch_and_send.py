import datetime
import os
import sqlite3
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv
from utils import format_html
load_dotenv()

# Get info from db
conn = sqlite3.connect('db.db')
cursor = conn.cursor()
cursor.execute('''
SELECT * FROM sales_summary
WHERE date >= datetime('now', '-36 hours')
''')
rows = cursor.fetchall()
conn.close()

# Convert query to dict
stores = {'ek': {}, 'bw': {}, 'sd': {}, 'vr': {}}
for index, store, metric, value, date in rows:
    stores[store][metric] = value

# Send email
message = Mail(
    from_email=os.getenv("SENDGRID_EMAIL"),
    to_emails=os.getenv("CLIENT_EMAIL"),
    subject=f'CHC Daily Report -- {datetime.datetime.now().strftime("%b %d, %Y")}',
    html_content=format_html(stores))
try:
    sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
    response = sg.send(message)
    print(response.status_code)
    print(response.body)
    print(response.headers)
except Exception as e:
    print(e.message)

print("Email sent successfully!")
