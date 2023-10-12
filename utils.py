import re
import sqlite3

import yaml


def parse_hme(pdf):
    # first page
    text = (pdf[0].replace("\n", " "))

    # store
    store = find_store(text)

    # ave time
    ave_time = find_lane_total_2(text)

    # convert mm:ss string to seconds int
    ave_time = int(ave_time.split(':')[0]) * 60 + int(ave_time.split(':')[1])

    return [{'store': store, 'metric': 'ave_time', 'value': ave_time}]


def parse_jolt(pdf):
    # first page
    text = (pdf[0].replace("\n", " "))

    # jolt store id
    store_id = yaml.safe_load(open("config.yml"))["jolt_store_id"]
    
    items = []
    for key, value in store_id.items():
        # complete %
        complete_per_str = find_complete_per(text, value)

        # convert xx.xx% string to float
        complete_per = float(complete_per_str.replace('%', ''))

        items.append({'store': key, 'metric': 'complete', 'value': complete_per})
        
    return items


def parse_sales_summary(pdf):

    # page of the pdf to parse for each store
    sales_summary_config = yaml.safe_load(open("config.yml"))["sales_summary"]
    
    items = []
    for key, value in sales_summary_config.items():
        # net sales
        net_sales = find_net_sales(pdf[value])
        items.append({'store': key, 'metric': 'net_sales', 'value': net_sales})
        
        # customer count
        customer_count = find_customer_count(pdf[value])
        items.append({'store': key, 'metric': 'customer_count', 'value': customer_count})
               
    return items


"""Parsing with REGEX"""


def find_net_sales(text):
    # regular expression to find the net sales in the example string below
    # example string: 'Count:  177  Net Sales  $2,055.02  Guest Count:  177'
    pattern = r"Net Sales\s+\$([\d,]+\.\d\d)"
    match = re.search(pattern, text)
    if match:
        return float(match.group(1).replace(",", ""))


def find_customer_count(text):
    # regular expression to find the customer count in the example string below
    # example string: 'Net Sales  $2,055.02  Guest Count:  177  Order Average:'
    pattern = r"Guest Count:\s+(\d+)"
    match = re.search(pattern, text)
    if match:
        return int(match.group(1))


def find_store(text):
    # todo: add regex to find the store name in the example string below
    return 'bw'


def find_lane_total_2(text):
    # regular expression to find the lane total 2 ave time in the example string below
    # example string: '11:37  Lane Total 2  169  04:12  9/14/2023 6:28:47 PM 9/14/2023'
    pattern = r"Lane Total 2\s+(\d+)\s+(\d+:\d+)"
    match = re.search(pattern, text)
    if match:
        return match.group(2)


def find_complete_per(text, store_id):
    # regular expression to find the complete % which is the first value in the parentheses after the store id note
    # that the value may be in the format xx.xx% or xx% so the regex must account for both store_id = ['100-',
    # '400-', '200-', '300-'] 100- Bridgewater DQ 21 (45%)  21 (45.65%)  0 (0%)  25 (54.35%)  0 400- Verona DQ  23 (
    # 50%)  23 (50%)  0 (0%)  23 (50%)  0
    pattern = f'{store_id}-' + r".*?\(([\d.%]+)\)"
    match = re.search(pattern, text)
    if match:
        return match.group(1)


r"{}.*?\((\d+)%\)"

"""SQL Database Functions"""


def insert_sales_summary(parsed_values, cursor):
    for parsed_value in parsed_values:
        cursor.execute('''
        INSERT INTO sales_summary (store, metric, value)
        VALUES (?, ?, ?)
        ''', (parsed_value['store'], parsed_value['metric'], parsed_value['value']))


def insert_hme(parsed_values, cursor):
    for parsed_value in parsed_values:
        cursor.execute('''
        INSERT INTO hme (store, metric, value)
        VALUES (?, ?, ?)
        ''', (parsed_value['store'], parsed_value['metric'], parsed_value['value']))


def insert_jolt(parsed_values, cursor):
    for parsed_value in parsed_values:
        cursor.execute('''
        INSERT INTO jolt (store, metric, value)
        VALUES (?, ?, ?)
        ''', (parsed_value['store'], parsed_value['metric'], parsed_value['value']))


def print_db(cursor):
    cursor.execute("SELECT * FROM sales_summary")
    rows = cursor.fetchall()
    for row in rows:
        print(row)


def create_database():
    conn = sqlite3.connect('db.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sales_summary (
        id INTEGER PRIMARY KEY,
        store TEXT NOT NULL,
        metric TEXT NOT NULL,
        value INTEGER NOT REAL,
        date DATETIME DEFAULT CURRENT_TIMESTAMP
    ); 
    
    CREATE TABLE IF NOT EXISTS hme (
        id INTEGER PRIMARY KEY,
        store TEXT NOT NULL,
        metric TEXT NOT NULL,
        value INTEGER NOT REAL,
        date DATETIME DEFAULT CURRENT_TIMESTAMP
    ); 
    
    CREATE TABLE IF NOT EXISTS jolt (
        id INTEGER PRIMARY KEY,
        store TEXT NOT NULL,
        metric TEXT NOT NULL,
        value INTEGER NOT REAL,
        date DATETIME DEFAULT CURRENT_TIMESTAMP
    ); 
    ''')
    conn.commit()
    conn.close()


def format_html(stores):
    # Set styles
    styles = {
        'table': 'style="border-collapse: collapse; width: 100%;"',
        'th': 'style="border: 1px solid black; padding: 8px; text-align: left; background-color: #f2f2f2;"',
        'td': 'style="border: 1px solid black; padding: 8px; text-align: left;"'
    }

    # Create HTML table
    html = """
    <table {styles[table]}>
        <thead>
            <tr>
                <th {styles[th]}></th>
                <th {styles[th]}>Net Sales ($)</th>
                <th {styles[th]}>Customer Count (#)</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <th {styles[th]}>BW</th>
                <td {styles[td]}>{stores[bw][net_sales]}</td>
                <td {styles[td]}>{stores[bw][customer_count]}</td>
            </tr>
            <tr>
                <th {styles[th]}>SD</th>
                <td {styles[td]}>{stores[sd][net_sales]}</td>
                <td {styles[td]}>{stores[sd][customer_count]}</td>
            </tr>
            <tr>
                <th {styles[th]}>EK</th>
                <td {styles[td]}>{stores[ek][net_sales]}</td>
                <td {styles[td]}>{stores[ek][customer_count]}</td>
            </tr>
            <tr>
                <th {styles[th]}>VR</th>
                <td {styles[td]}>{stores[vr][net_sales]}</td>
                <td {styles[td]}>{stores[vr][customer_count]}</td>
            </tr>
        </tbody>
    </table>
    """.format(styles=styles, stores=stores)

    return html
