import tkinter as tk
from tkinter import messagebox
from tkinter import Tk, Label, Entry, Button, StringVar, OptionMenu
from tkinter import *
import customtkinter as c
from tkinter import *
import customtkinter as c
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sqlite3
from functools import partial

total_cost = 0
average_cost_per_part = 0
from functools import partial

total_cost = 0
average_cost_per_part = 0

def fetch_options(query):
    con = sqlite3.connect('nexttech_calculator.db')
    cur = con.cursor()
    cur.execute(query)
    options = {row[1]: row[0] for row in cur.fetchall()}  # Map names to IDs
    con.close()
    return options

def update_machine_options(machine_id_var, material_id_var, machine_id_menu, material_options, *args):
    global machine_options  # Ensure machine_options is updated globally
    selected_material = material_id_var.get()
    if selected_material == "Choose One":
        machine_id_var.set("Choose One")
        machine_id_menu['menu'].delete(0, 'end')
        machine_options = {}
        return

    material_id = material_options[selected_material]
    query = "SELECT cb.in_machine, n.machine_name FROM combination cb JOIN machines n ON cb.in_machine = n.machine_id WHERE cb.using_material = ?"
    con = sqlite3.connect('codeabase/nexttech_calculator.db')
    cur = con.cursor()
    cur.execute(query, (material_id,))
    machine_options = {row[1]: row[0] for row in cur.fetchall()}

    machine_id_var.set("Choose One")
    machine_id_menu['menu'].delete(0, 'end')
    for machine_name in machine_options.keys():
        machine_id_menu['menu'].add_command(label=machine_name, command=tk._setit(machine_id_var, machine_name))

def material_cost_calc(parts_produced,numbers_of_builds, part_mass, support_mass_per_part, machine_build_area, machine_build_height, material_density, recycling_fraction, material_cost):
            total_part_material = parts_produced * part_mass
            total_support_material = parts_produced * support_mass_per_part
            total_material_all_builds = (numbers_of_builds * machine_build_area * machine_build_height * material_density) / 1000
            recycled_material = (total_material_all_builds - total_part_material - total_support_material) * (recycling_fraction)
            material_waste = total_material_all_builds - recycled_material - total_part_material - total_support_material
            material_required = material_waste + total_support_material + total_part_material
            total_material_cost = material_required * material_cost

            return total_material_cost

def build_prep(parts_produced,numbers_of_builds,subsequent_prep, first_time_prep, salary_engineer):
            build_prep_time = ((numbers_of_builds - 1) * subsequent_prep) + first_time_prep
            total_build_prep_cost = build_prep_time * salary_engineer

            return total_build_prep_cost

def post_process_cost(parts_produced,numbers_of_builds,removal_time_constant, part_area, salary_technician):
            post_process_time_per_part = removal_time_constant * part_area**0.5
            total_post_process_time = post_process_time_per_part * parts_produced
            total_post_process_cost = total_post_process_time * salary_technician

            return total_post_process_cost

