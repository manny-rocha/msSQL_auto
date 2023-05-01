import sqlite3

# create a new database and connect to it
conn = sqlite3.connect('peaches.db')

# create a new table called "employees" with a single column called "EmployeeName"
conn.execute('''
    CREATE TABLE employees
    (
        EmployeeName TEXT
    )
''')

# insert a few sample names into the "employees" table
names = [
    'Andrews, Thomas',
    'Burch, Denise',
    'Thomas, Pamela',
    'Barajas, Kathleen',
    'Francis, Anna'
]

for name in names:
    conn.execute("INSERT INTO employees (EmployeeName) VALUES (?)", (name,))

# commit changes and close connection
conn.commit()
conn.close()
