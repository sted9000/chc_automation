import sqlite3


def print_db():
    # Connect to the database
    connection = sqlite3.connect('db.db')

    # Create a cursor object using the cursor() method
    cursor = connection.cursor()

    # Get the list of all tables in the database
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    # Print all tables and their rows
    for table in tables:
        table_name = table[0]
        print(f"Table: {table_name}")

        # Get and print all rows from the table
        cursor.execute(f"SELECT * FROM {table_name};")
        rows = cursor.fetchall()
        for row in rows:
            print(row)

        print("-" * 50)

    # Close the connection
    connection.close()


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