def machine_cost(parts_produced,numbers_of_builds,total_machine_cost, infrastructure_cost, cost_of_capital, machine_lifetime, maintenance_cost, hours_per_day, days_per_week, machine_uptime, machine_build_rate, part_material_volume, time_per_machine_warmup, time_per_machine_cooldown, time_per_build_setup, time_per_build_removal, FTE_per_machine, FTE_build_exchange, salary_operator, additional_operating_cost, consumable_cost_per_build):
            total_up_front_cost = total_machine_cost * (1 + infrastructure_cost)
            annual_depreciation = cost_of_capital * total_up_front_cost / (1 - (1 + cost_of_capital) ** (-1 * machine_lifetime))
            annual_maintenance = maintenance_cost * total_machine_cost
            annual_machine_cost = annual_maintenance + annual_depreciation
            operating_hours_per_year = hours_per_day * days_per_week * 52 * machine_uptime
            
            machine_cost_per_hour_occupied = annual_machine_cost / operating_hours_per_year

            total_warmup_time = numbers_of_builds * time_per_machine_warmup
            total_print_time = parts_produced * part_material_volume / machine_build_rate
            total_cooldown_time = numbers_of_builds * time_per_machine_cooldown
            total_build_exchange_time = numbers_of_builds * (time_per_build_setup + time_per_build_removal)
            total_machine_time_required = total_warmup_time + total_print_time + total_cooldown_time + total_build_exchange_time

            total_machine_usage_cost = total_machine_time_required * machine_cost_per_hour_occupied

            # Consumables
            operating_cost = additional_operating_cost * (total_warmup_time + total_print_time + total_cooldown_time)
            per_build_consumables = consumable_cost_per_build * numbers_of_builds
            total_consumables_cost = operating_cost + per_build_consumables

            # Labor
            labour_hours_during_build = (total_warmup_time + total_print_time + total_cooldown_time) * FTE_per_machine
            labour_hours_during_build_exchange = total_build_exchange_time * FTE_build_exchange
            total_labour_hours = labour_hours_during_build + labour_hours_during_build_exchange
            total_labor_cost = total_labour_hours * salary_operator

            return total_machine_usage_cost, total_consumables_cost, total_labor_cost

def display_results(total_cost, average_cost_per_part, cost_breakdown):
            # Clear the frame2 content
            for widget in frame2.winfo_children():
                widget.destroy()

            # Configure grid weights
            frame2.grid_rowconfigure(0, weight=1)
            frame2.grid_columnconfigure(0, weight=1)

            tk.Label(frame2, text=f"Total Cost: {total_cost}").grid(row=0, column=0, sticky='w')
            tk.Label(frame2, text=f"Average Cost per Part: {average_cost_per_part}").grid(row=1, column=0, sticky='w')
            tk.Label(frame2, text="Cost Breakdown:").grid(row=2, column=0, sticky='w')

            row = 3
            for key, value in cost_breakdown.items():
                tk.Label(frame2, text=f"{key}: {value}").grid(row=row, column=0, sticky='w')
                row += 1

            # Create a graph of cost per part up to 100
            fig = Figure(figsize=(5, 4), dpi=100)
            ax = fig.add_subplot(111)
            parts = list(range(1, 101))
            costs = [total_cost / part for part in parts]
            ax.plot(parts, costs)
            ax.set_xlabel('Number of Parts')
            ax.set_ylabel('Cost per Part')
            ax.set_title('Cost per Part up to 100')

            canvas = FigureCanvasTkAgg(fig, master=frame2)
            canvas.draw()
            canvas.get_tk_widget().grid(row=row, column=0, sticky='w')


