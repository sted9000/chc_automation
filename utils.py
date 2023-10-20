import sqlite3


def print_db(cursor):
    cursor.execute("SELECT * FROM sales_summary")
    rows = cursor.fetchall()
    for row in rows:
        print(row)


def create_database():
    conn = sqlite3.connect('db.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sales (
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
    
    CREATE TABLE IF NOT EXISTS timecard (
        id INTEGER PRIMARY KEY,
        store TEXT NOT NULL,
        metric TEXT NOT NULL,
        value INTEGER NOT REAL,
        date DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS till_history (
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
