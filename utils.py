import sqlite3


def print_db(cursor):
    cursor.execute("SELECT * FROM sales_summary")
    rows = cursor.fetchall()
    for row in rows:
        print(row)


def create_database():
    conn = sqlite3.connect('db.db')
    cursor = conn.cursor()
    cursor.executescript('''
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY,
        store TEXT NOT NULL,
        metric TEXT NOT NULL,
        value INTEGER,
        date DATETIME NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    ); 
    
    CREATE TABLE IF NOT EXISTS hme (
        id INTEGER PRIMARY KEY,
        store TEXT NOT NULL,
        metric TEXT NOT NULL,
        value INTEGER,
        date DATETIME NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    ); 
    
    CREATE TABLE IF NOT EXISTS jolt (
        id INTEGER PRIMARY KEY,
        store TEXT NOT NULL,
        metric TEXT NOT NULL,
        value INTEGER,
        date DATETIME NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    ); 
    
    CREATE TABLE IF NOT EXISTS timecard (
        id INTEGER PRIMARY KEY,
        store TEXT NOT NULL,
        employee TEXT NOT NULL,
        clock_out DATETIME NOT NULL,
        date DATETIME NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS till_history (
        id INTEGER PRIMARY KEY,
        store TEXT NOT NULL,
        metric TEXT NOT NULL,
        value INTEGER,
        date DATETIME NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    ''')
    conn.commit()
    conn.close()


def format_html(sales_dict, till_history_dict, timecard_dict, jolt_dict, hme_dict):
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
            "                <td {styles[td]}>{sales[bw][net_sales]}</td>\n"
            "                <td {styles[td]}>{sales[bw][customer_count]}</td>\n"
            "                <td {styles[td]}>{sales[bw][labor]}</td>\n"
            "                <td {styles[td]}>{sales[bw][sales_labor]}</td>\n"
            "                <td {styles[td]}>{till[bw][over_short]}</td>\n"
            "                <td {styles[td]}>{jolt[bw][complete_per]}</td>\n"
            "                <td {styles[td]}>{hme[bw][ave_time]}</td>\n"
            "                <td {styles[td]}>{sales[bw][donation_rate]}</td>\n"
            "                <td {styles[td]}>{timecard[bw]}</td>\n"
            "            </tr>\n"
            "            <tr>\n"
            "                <th {styles[th]}>SD</th>\n"
            "                <td {styles[td]}>{sales[sd][net_sales]}</td>\n"
            "                <td {styles[td]}>{sales[sd][customer_count]}</td>\n"
            "                <td {styles[td]}>{sales[sd][labor]}</td>\n"
            "                <td {styles[td]}>{sales[sd][sales_labor]}</td>\n"
            "                <td {styles[td]}>{till[sd][over_short]}</td>\n"
            "                <td {styles[td]}>{jolt[sd][complete_per]}</td>\n"
            "                <td {styles[td]}>{hme[sd][ave_time]}</td>\n"
            "                <td {styles[td]}>{sales[sd][donation_rate]}</td>\n"
            "                <td {styles[td]}>{timecard[sd]}</td>\n"
            "            </tr>\n"
            "            <tr>\n"
            "                <th {styles[th]}>EK</th>\n"
            "                <td {styles[td]}>{sales[ek][net_sales]}</td>\n"
            "                <td {styles[td]}>{sales[ek][customer_count]}</td>\n"
            "                <td {styles[td]}>{sales[ek][labor]}</td>\n"
            "                <td {styles[td]}>{sales[ek][sales_labor]}</td>\n"
            "                <td {styles[td]}>{till[ek][over_short]}</td>\n"
            "                <td {styles[td]}>{jolt[ek][complete_per]}</td>\n"
            "                <td {styles[td]}>{hme[ek][ave_time]}</td>\n"
            "                <td {styles[td]}>{sales[ek][donation_rate]}</td>\n"
            "                <td {styles[td]}>{timecard[ek]}</td>\n"
            "            </tr>\n"
            "            <tr>\n"
            "                <th {styles[th]}>VR</th>\n"
            "                <td {styles[td]}>{sales[vr][net_sales]}</td>\n"
            "                <td {styles[td]}>{sales[vr][customer_count]}</td>\n"
            "                <td {styles[td]}>{sales[vr][labor]}</td>\n"
            "                <td {styles[td]}>{sales[vr][sales_labor]}</td>\n"
            "                <td {styles[td]}>{till[vr][over_short]}</td>\n"
            "                <td {styles[td]}>{jolt[vr][complete_per]}</td>\n"
            "                <td {styles[td]}>{hme[vr][ave_time]}</td>\n"
            "                <td {styles[td]}>{sales[vr][donation_rate]}</td>\n"
            "                <td {styles[td]}>{timecard[vr]}</td>\n"
            "            </tr>\n"
            "        </tbody>\n"
            "    </table>\n"
            "    ").format(styles=styles, sales=sales_dict, till=till_history_dict, timecard=timecard_dict, jolt=jolt_dict, hme=hme_dict)

    return html