def calculate(project_name_entry, machine_id_var, material_id_var, parts_produced_entry, numbers_of_builds_entry, part_mass_entry, material_id_menu, material_options, part_height_entry, part_area_entry, support_material_entry):
        global total_cost, average_cost_per_part
        con = sqlite3.connect('codebase/nexttech_calculator.db')
        cur = con.cursor()

        #project
        project_name = project_name_entry.get()
        #project
        project_name = project_name_entry.get()
        parts_produced = int(parts_produced_entry.get())
        numbers_of_builds = int(numbers_of_builds_entry.get())
        
        
        machine_id = machine_options[machine_id_var.get()]
        material_id = material_options[material_id_var.get()]

        # Fetch the process based on the selected material and machine
        query = "SELECT with_process FROM combination WHERE using_material = ? AND in_machine = ?"
        query = "SELECT with_process FROM combination WHERE using_material = ? AND in_machine = ?"
        process_id = cur.execute(query, (material_id, machine_id)).fetchone()
        if process_id is None:
            messagebox.showerror("Error", "No process found for the selected machine and material.")
            return
        process_id = process_id[0] 

        query = "SELECT * FROM materials WHERE material_id = ?"
        materials = cur.execute(query, (material_id,)).fetchone()
        print(material_id, process_id)
        query = "SELECT * FROM materials WHERE material_id = ?"
        materials = cur.execute(query, (material_id,)).fetchone()
        print(material_id, process_id)
        if materials is None:
            messagebox.showerror("Error", "No materials found for the selected machine and process.")
            return
 
 
        machine = cur.execute("SELECT * FROM machines WHERE machine_id = ?", (machine_id,)).fetchone()
        if machine is None:
            messagebox.showerror("Error", "No machine found with the selected ID.")
            return

        process = cur.execute("SELECT * FROM processes WHERE process_id = ?", (process_id,)).fetchone()
        if process is None:
            messagebox.showerror("Error", "No process found with the selected ID.")
            return

        operations = cur.execute("SELECT * FROM operations WHERE for_machine = ?", (machine_id,)).fetchone()
        if operations is None:
            messagebox.showerror("Error", "No operations found for the selected machine.")

        #material
        material_cost = materials[3] #dollar/kg
        material_density = materials[2] #g/cm^3

        #part
        part_mass = float(part_mass_entry.get())
        part_height = float(part_height_entry.get())
        part_area = float(part_area_entry.get())
        support_material = float(support_material_entry.get())
        support_mass_per_part = support_material * part_mass #kg
        part_material_volume = (part_mass * 1000) / material_density #cm^3

        #machine
        total_machine_cost = machine[2] #dollar
        machine_lifetime = machine[3] #years
        cost_of_capital = machine[4] #%
        infrastructure_cost = machine[5] #% of machine cost up front
        maintenance_cost = machine[6] #% of machine cost per year
        machine_build_rate = machine[7] #cm^3/hr	
        machine_build_area = machine[8] #cm^2
        machine_build_height = machine[9] #cm
        machine_uptime = machine[10] #%
        machine_build_volume = (machine_build_area * machine_build_height) / 1000 #Liter

        #process
        packing_policy = process[2] #2d or 3d
        packing_fraction = process[3] #%
        recycling_fraction = process[4] #%
        additional_operating_cost = process[5] #dollar/hr
        consumable_cost_per_build = process[6] #dollar
        first_time_prep = process[7] #hours
        subsequent_prep = process[8] #hours
        time_per_build_setup = process[9] #hours
        time_per_build_removal = process[10] #hours
        time_per_machine_warmup = process[11] #hours
        time_per_machine_cooldown = process[12] #hours

        #post-process
        removal_time_constant = machine[11] 
        removal_time_constant = machine[11] 
        time_to_remove = (60*10**0.5)*removal_time_constant

        #operations
        hours_per_day = operations[1] #hours/day
        days_per_week = operations[2] #days/week
        FTE_per_machine = operations[3]
        FTE_build_exchange = operations[4]
        FTE_support_removal = operations[5]
        salary_engineer = operations[6] #dollar/hr
        salary_operator = operations[7] #dollar/hr
        salary_technician = operations[8] #dollar/hr

        material_cost_for_run = material_cost_calc(parts_produced, numbers_of_builds, part_mass, support_mass_per_part, machine_build_area, machine_build_height, material_density, recycling_fraction, material_cost)
        build_prep_cost = build_prep(parts_produced, numbers_of_builds, subsequent_prep, first_time_prep, salary_engineer)
        machine_usage_cost, consumables_cost, labor_cost = machine_cost(parts_produced, numbers_of_builds, total_machine_cost, infrastructure_cost, cost_of_capital, machine_lifetime, maintenance_cost, hours_per_day, days_per_week, machine_uptime, machine_build_rate, part_material_volume, time_per_machine_warmup, time_per_machine_cooldown, time_per_build_setup, time_per_build_removal, FTE_per_machine, FTE_build_exchange, salary_operator, additional_operating_cost, consumable_cost_per_build)
        post_process_cost_for_run = post_process_cost(parts_produced, numbers_of_builds, removal_time_constant, part_area, salary_technician)
        material_cost_for_run = material_cost_calc(parts_produced, numbers_of_builds, part_mass, support_mass_per_part, machine_build_area, machine_build_height, material_density, recycling_fraction, material_cost)
        build_prep_cost = build_prep(parts_produced, numbers_of_builds, subsequent_prep, first_time_prep, salary_engineer)
        machine_usage_cost, consumables_cost, labor_cost = machine_cost(parts_produced, numbers_of_builds, total_machine_cost, infrastructure_cost, cost_of_capital, machine_lifetime, maintenance_cost, hours_per_day, days_per_week, machine_uptime, machine_build_rate, part_material_volume, time_per_machine_warmup, time_per_machine_cooldown, time_per_build_setup, time_per_build_removal, FTE_per_machine, FTE_build_exchange, salary_operator, additional_operating_cost, consumable_cost_per_build)
        post_process_cost_for_run = post_process_cost(parts_produced, numbers_of_builds, removal_time_constant, part_area, salary_technician)

        total_cost = material_cost_for_run + build_prep_cost + machine_usage_cost + consumables_cost + labor_cost + post_process_cost_for_run
        average_cost_per_part = total_cost / parts_produced
        total_cost = material_cost_for_run + build_prep_cost + machine_usage_cost + consumables_cost + labor_cost + post_process_cost_for_run
        average_cost_per_part = total_cost / parts_produced

        cost_breakdown = {
            "Material Cost": material_cost_for_run,
            "Build Prep Cost": build_prep_cost,
            "Machine Usage Cost": machine_usage_cost,
            "Consumables Cost": consumables_cost,
            "Labor Cost": labor_cost,
            "Post Process Cost": post_process_cost_for_run
        }
        cost_breakdown = {
            "Material Cost": material_cost_for_run,
            "Build Prep Cost": build_prep_cost,
            "Machine Usage Cost": machine_usage_cost,
            "Consumables Cost": consumables_cost,
            "Labor Cost": labor_cost,
            "Post Process Cost": post_process_cost_for_run
        }

        display_results(total_cost, average_cost_per_part, cost_breakdown)
        
        display_results(total_cost, average_cost_per_part, cost_breakdown)
        
        messagebox.showinfo("Success", "Calculation completed successfully!")

