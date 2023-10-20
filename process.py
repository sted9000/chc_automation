import sqlite3
import pdftotext
import yaml
from regex import find_store, find_lane_total_2, find_complete_per, find_net_sales, find_customer_count, \
    find_late_clock_out_times, find_over_short


def process_hme(download):
    # open the pdf
    with open(download, "rb") as f:
        pdf = pdftotext.PDF(f)

    # first page
    text = (pdf[0].replace("\n", " "))

    # store
    store = download.split('-')[1]

    # ave time
    ave_time = find_lane_total_2(text)

    # convert mm:ss string to seconds int
    ave_time = int(ave_time.split(':')[0]) * 60 + int(ave_time.split(':')[1])

    # connect to database
    conn = sqlite3.connect('db.db')
    cursor = conn.cursor()

    # insert into database
    cursor.execute('''
        INSERT INTO hme (store, metric, value)
        VALUES (?, ?, ?)
        ''', (store, 'ave_time', ave_time))

    # commit and close connection
    conn.commit()
    conn.close()


def process_jolt(download):
    # open the pdf
    with open(download, "rb") as f:
        pdf = pdftotext.PDF(f)

    # first page
    text = (pdf[0].replace("\n", " "))

    # jolt store id
    store_id = yaml.safe_load(open("config.yml"))["jolt_store_id"]

    # connect to database
    conn = sqlite3.connect('db.db')
    cursor = conn.cursor()

    for key, value in store_id.items():
        # complete %
        complete_per_str = find_complete_per(text, value)

        # convert xx.xx% string to float
        complete_per = float(complete_per_str.replace('%', ''))

        # insert into database
        cursor.execute('''
            INSERT INTO jolt (store, metric, value)
            VALUES (?, ?, ?)
            ''', (key, 'complete', complete_per))

    # commit and close connection
    conn.commit()
    conn.close()


def process_sales(download):
    # open the pdf
    with open(download, "rb") as f:
        pdf = pdftotext.PDF(f)

    # page of the pdf to parse for each store
    sales_summary_config = yaml.safe_load(open("config.yml"))["sales_summary"]

    # connect to database
    conn = sqlite3.connect('db.db')
    cursor = conn.cursor()

    for key, value in sales_summary_config.items():
        # net sales
        net_sales = find_net_sales(pdf[value])
        cursor.execute('''
            INSERT INTO sales (store, metric, value)
            VALUES (?, ?, ?)
            ''', (key, 'net_sales', net_sales))

        # customer count
        customer_count = find_customer_count(pdf[value])
        cursor.execute('''
        INSERT INTO sales (store, metric, value)
        VALUES (?, ?, ?)
        ''', (key, 'customer_count', customer_count))

    # commit and close connection
    conn.commit()
    conn.close()


def process_timecard(download):
    # open the pdf
    with open(download, "rb") as f:
        pdf = pdftotext.PDF(f)

    # late clock out times
    late_clock_out_times = []

    # number of pages in the pdf
    num_pages = len(pdf)

    # iterate through each page of the pdf
    for page in range(num_pages):

        if find_late_clock_out_times(pdf[page]):
            # find the store name
            store = find_store(pdf[page])

            # find the late clock out times
            late_clock_out_times.append(store)

    # count the number of times each store is late
    late_clock_out_times = {i: late_clock_out_times.count(i) for i in late_clock_out_times}
    print(late_clock_out_times)

    # connect to database
    conn = sqlite3.connect('db.db')
    cursor = conn.cursor()

    # insert into database
    store_id = yaml.safe_load(open("config.yml"))["store_id"]
    # iterate through each store key
    for key in store_id.keys():
        # if the store is in the late clock out times dictionary
        if key in late_clock_out_times.keys():
            # insert into database
            cursor.execute('''
                INSERT INTO timecard (store, metric, value)
                VALUES (?, ?, ?)
                ''', (key, 'late_clock_out_times', late_clock_out_times[key]))
        else:
            # insert into database
            cursor.execute('''
                INSERT INTO timecard (store, metric, value)
                VALUES (?, ?, ?)
                ''', (key, 'late_clock_out_times', 0))

    # commit and close connection
    conn.commit()
    conn.close()


def process_till_history(download):
    # open the pdf
    with open(download, "rb") as f:
        pdf = pdftotext.PDF(f)

    # page of the pdf to parse for each store
    till_history_page = yaml.safe_load(open("config.yml"))["till_history_page"]

    # connect to database
    conn = sqlite3.connect('db.db')
    cursor = conn.cursor()

    for key, value in till_history_page.items():
        # over/short
        over_short = find_over_short(pdf[value])
        cursor.execute('''
            INSERT INTO sales (store, metric, value)
            VALUES (?, ?, ?)
            ''', (key, 'over_short', over_short))

    # commit and close connection
    conn.commit()
    conn.close()
