import sqlite3
import os

# Path to the database file
db_path = 'database/nexttech_calculator.db'

# Check if the database file exists
if not os.path.exists(db_path):
    print(f"Database file {db_path} does not exist.")
    exit(1)

# Create a connection object that represents the database
con = sqlite3.connect(db_path)

# Create a cursor object that is used to interact with the database
cur = con.cursor()

inp = ''
while inp != 'y' and inp != 'n':
    print("WARNING!!! This will drop all tables and reset the databse to its default state as of 30/10/24")
    inp = input('Are you SURE you want to do this? (y/n): ')
if inp == 'y':
    try:
        #Drop tables for clean install
        cur.execute("DROP TABLE IF EXISTS machines;")
        cur.execute("DROP TABLE IF EXISTS materials;")
        cur.execute("DROP TABLE IF EXISTS parts;")
        cur.execute("DROP TABLE IF EXISTS processes;")
        cur.execute("DROP TABLE IF EXISTS post_processes;")
        cur.execute("DROP TABLE IF EXISTS operations;")
        cur.execute("DROP TABLE IF EXISTS calculations;")
    except Exception as e:
        print('Error:', e)

    try:
        #Create table for storing machine variables
        cur.execute("""CREATE TABLE machines (machine_id INT PRIMARY KEY,
                    machine_name TEXT,
                    total_machine_cost INT, 
                    machine_lifetime INT, 
                    cost_of_capital FLOAT, 
                    infrastructure_cost FLOAT,
                    maintenance_cost FLOAT,
                    machine_build_area FLOAT,
                    machine_build_height FLOAT,
                    machine_build_rate INT,
                    machine_uptime FLOAT
                    );""")

    except Exception as e:
        print('Error:', e)

    try:
        #Create table for storing material variables
        cur.execute("""CREATE TABLE materials (material_id INT PRIMARY KEY,
                    material_name TEXT,
                    material_density FLOAT,
                    material_cost FLOAT,
                    in_process INT,
                    for_machine INT);""")
    except Exception as e:
        print('Error:', e)


    try:
        #Create table for storing part variables
        cur.execute("""CREATE TABLE parts (part_id INT PRIMARY KEY,
                    support_material FLOAT);""")
    except Exception as e:
        print('Error:', e)

    try:
        #Create table storing process variables
        cur.execute("""CREATE TABLE processes (process_id INT PRIMARY KEY, 
                    process_name TEXT,
                    packing_policy INT(1), 
                    packing_fraction FLOAT, 
                    recycling_fraction FLOAT,
                    additional_operating_cost FLOAT,
                    consumable_cost_per_build FLOAT,
                    first_time_prep FLOAT,
                    subsequent_prep FLOAT,
                    time_per_build_setup FLOAT,
                    time_per_build_removal FLOAT,
                    time_per_machine_warmup FLOAT,
                    time_per_machine_cooldown FLOAT);""")
    except Exception as e:
        print('Error:', e)

    try:
        #Create table for storing post-process variables
        cur.execute("""CREATE TABLE post_processes (post_process_id INT PRIMARY KEY, 
                    removal_time_constant FLOAT,
                    for_machine INT);""")
    except Exception as e:
        print('Error:', e)

    try:
        #Create table storing operations variables
        cur.execute("""CREATE TABLE operations (operations_id INT PRIMARY KEY, 
                    hours_per_day INT,
                    days_per_week INT,
                    FTE_per_machine FLOAT, 
                    FTE_build_exchange FLOAT, 
                    FTE_support_removal FLOAT,
                    salary_engineer FLOAT,
                    salary_operator FLOAT,
                    salary_technician FLOAT,
                    for_machine INT);""")
    except Exception as e:
        print('Error:', e)

    #Create table for storing calculations
    cur.execute("""CREATE TABLE calculations (calculation_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                date DATETIME DEFAULT CURRENT_TIMESTAMP,
                project_name VARCHAR,
                machine_used INT, 
                material_used INT, 
                parts_made INT, 
                builds_done INT, 
                process_used INT, 
                post_process_used INT, 
                operation_used INT, 
                total_cost FLOAT,
                average_cost FLOAT);""")
    

    #Insert machines into table
    cur.execute("""INSERT INTO machines (machine_id, machine_name, total_machine_cost, machine_lifetime, cost_of_capital, infrastructure_cost, maintenance_cost, machine_build_area, machine_build_height, machine_build_rate, machine_uptime)
                VALUES(1, 'Ultimaker 3', 3499, 7, 0.07, 0.05, 0, 462, 20, 29, 0.8);""")
    cur.execute("""INSERT INTO machines (machine_id, machine_name, total_machine_cost, machine_lifetime, cost_of_capital, infrastructure_cost, maintenance_cost, machine_build_area, machine_build_height, machine_build_rate, machine_uptime)
                VALUES(2, 'Stratasys Fortus 360mc', 145000, 7, 0.07, 0.05, 0.07, 1441, 41, 61, 0.8);""")
    cur.execute("""INSERT INTO machines (machine_id, machine_name, total_machine_cost, machine_lifetime, cost_of_capital, infrastructure_cost, maintenance_cost, machine_build_area, machine_build_height, machine_build_rate, machine_uptime)
                VALUES(3, 'Form 2', 3500, 7, 0.07, 0.35, 0.05, 210, 18, 105, 0.8);""")
    cur.execute("""INSERT INTO machines (machine_id, machine_name, total_machine_cost, machine_lifetime, cost_of_capital, infrastructure_cost, maintenance_cost, machine_build_area, machine_build_height, machine_build_rate, machine_uptime)
                VALUES(4, '3D Systems ProX 950', 999000, 7, 0.07, 0.1, 0.05, 11250, 55, 600, 0.8);""")
    cur.execute("""INSERT INTO machines (machine_id, machine_name, total_machine_cost, machine_lifetime, cost_of_capital, infrastructure_cost, maintenance_cost, machine_build_area, machine_build_height, machine_build_rate, machine_uptime)
                VALUES(5, 'Figure 4 - Stand Alone', 21700, 7, 0.07, 0.35, 0.05, 87.61, 19.6, 569, 0.8);""")
    cur.execute("""INSERT INTO machines (machine_id, machine_name, total_machine_cost, machine_lifetime, cost_of_capital, infrastructure_cost, maintenance_cost, machine_build_area, machine_build_height, machine_build_rate, machine_uptime)
                VALUES(6, 'Figure 4 - Modular', 50000, 7, 0.07, 0.1, 0.05, 87.61, 19.6, 569, 0.8);""")
    cur.execute("""INSERT INTO machines (machine_id, machine_name, total_machine_cost, machine_lifetime, cost_of_capital, infrastructure_cost, maintenance_cost, machine_build_area, machine_build_height, machine_build_rate, machine_uptime)
                VALUES(7, 'EOSINT P800', 1055000, 7, 0.07, 0.2, 0.05, 2660, 56, 2774, 0.8);""")
    cur.execute("""INSERT INTO machines (machine_id, machine_name, total_machine_cost, machine_lifetime, cost_of_capital, infrastructure_cost, maintenance_cost, machine_build_area, machine_build_height, machine_build_rate, machine_uptime)
                VALUES(8, 'EOSm100', 248000, 7, 0.07, 0.5, 0.05, 79, 10, 5, 0.8);""")
    cur.execute("""INSERT INTO machines (machine_id, machine_name, total_machine_cost, machine_lifetime, cost_of_capital, infrastructure_cost, maintenance_cost, machine_build_area, machine_build_height, machine_build_rate, machine_uptime)
                VALUES(9, 'EOSm400-4', 1758000, 7, 0.07, 0.5, 0.05, 1600, 40, 107, 0.8);""")
    cur.execute("""INSERT INTO machines (machine_id, machine_name, total_machine_cost, machine_lifetime, cost_of_capital, infrastructure_cost, maintenance_cost, machine_build_area, machine_build_height, machine_build_rate, machine_uptime)
                VALUES(10, '3D System Figure 4', 50000, 7, 0.07, 0.1, 0.05, 87.61, 19.6, 569, 0.8);""")

    #Insert processes into table
    cur.execute("""INSERT INTO processes (process_id, process_name, packing_policy, packing_fraction, recycling_fraction, additional_operating_cost, consumable_cost_per_build, first_time_prep, subsequent_prep, time_per_build_setup, time_per_build_removal, time_per_machine_warmup, time_per_machine_cooldown)
                VALUES (1, 'DLP', 2, 0.9, 0.9, 0, 1, 1, 0, 0.5, 0.25, 0, 0);""")
    cur.execute("""INSERT INTO processes (process_id, process_name, packing_policy, packing_fraction, recycling_fraction, additional_operating_cost, consumable_cost_per_build, first_time_prep, subsequent_prep, time_per_build_setup, time_per_build_removal, time_per_machine_warmup, time_per_machine_cooldown)
                VALUES (2, 'FFF', 2, 0.9, 1, 0, 0.58, 1, 0, 0.5, 0.5, 0.15, 0.1);""")
    cur.execute("""INSERT INTO processes (process_id, process_name, packing_policy, packing_fraction, recycling_fraction, additional_operating_cost, consumable_cost_per_build, first_time_prep, subsequent_prep, time_per_build_setup, time_per_build_removal, time_per_machine_warmup, time_per_machine_cooldown)
                VALUES (3, 'FDM', 2, 0.9, 1, 0, 3.72, 2, 0, 0.5, 0.1, 0.3, 0.15);""")
    cur.execute("""INSERT INTO processes (process_id, process_name, packing_policy, packing_fraction, recycling_fraction, additional_operating_cost, consumable_cost_per_build, first_time_prep, subsequent_prep, time_per_build_setup, time_per_build_removal, time_per_machine_warmup, time_per_machine_cooldown)
                VALUES (4, 'SLA', 2, 0.9, 0.9, 0, 0.25, 1, 0, 0.25, 0.1, 0.15, 0);""")
    cur.execute("""INSERT INTO processes (process_id, process_name, packing_policy, packing_fraction, recycling_fraction, additional_operating_cost, consumable_cost_per_build, first_time_prep, subsequent_prep, time_per_build_setup, time_per_build_removal, time_per_machine_warmup, time_per_machine_cooldown)
                VALUES (5, 'SLS', 3, 0.95, 0.9, 0, 1.5, 3, 0, 0.75, 0.5, 0.5, 0.5);""")
    cur.execute("""INSERT INTO processes (process_id, process_name, packing_policy, packing_fraction, recycling_fraction, additional_operating_cost, consumable_cost_per_build, first_time_prep, subsequent_prep, time_per_build_setup, time_per_build_removal, time_per_machine_warmup, time_per_machine_cooldown)
                VALUES (6, 'SLM', 2, 0.9, 0.9, 20, 25, 3, 0, 0.75, 0.5, 0.5, 0.5);""")

    #Insert post-processes into table
    cur.execute("""INSERT INTO post_processes (post_process_id, removal_time_constant, for_machine) VALUES (1, 0.05, 1);""")
    cur.execute("""INSERT INTO post_processes (post_process_id, removal_time_constant, for_machine) VALUES (2, 0.03, 2);""")
    cur.execute("""INSERT INTO post_processes (post_process_id, removal_time_constant, for_machine) VALUES (3, 0.08, 3);""")
    cur.execute("""INSERT INTO post_processes (post_process_id, removal_time_constant, for_machine) VALUES (4, 0.05, 4);""")
    cur.execute("""INSERT INTO post_processes (post_process_id, removal_time_constant, for_machine) VALUES (5, 0.05, 5);""")
    cur.execute("""INSERT INTO post_processes (post_process_id, removal_time_constant, for_machine) VALUES (6, 0.05, 6);""")
    cur.execute("""INSERT INTO post_processes (post_process_id, removal_time_constant, for_machine) VALUES (7, 0, 7);""")
    cur.execute("""INSERT INTO post_processes (post_process_id, removal_time_constant, for_machine) VALUES (8, 0.11, 8);""")
    cur.execute("""INSERT INTO post_processes (post_process_id, removal_time_constant, for_machine) VALUES (9, 0.11, 9);""")

    #Insert operations into table
    cur.execute("""INSERT INTO operations (operations_id, hours_per_day, days_per_week, FTE_per_machine, FTE_build_exchange, FTE_support_removal, salary_engineer, salary_operator, salary_technician, for_machine) 
                VALUES(1, 18, 5, 0.05, 1, 1, 70, 40, 30, 1);""")
    cur.execute("""INSERT INTO operations (operations_id, hours_per_day, days_per_week, FTE_per_machine, FTE_build_exchange, FTE_support_removal, salary_engineer, salary_operator, salary_technician, for_machine) 
                VALUES(2, 18, 5, 0.1, 1, 1, 70, 40, 30, 2);""")
    cur.execute("""INSERT INTO operations (operations_id, hours_per_day, days_per_week, FTE_per_machine, FTE_build_exchange, FTE_support_removal, salary_engineer, salary_operator, salary_technician, for_machine)
                VALUES(3, 18, 5, 0.05, 1, 1, 70, 40, 30, 3);""")
    cur.execute("""INSERT INTO operations (operations_id, hours_per_day, days_per_week, FTE_per_machine, FTE_build_exchange, FTE_support_removal, salary_engineer, salary_operator, salary_technician, for_machine)
                VALUES(4, 18, 5, 0.15, 1, 1, 70, 50, 30, 4);""")
    cur.execute("""INSERT INTO operations (operations_id, hours_per_day, days_per_week, FTE_per_machine, FTE_build_exchange, FTE_support_removal, salary_engineer, salary_operator, salary_technician, for_machine)
                VALUES(5, 18, 5, 0.1, 1, 1, 70, 50, 30, 5);""")
    cur.execute("""INSERT INTO operations (operations_id, hours_per_day, days_per_week, FTE_per_machine, FTE_build_exchange, FTE_support_removal, salary_engineer, salary_operator, salary_technician, for_machine)
                VALUES(6, 18, 5, 0.1, 1, 1, 70, 50, 30, 6);""")
    cur.execute("""INSERT INTO operations (operations_id, hours_per_day, days_per_week, FTE_per_machine, FTE_build_exchange, FTE_support_removal, salary_engineer, salary_operator, salary_technician, for_machine)
                VALUES(7, 18, 5, 0.15, 1, 1, 70, 50, 30, 7);""")
    cur.execute("""INSERT INTO operations (operations_id, hours_per_day, days_per_week, FTE_per_machine, FTE_build_exchange, FTE_support_removal, salary_engineer, salary_operator, salary_technician, for_machine)
                VALUES(8, 18, 5, 0.15, 1, 1, 70, 50, 30, 8);""")
    cur.execute("""INSERT INTO operations (operations_id, hours_per_day, days_per_week, FTE_per_machine, FTE_build_exchange, FTE_support_removal, salary_engineer, salary_operator, salary_technician, for_machine)
                VALUES(9, 18, 5, 0.15, 1, 1, 70, 50, 30, 9);""")

    #Insert materials into table
    cur.execute("""INSERT INTO materials (material_id, material_name, material_density, material_cost, in_process, for_machine) 
                VALUES(1, 'ABS', 1.1, 66.66, 3, 1);""")
    cur.execute("""INSERT INTO materials (material_id, material_name, material_density, material_cost, in_process, for_machine)
                VALUES(2, 'Ultem', 1.27, 178.86, 3, 2);""")
    cur.execute("""INSERT INTO materials (material_id, material_name, material_density, material_cost, in_process, for_machine)
                VALUES(3, 'Clear Resin', 1.18, 126.27, 4, 3);""")
    cur.execute("""INSERT INTO materials (material_id, material_name, material_density, material_cost, in_process, for_machine)
                VALUES(4, 'Dental Model Resin', 1.18, 126.27, 4, 3);""")
    cur.execute("""INSERT INTO materials (material_id, material_name, material_density, material_cost, in_process, for_machine)
                VALUES(5, 'Accura Xtreme', 1.18, 280, 4, 4);""")
    cur.execute("""INSERT INTO materials (material_id, material_name, material_density, material_cost, in_process, for_machine)
                VALUES(6, 'Casting Resing', 1.18, 253.39, 4, 3);""")
    cur.execute("""INSERT INTO materials (material_id, material_name, material_density, material_cost, in_process, for_machine)
                VALUES(7, 'PA2200', 0.93, 67.5, 5, 7);""")
    cur.execute("""INSERT INTO materials (material_id, material_name, material_density, material_cost, in_process, for_machine)
                VALUES(8, 'PA12', 1.01, 60, 5, 7);""")
    cur.execute("""INSERT INTO materials (material_id, material_name, material_density, material_cost, in_process, for_machine)
                VALUES(9, 'Alumide', 1.36, 50, 5, 7);""")
    cur.execute("""INSERT INTO materials (material_id, material_name, material_density, material_cost, in_process, for_machine)
                VALUES(10, 'Ti6Al4V', 4.43, 400, 6, 8);""")
    cur.execute("""INSERT INTO materials (material_id, material_name, material_density, material_cost, in_process, for_machine)
                VALUES(11, 'Ti6Al4V', 4.43, 400, 6, 9);""")
    cur.execute("""INSERT INTO materials (material_id, material_name, material_density, material_cost, in_process, for_machine)
                VALUES(12, 'SSL316', 8, 30, 6, 8);""")
    cur.execute("""INSERT INTO materials (material_id, material_name, material_density, material_cost, in_process, for_machine)
                VALUES(13, 'SSL316', 8, 30, 6, 9);""")
    cur.execute("""INSERT INTO materials (material_id, material_name, material_density, material_cost, in_process, for_machine)
                VALUES(14, 'Problack 10', 2.6, 250, 1, 10);""")

    con.commit()

if inp == 'n':
    print('Database reset cancelled')
    con.close()