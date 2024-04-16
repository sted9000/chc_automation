import datetime
import sqlite3
import pdftotext
import yaml
from regex import find_lane_total_2, find_complete_per, find_net_sales, find_customer_count, \
    find_over_short, find_labor, find_sales_labor, find_donation_count, find_clock_out_times, find_refunds


def process_sales(download, date):
    # open the pdf
    with open(download, "rb") as f:
        pdf = pdftotext.PDF(f)
        # https: // github.com / jalan / pdftotext / issues / 110

    # page of the pdf to parse for each store
    sales_summary_config = yaml.safe_load(open("config.yml"))["reports"]["sales"]["page_identifiers"]

    # connect to database
    conn = sqlite3.connect('db.db')
    cursor = conn.cursor()

    for key, value in sales_summary_config.items():
        print(key, value)
        # net sales
        net_sales = find_net_sales(pdf[value])
        cursor.execute('''
            INSERT INTO sales (store, metric, value, date)
            VALUES (?, ?, ?, ?)
            ''', (key, 'net_sales', net_sales, date))

        # customer count
        customer_count = find_customer_count(pdf[value])
        cursor.execute('''
        INSERT INTO sales (store, metric, value, date)
        VALUES (?, ?, ?, ?)
        ''', (key, 'customer_count', customer_count, date))

        # labor
        labor = find_labor(pdf[value])
        cursor.execute('''
        INSERT INTO sales (store, metric, value, date)
        VALUES (?, ?, ?, ?)
        ''', (key, 'labor', labor, date))

        # sales / labor
        sales_labor = find_sales_labor(pdf[value])
        cursor.execute('''
        INSERT INTO sales (store, metric, value, date)
        VALUES (?, ?, ?, ?)
        ''', (key, 'sales_labor', sales_labor, date))

        # donation count
        donation_count = find_donation_count(pdf[value])
        cursor.execute('''
        INSERT INTO sales (store, metric, value, date)
        VALUES (?, ?, ?, ?)
        ''', (key, 'donation_count', donation_count, date))

        # refunds
        refunds = find_refunds(pdf[value])
        print(f"refunds: {refunds}, store: {key}")
        cursor.execute('''
        INSERT INTO sales (store, metric, value, date)
        VALUES (?, ?, ?, ?)
        ''', (key, 'refunds', refunds, date))

    # commit and close connection
    conn.commit()
    conn.close()


def process_till(download, date):
    # print('process_till')
    # open the pdf
    with open(download, "rb") as f:
        pdf = pdftotext.PDF(f, physical=True)

    # page of the pdf to parse for each store
    till_page = yaml.safe_load(open("config.yml"))["reports"]["till"]["page_identifiers"]
    # print(till_page)
    # connect to database
    conn = sqlite3.connect('db.db')
    cursor = conn.cursor()

    for key, value in till_page.items():
        # print(key, value)
        # over/short
        over_short = find_over_short(pdf[value])
        # print(over_short)
        cursor.execute('''
            INSERT INTO till (store, metric, value, date)
            VALUES (?, ?, ?, ?)
            ''', (key, 'over_short', over_short, date))

    # commit and close connection
    conn.commit()
    conn.close()


def process_timecard(download, date):
    # open the pdf
    with open(download, "rb") as f:
        pdf = pdftotext.PDF(f)

    # late clock out times
    late_clock_out_times = []

    # number of pages in the pdf
    num_pages = len(pdf)

    # connect to database
    conn = sqlite3.connect('db.db')
    cursor = conn.cursor()

    # iterate through each page of the pdf
    for page in range(num_pages):

        # find the clock out times
        clock_out_times = find_clock_out_times(pdf[page])

        # for each time
        for time in clock_out_times:

            # turn time into datetime.time object
            time = datetime.datetime.strptime(time, '%I:%M %p').time()

            # if time is between 01:50 AM and 02:10 AM
            if datetime.time(1, 50) < time < datetime.time(2, 10):
                # find the store name
                store = find_store(pdf[page])

                # find the employee name
                employee = find_late_clock_out_employee(pdf[page])

                # time that is compatible with database
                dt_str = time.strftime('%Y-%m-%d %H:%M:%S')

                print(f'{employee} clocked out at {time} at {store}')
                # insert into database
                cursor.execute('''
                    INSERT INTO timecard (store, employee, clock_out, date)
                    VALUES (?, ?, ?, ?)
                    ''', (store, employee, dt_str, date))

    # commit and close connection
    conn.commit()
    conn.close()


def process_hme(download, date):
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
        INSERT INTO hme (store, metric, value, date)
        VALUES (?, ?, ?, ?)
        ''', (store, 'ave_time', ave_time, date))

    # commit and close connection
    conn.commit()
    conn.close()


def process_jolt(download, date):
    # open the pdf
    with open(download, "rb") as f:
        pdf = pdftotext.PDF(f)

    # first page
    text = (pdf[0].replace("\n", " "))

    # jolt store id
    store_id = yaml.safe_load(open("config.yml"))["reports"]["jolt"]["page_identifiers"]

    # connect to database
    conn = sqlite3.connect('db.db')
    cursor = conn.cursor()

    for key, value in store_id.items():
        # complete %
        complete_per_str = find_complete_per(text, value)

        # break if no complete % found
        if complete_per_str is None:
            break

        # convert xx.xx% string to float
        complete_per = float(complete_per_str.replace('%', ''))

        # insert into database
        cursor.execute('''
            INSERT INTO jolt (store, metric, value, date)
            VALUES (?, ?, ?, ?)
            ''', (key, 'complete', complete_per, date))

    # commit and close connection
    conn.commit()
    conn.close()
