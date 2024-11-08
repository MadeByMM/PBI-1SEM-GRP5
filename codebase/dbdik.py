import sqlite3
import tkinter as tk
from tkinter import ttk

# Function to fetch and format the data
def fetch_and_format_data():
    # Connect to the SQLite database
    conn = sqlite3.connect('Codebase/nexttech_calculator.db')
    c2 = conn.cursor()

    # Enable foreign key support in SQLite (optional, if foreign keys are involved)
    c2.execute("PRAGMA foreign_keys = ON;")

    # Execute the SQL query to get machine_name along with other data
    c2.execute(""" 
    SELECT DISTINCT 
        m.machine_id, 
        m.machine_name, 
        m.total_machine_cost, 
        m.machine_lifetime, 
        m.cost_of_capital, 
        m.infrastructure_cost, 
        m.maintenance_cost, 
        m.machine_build_area, 
        m.machine_build_height, 
        m.machine_build_rate, 
        m.machine_uptime, 
        m.removal_time_constant, 
        p.process_id, 
        p.process_name, 
        p.packing_policy, 
        p.packing_fraction, 
        p.recycling_fraction, 
        p.additional_operating_cost, 
        p.consumable_cost_per_build, 
        p.first_time_prep, 
        p.subsequent_prep, 
        p.time_per_build_setup, 
        p.time_per_build_removal, 
        p.time_per_machine_warmup, 
        p.time_per_machine_cooldown,
        o.operations_id, 
        o.hours_per_day, 
        o.days_per_week, 
        o.FTE_per_machine, 
        o.FTE_build_exchange, 
        o.FTE_support_removal, 
        o.salary_engineer, 
        o.salary_operator, 
        o.salary_technician
    FROM combination c 
    JOIN machines m ON c.in_machine = m.machine_id 
    JOIN processes p ON c.with_process = p.process_id 
    JOIN operations o ON o.for_machine = m.machine_id;
    """)

    # Fetch the results
    rows = c2.fetchall()

    # Create a dictionary to store data grouped by machine_name
    data_by_machine_name = {}

    # Organize the data by machine_name
    for row in rows:
        (machine_id, machine_name, total_machine_cost, machine_lifetime, cost_of_capital, 
         infrastructure_cost, maintenance_cost, machine_build_area, machine_build_height, 
         machine_build_rate, machine_uptime, removal_time_constant, process_id, process_name, 
         packing_policy, packing_fraction, recycling_fraction, additional_operating_cost, 
         consumable_cost_per_build, first_time_prep, subsequent_prep, time_per_build_setup, 
         time_per_build_removal, time_per_machine_warmup, time_per_machine_cooldown, 
         operations_id, hours_per_day, days_per_week, FTE_per_machine, FTE_build_exchange, 
         FTE_support_removal, salary_engineer, salary_operator, salary_technician) = row

        if machine_name not in data_by_machine_name:
            data_by_machine_name[machine_name] = []
        data_by_machine_name[machine_name].append({
            "process_id": process_id,
            "process_name": process_name,
            "operations_id": operations_id,
            "total_machine_cost": total_machine_cost,
            "machine_lifetime": machine_lifetime,
            "cost_of_capital": cost_of_capital,
            "infrastructure_cost": infrastructure_cost,
            "maintenance_cost": maintenance_cost,
            "machine_build_area": machine_build_area,
            "machine_build_height": machine_build_height,
            "machine_build_rate": machine_build_rate,
            "machine_uptime": machine_uptime,
            "removal_time_constant": removal_time_constant,
            "packing_policy": packing_policy,
            "packing_fraction": packing_fraction,
            "recycling_fraction": recycling_fraction,
            "additional_operating_cost": additional_operating_cost,
            "consumable_cost_per_build": consumable_cost_per_build,
            "first_time_prep": first_time_prep,
            "subsequent_prep": subsequent_prep,
            "time_per_build_setup": time_per_build_setup,
            "time_per_build_removal": time_per_build_removal,
            "time_per_machine_warmup": time_per_machine_warmup,
            "time_per_machine_cooldown": time_per_machine_cooldown,
            "hours_per_day": hours_per_day,
            "days_per_week": days_per_week,
            "FTE_per_machine": FTE_per_machine,
            "FTE_build_exchange": FTE_build_exchange,
            "FTE_support_removal": FTE_support_removal,
            "salary_engineer": salary_engineer,
            "salary_operator": salary_operator,
            "salary_technician": salary_technician
        })

    # Close the connection
    conn.close()

    return data_by_machine_name

# Function to update the Treeview based on selected machine
def update_treeview(selected_machine, data_by_machine_name, tree):
    # Clear previous items in the Treeview
    for item in tree.get_children():
        tree.delete(item)

    # Insert the machine data into the Treeview
    if selected_machine in data_by_machine_name:
        machine_data = data_by_machine_name[selected_machine]

        for record in machine_data:
            for attr_name, attr_value in record.items():
                # Insert attribute name and value as a new row in the Treeview
                tree.insert("", "end", values=(attr_name, attr_value))

# Function to display the data in the Tkinter window
def display_data():
    data_by_machine_name = fetch_and_format_data()

    # Create a Tkinter window
    window = tk.Tk()
    window.title("Machine Data")

    # Create a combobox to select a machine
    machine_names = list(data_by_machine_name.keys())
    combobox = ttk.Combobox(window, values=machine_names, state="readonly")
    combobox.set("Select Machine")
    combobox.pack(pady=10)

    # Create a Treeview widget
    columns = ("Attribute", "Value")
    tree = ttk.Treeview(window, columns=columns, show="headings")
    tree.heading("Attribute", text="Attribute")
    tree.heading("Value", text="Value")

    # Add a vertical scrollbar to the Treeview
    scrollbar = ttk.Scrollbar(window, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Pack the Treeview
    tree.pack(fill=tk.BOTH, expand=True)

    # Bind the combobox selection event to update the Treeview
    combobox.bind("<<ComboboxSelected>>", lambda event: update_treeview(combobox.get(), data_by_machine_name, tree))

   