def save_calculation(name_pro, machine_id_var, material_id_var, parts_produced_entry, numbers_of_builds_entry):
        global total_cost, average_cost_per_part
        con = sqlite3.connect('codebase/nexttech_calculator.db')
        cur = con.cursor()
        
        machine_id = machine_options[machine_id_var.get()]
        material_id = material_options[material_id_var.get()]
        parts_produced = int(parts_produced_entry.get())
        numbers_of_builds = int(numbers_of_builds_entry.get())
        project_name = name_pro.get()

        print(machine_id, material_id)

        query = "SELECT with_process FROM combination WHERE using_material = ? AND in_machine = ?"
        process_id = cur.execute(query, (material_id, machine_id)).fetchone()
        process_id = process_id[0]       

        cur.execute("""INSERT INTO calculations (project_name, machine_used, material_used, parts_made, builds_done, process_used, total_cost, average_cost)
                        VALUES(?,?,?,?,?,?,?,?)""", (project_name, machine_id, material_id, parts_produced, numbers_of_builds, process_id, total_cost, average_cost_per_part))
        con.commit()

        messagebox.showinfo("Success", "Calculation saved successfully!")
        
# Fetch options for dropdown menus
material_options = fetch_options("SELECT material_id, material_name FROM materials")

# Add "Choose One" option
material_options = {"Choose One": None, **material_options}

# Initialize machine_options
machine_options = {}

# Create the main window
root = c.CTk()
root.title("Calculator")
root.geometry("1280x720")
root.config(bg= "#333333")

