import sqlite3

con = sqlite3.connect("nexttech_calculator.db") 
c = con.cursor()

for table in ['machines', 'operations', 'processes', 'post_processes']:
    c.execute(f"PRAGMA table_info({table})")
    print(f"Columns in {table}:")
    for column in c.fetchall():
        print(column)
    print("\n")




