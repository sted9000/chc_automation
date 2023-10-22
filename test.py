import datetime

from process import process_timecard, process_till_history, process_sales

download = './data/timecard-2023-10-19.pdf'
# extract the store from the download string

yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
yesterday = yesterday.strftime("%Y-%m-%d")

process_timecard(download, yesterday)