#Frame around head menue, remove when we have a menu
framehm = c.CTkFrame(root,
                    fg_color=("#000000"),
                    bg_color=("#333333"),
                    height=670,
                    width=181)
framehm.place(x=25, y=25)

#Frame around calculation
frame2 = c.CTkFrame(root,
                    fg_color=("#CDCCCC"),
                    bg_color=("#333333"),
                    height=670,
                    width=510)
frame2.place(x=740, y=25)

#Headline Calculation
overskrift2 = c.CTkLabel(root, text = "Calculation",
                        font = ("Arial",32, "bold"),
                        text_color=("#0377AC"),
                        bg_color =("#CDCCCC"),width=300, justify=CENTER)
overskrift2.place(x=840, y=35,)

# Save button, MISSING A COMMAND
save_button = c.CTkButton(root, command=lambda: save_calculation(name_pro, machine_id_var, material_id_var, parts_produced_entry, numbers_of_builds_entry),
                        text="Save calculation",
                        font=("Arial", 24),
                        text_color=("#FFFFFF"),
                        fg_color=("#0377AC"),
                        bg_color=("#CDCCCC"),
                        height=40, width=300, anchor="center",
                        hover_color="#034868",
                        corner_radius=20)
save_button.place(x=840, y=620)

# Space for GUI Calculation 






#Frame around calculator 
frame1 = c.CTkFrame(root,
                    fg_color=("#CDCCCC"),
                    bg_color=("#333333"),
                    height=670,
                    width=480)
frame1.place(x=231, y=25)

#Headline
overskrift1 = c.CTkLabel(root, text = "New calculation",
                        font = ("Arial",32, "bold"),
                        text_color=("#0377AC"),
                        bg_color =("#CDCCCC"),width=300, justify=CENTER)
overskrift1.place(x=321, y=35,)



# Name project, MISSING A COMMAND
name_pro = c.CTkEntry(root,
                        placeholder_text="Name your project",
                        font=("Arial", 20),
                        text_color=("#0377AC"),
                        fg_color=("#FFFFFF"), bg_color=("#CDCCCC"),
                        height=35, width=300,
                        corner_radius=20, border_color="#0377AC", border_width=2)
name_pro.place(x=321, y=85)


#Pick Machine; dropdown menus
label4 = c.CTkLabel(root, text="Pick machine:", font=("Arial", 18), text_color=("#0377AC"), bg_color=("#CDCCCC"),
                    anchor="e", width=180)
label4.place(x=270, y=320)

# Create the main window
root = c.CTk()
root.title("Calculator")
root.geometry("1280x720")
root.config(bg= "#333333")

#Frame around head menue, remove when we have a menu
framehm = c.CTkFrame(root,
                    fg_color=("#000000"),
                    bg_color=("#333333"),
                    height=670,
                    width=181)
framehm.place(x=25, y=25)

#Frame around calculation
frame2 = c.CTkFrame(root,
                    fg_color=("#CDCCCC"),
                    bg_color=("#333333"),
                    height=670,
                    width=510)
frame2.place(x=740, y=25)

#Headline Calculation
overskrift2 = c.CTkLabel(root, text = "Calculation",
                        font = ("Arial",32, "bold"),
                        text_color=("#0377AC"),
                        bg_color =("#CDCCCC"),width=300, justify=CENTER)
overskrift2.place(x=840, y=35,)

# Save button, MISSING A COMMAND
save_button = c.CTkButton(root, command=lambda: save_calculation(name_pro, machine_id_var, material_id_var, parts_produced_entry, numbers_of_builds_entry),
                        text="Save calculation",
                        font=("Arial", 24),
                        text_color=("#FFFFFF"),
                        fg_color=("#0377AC"),
                        bg_color=("#CDCCCC"),
                        height=40, width=300, anchor="center",
                        hover_color="#034868",
                        corner_radius=20)
