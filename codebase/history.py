import sqlite3
import tkinter as tk
from tkinter import *
import customtkinter as c
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Connect to the database
con = sqlite3.connect('database/nexttech_calculator.db')
cur = con.cursor()
cur.execute("""SELECT c.calculation_id, c.date, c.project_name, n.machine_name, m.material_name, c.average_cost
            FROM calculations c
            JOIN materials m ON c.material_used = m.material_id
            JOIN machines n ON c.machine_used = n.machine_id""")

master = c.CTk()
master.title("History")
master.geometry("1280x720")
master.configure(fg_color="#D9D9D9")

headers = ["ID", "Date", "Project Name", "Machine", "Material", "Cost per part", "Details"]
sort_order = ["ASC", "DESC"]
current_order = [0, 0, 0, 0]

for j, header in enumerate(headers):
    header_label = c.CTkLabel(master, text=header, font=("Arial", 16, "bold"))
    header_label.grid(row=0, column=j, padx=10, pady=5)

def sort_by_column(column_index):
    global current_order
    sort_columns = ["c.calculation_id","c.date","c.project_name", "n.machine_name", "m.material_name", "c.average_cost"]
    order = sort_order[current_order[column_index]]
    cur.execute(f"""SELECT c.date, c.project_name, n.machine_name, m.material_name, c.average_cost
                    FROM calculations c
                    JOIN materials m ON c.material_used = m.material_id
                    JOIN machines n ON c.machine_used = n.machine_id
                    ORDER BY {sort_columns[column_index]} {order}""")
    current_order[column_index] = 1 - current_order[column_index]
    update_table()

def view_details(calculation_id):
    cur.execute(f"""SELECT c.calculation_id, c.date, c.project_name, c.machine_used, c.material_used, c.parts_made, c.builds_done, c.total_cost, c.average_cost,
                n.machine_name, m.material_name
                FROM calculations c 
                JOIN machines n ON c.machine_used = n.machine_id
                JOIN materials m ON c.material_used = m.material_id
                WHERE calculation_id = {calculation_id};""")
    
    
    details = cur.fetchone()

    details_window = Toplevel(master)
    details_window.title("Calculation Details")
    details_window.geometry("800x600")

    details_text = Text(details_window, wrap=WORD, font=("Arial", 12))
    details_text.insert(END, f"Calculation ID: {details[0]}\n")
    details_text.insert(END, f"Date: {details[1]}\n")
    details_text.insert(END, f"Machine Used: {details[9]}\n")
    details_text.insert(END, f"Material Used: {details[10]}\n")
    details_text.insert(END, f"Parts Made: {details[5]}\n")
    details_text.insert(END, f"Builds Done: {details[6]}\n")
    details_text.insert(END, f"Total Cost: {details[7]}\n")
    details_text.insert(END, f"Average Cost: {details[8]}\n")
    details_text.grid(row=0, column=0, sticky='nsew')

    details_window.grid_rowconfigure(0, weight=1)
    details_window.grid_columnconfigure(0, weight=1)


    fig = Figure(figsize=(5, 4), dpi=100)
    ax = fig.add_subplot(111)
    parts = list(range(1, 101))
    costs = [details[6] / part for part in parts]
    ax.plot(parts, costs)
    ax.set_xlabel('Number of Parts')
    ax.set_ylabel('Cost per Part')
    ax.set_title('Cost per Part up to 100')

    canvas = FigureCanvasTkAgg(fig, master=details_window)
    canvas.draw()
    canvas.get_tk_widget().grid(row=1, column=0, sticky='nsew')

def update_table():
    for widget in master.winfo_children():
        if isinstance(widget, c.CTkLabel) or isinstance(widget, c.CTkButton):
            widget.destroy()

    for j, header in enumerate(headers):
        header_button = c.CTkButton(master, text=header,text_color="black", font=("Arial", 16, "bold"), fg_color="#C6C5C5",border_width=2 ,border_color="#0377AC", command=lambda j=j: sort_by_column(j))
        header_button.grid(row=0, column=j, padx=10, pady=5)

    rows = cur.fetchall()
    for i, row in enumerate(rows):
        for j, value in enumerate(row):
            cell = c.CTkLabel(master, text=value, font=("Arial", 12), text_color="#0377AC")
            cell.grid(row=i+1, column=j, padx=10, pady=5)
        details_button = c.CTkButton(master, text="Details", font=("Arial", 10), command=lambda row=row: view_details(row[0]))
        details_button.grid(row=i+1, column=6, padx=10, pady=5)

update_table()
while True:
    rows = cur.fetchall()
    if not rows:
        break

    for i, row in enumerate(rows):
        for i, row in enumerate(rows):
            for j, value in enumerate(row):
                cell = c.CTkLabel(master, text=value, font=("Arial", 12),text_color="#0377AC")
                cell.grid(row=i+1, column=j, padx=10, pady=5)
                details_button = c.CTkButton(master, text="Details", font=("Arial", 10))
                details_button.grid(row=i+1, column=4, padx=10, pady=5)

master.mainloop()