save_button.place(x=840, y=620)

# Space for GUI Calculation 






#Frame around calculator 
frame1 = c.CTkFrame(root,
                    fg_color=("#CDCCCC"),
                    bg_color=("#333333"),
                    height=670,
                    width=480)
frame1.place(x=231, y=25)

#Headline
overskrift1 = c.CTkLabel(root, text = "New calculation",
                        font = ("Arial",32, "bold"),
                        text_color=("#0377AC"),
                        bg_color =("#CDCCCC"),width=300, justify=CENTER)
overskrift1.place(x=321, y=35,)



# Name project, MISSING A COMMAND
name_pro = c.CTkEntry(root,
                        placeholder_text="Name your project",
                        font=("Arial", 20),
                        text_color=("#0377AC"),
                        fg_color=("#FFFFFF"), bg_color=("#CDCCCC"),
                        height=35, width=300,
                        corner_radius=20, border_color="#0377AC", border_width=2)
name_pro.place(x=321, y=85)


#Pick Machine; dropdown menus
label4 = c.CTkLabel(root, text="Pick machine:", font=("Arial", 18), text_color=("#0377AC"), bg_color=("#CDCCCC"),
                    anchor="e", width=180)
label4.place(x=270, y=320)

machine_id_var = StringVar(root)
machine_id_var.set("Choose One")  # default value
machine_id_menu = OptionMenu(root, machine_id_var, "Choose One")
machine_id_menu.place(x=480, y=320)

# Pick Materials; dropdown menus
label3 = c.CTkLabel(root, text="Pick material:", font=("Arial", 18), text_color=("#0377AC"), bg_color=("#CDCCCC"),
                    anchor="e", width=180)
label3.place(x=270, y=270)

material_id_var = StringVar(root)
material_id_var.set("Choose One")  # default value
material_id_var.trace_add('write', partial(update_machine_options, machine_id_var, material_id_var, machine_id_menu, material_options))
material_id_menu = OptionMenu(root, material_id_var, *material_options.keys())
material_id_menu.place(x=480, y=270)

# Enter parts produced
label1 = c.CTkLabel(root, text="Enter parts produced:", font=("Arial", 18), text_color=("#0377AC"), bg_color=("#CDCCCC"),
                    anchor="e", width=180)
label1.place(x=270, y=170)
parts_produced_entry = c.CTkEntry(root, fg_color=("#FFFFFF"), bg_color=("#CDCCCC"), height=30, width=177, corner_radius=20, border_color="#0377AC", border_width=2)
parts_produced_entry.place(x=480, y=170)
machine_id_menu.place(x=480, y=320)

# Pick Materials; dropdown menus
label3 = c.CTkLabel(root, text="Pick material:", font=("Arial", 18), text_color=("#0377AC"), bg_color=("#CDCCCC"),
                    anchor="e", width=180)
label3.place(x=270, y=270)

material_id_var = StringVar(root)
material_id_var.set("Choose One")  # default value
material_id_var.trace_add('write', partial(update_machine_options, machine_id_var, material_id_var, machine_id_menu, material_options))
material_id_menu = OptionMenu(root, material_id_var, *material_options.keys())
material_id_menu.place(x=480, y=270)

# Enter parts produced
label1 = c.CTkLabel(root, text="Enter parts produced:", font=("Arial", 18), text_color=("#0377AC"), bg_color=("#CDCCCC"),
                    anchor="e", width=180)
label1.place(x=270, y=170)
parts_produced_entry = c.CTkEntry(root, fg_color=("#FFFFFF"), bg_color=("#CDCCCC"), height=30, width=177, corner_radius=20, border_color="#0377AC", border_width=2)
parts_produced_entry.place(x=480, y=170)

# Enter number of builds
label2 = c.CTkLabel(root, text="Enter number of builds:", font=("Arial", 18), text_color=("#0377AC"), bg_color=("#CDCCCC"),
                    anchor="e", width=180)
label2.place(x=270, y=220)
numbers_of_builds_entry = c.CTkEntry(root, fg_color=("#FFFFFF"), bg_color=("#CDCCCC"), height=30, width=177, corner_radius=20, border_color="#0377AC", border_width=2)
numbers_of_builds_entry.place(x=480, y=220)
# Enter number of builds
label2 = c.CTkLabel(root, text="Enter number of builds:", font=("Arial", 18), text_color=("#0377AC"), bg_color=("#CDCCCC"),
                    anchor="e", width=180)
label2.place(x=270, y=220)
numbers_of_builds_entry = c.CTkEntry(root, fg_color=("#FFFFFF"), bg_color=("#CDCCCC"), height=30, width=177, corner_radius=20, border_color="#0377AC", border_width=2)
numbers_of_builds_entry.place(x=480, y=220)

# Enter part mass in kg 
label5 = c.CTkLabel(root, text="Enter part mass in kg:", font=("Arial", 18), text_color=("#0377AC"), bg_color=("#CDCCCC"),
                    anchor="e", width=180)
label5.place(x=270, y=370)
part_mass_entry = c.CTkEntry(root, fg_color=("#FFFFFF"), bg_color=("#CDCCCC"), height=30, width=177, corner_radius=20, border_color="#0377AC", border_width=2,
                             placeholder_text="Kg.", placeholder_text_color=("#7A7A7A"))
part_mass_entry.place(x=480, y=370)

# Enter part height in cm
label6 = c.CTkLabel(root, text="Enter part height in cm:", font=("Arial", 18), text_color=("#0377AC"), bg_color=("#CDCCCC"),
                    anchor="e", width=180)
label6.place(x=270, y=420)
part_height_entry = c.CTkEntry(root, fg_color=("#FFFFFF"), bg_color=("#CDCCCC"), height=30, width=177, corner_radius=20, border_color="#0377AC", border_width=2,
                               placeholder_text="cm", placeholder_text_color=("#7A7A7A"))
part_height_entry.place(x=480, y=420)

# Enter part area in cm^2
label7 = c.CTkLabel(root, text="Enter part area in cm^2:", font=("Arial", 18), text_color=("#0377AC"), bg_color=("#CDCCCC"),
                    anchor="e", width=180)
label7.place(x=270, y=470)
part_area_entry = c.CTkEntry(root, fg_color=("#FFFFFF"), bg_color=("#CDCCCC"), height=30, width=177, corner_radius=20, border_color="#0377AC", border_width=2,
                                    placeholder_text="cm^2", placeholder_text_color=("#7A7A7A"))
part_area_entry.place(x=480, y=470)

# Enter support material as percent of mass
label8 = c.CTkLabel(root, text="Enter support material:", font=("Arial", 18), text_color=("#0377AC"), bg_color=("#CDCCCC"),
                    anchor="e", width=180)
label8.place(x=270, y=520)
support_material_entry = c.CTkEntry(root, fg_color=("#FFFFFF"), bg_color=("#CDCCCC"), height=30, width=177, corner_radius=20, border_color="#0377AC", border_width=2,
                                    placeholder_text="percent of mass (ex.0.15)", placeholder_text_color=("#7A7A7A"))
support_material_entry.place(x=480, y=520)

# Reset button, MISSING A COMMAND
reset_button = c.CTkButton(root,
                        text="Reset",
                        font=("Arial", 24),
                        text_color=("#FFFFFF"),
                        fg_color=("#5F6669"),
                        bg_color=("#CDCCCC"),
                        height=40, width=150,
                        hover_color="#333333",
                        corner_radius=20)
reset_button.place(x=279, y=620)
# Enter part mass in kg 
label5 = c.CTkLabel(root, text="Enter part mass in kg:", font=("Arial", 18), text_color=("#0377AC"), bg_color=("#CDCCCC"),
                    anchor="e", width=180)
label5.place(x=270, y=370)
part_mass_entry = c.CTkEntry(root, fg_color=("#FFFFFF"), bg_color=("#CDCCCC"), height=30, width=177, corner_radius=20, border_color="#0377AC", border_width=2,
                             placeholder_text="Kg.", placeholder_text_color=("#7A7A7A"))
part_mass_entry.place(x=480, y=370)

# Enter part height in cm
label6 = c.CTkLabel(root, text="Enter part height in cm:", font=("Arial", 18), text_color=("#0377AC"), bg_color=("#CDCCCC"),
                    anchor="e", width=180)
label6.place(x=270, y=420)
part_height_entry = c.CTkEntry(root, fg_color=("#FFFFFF"), bg_color=("#CDCCCC"), height=30, width=177, corner_radius=20, border_color="#0377AC", border_width=2,
                               placeholder_text="cm", placeholder_text_color=("#7A7A7A"))
part_height_entry.place(x=480, y=420)

# Enter part area in cm^2
label7 = c.CTkLabel(root, text="Enter part area in cm^2:", font=("Arial", 18), text_color=("#0377AC"), bg_color=("#CDCCCC"),
                    anchor="e", width=180)
label7.place(x=270, y=470)
part_area_entry = c.CTkEntry(root, fg_color=("#FFFFFF"), bg_color=("#CDCCCC"), height=30, width=177, corner_radius=20, border_color="#0377AC", border_width=2,
                                    placeholder_text="cm^2", placeholder_text_color=("#7A7A7A"))
part_area_entry.place(x=480, y=470)

# Enter support material as percent of mass
label8 = c.CTkLabel(root, text="Enter support material:", font=("Arial", 18), text_color=("#0377AC"), bg_color=("#CDCCCC"),
                    anchor="e", width=180)
label8.place(x=270, y=520)
support_material_entry = c.CTkEntry(root, fg_color=("#FFFFFF"), bg_color=("#CDCCCC"), height=30, width=177, corner_radius=20, border_color="#0377AC", border_width=2,
                                    placeholder_text="percent of mass (ex.0.15)", placeholder_text_color=("#7A7A7A"))
support_material_entry.place(x=480, y=520)

# Reset button, MISSING A COMMAND
reset_button = c.CTkButton(root,
                        text="Reset",
                        font=("Arial", 24),
                        text_color=("#FFFFFF"),
                        fg_color=("#5F6669"),
                        bg_color=("#CDCCCC"),
                        height=40, width=150,
                        hover_color="#333333",
                        corner_radius=20)
reset_button.place(x=279, y=620)

# Create and place the submit button
submit_button = c.CTkButton(root, command=lambda: calculate(name_pro, machine_id_var, material_id_var, parts_produced_entry, numbers_of_builds_entry, part_mass_entry, material_id_menu, material_options, part_height_entry, part_area_entry, support_material_entry),
                        text="Submit",
                        font=("Arial", 24),
                        text_color=("#FFFFFF"),
                        fg_color=("#77AC03"),
                        bg_color=("#CDCCCC"),
                        height=40, width=150,
                        hover_color="#527605",
                        corner_radius=20)
submit_button.place(x=500, y=620)
submit_button = c.CTkButton(root, command=lambda: calculate(name_pro, machine_id_var, material_id_var, parts_produced_entry, numbers_of_builds_entry, part_mass_entry, material_id_menu, material_options, part_height_entry, part_area_entry, support_material_entry),
                        text="Submit",
                        font=("Arial", 24),
                        text_color=("#FFFFFF"),
                        fg_color=("#77AC03"),
                        bg_color=("#CDCCCC"),
                        height=40, width=150,
                        hover_color="#527605",
                        corner_radius=20)
submit_button.place(x=500, y=620)

# Run the application
root.mainloop()