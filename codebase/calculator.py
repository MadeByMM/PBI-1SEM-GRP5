import tkinter as tk
from tkinter import messagebox
from tkinter import Tk, Label, Entry, Button, StringVar, OptionMenu
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sqlite3

def fetch_options(query):
    con = sqlite3.connect('database/nexttech_calculator.db')
    cur = con.cursor()
    cur.execute(query)
    options = {row[1]: row[0] for row in cur.fetchall()}  # Map names to IDs
    con.close()
    return options

def update_machine_options(*args):
    global machine_options  # Ensure machine_options is updated globally
    selected_material = material_id_var.get()
    if selected_material == "Choose One":
        machine_id_var.set("Choose One")
        machine_id_menu['menu'].delete(0, 'end')
        machine_options = {}
        return

    material_id = material_options[selected_material]
    query = "SELECT machine_id, machine_name FROM machines WHERE machine_id IN (SELECT for_machine FROM materials WHERE material_id = ?)"
    con = sqlite3.connect('database/nexttech_calculator.db')
    cur = con.cursor()
    cur.execute(query, (material_id,))
    machine_options = {row[1]: row[0] for row in cur.fetchall()}
    con.close()

    machine_id_var.set("Choose One")
    machine_id_menu['menu'].delete(0, 'end')
    for machine_name in machine_options.keys():
        machine_id_menu['menu'].add_command(label=machine_name, command=tk._setit(machine_id_var, machine_name))


def calculate():
    try:

        if machine_id_var.get() == "Choose One" or material_id_var.get() == "Choose One":
            messagebox.showerror("Error", "Please select valid options for machine, process, and material.")
            return

        con = sqlite3.connect('database/nexttech_calculator.db')
        cur = con.cursor()

        parts_produced = int(parts_produced_entry.get())
        numbers_of_builds = int(numbers_of_builds_entry.get())

        machine_id = machine_options[machine_id_var.get()]
        material_id = material_options[material_id_var.get()]

        # Fetch the process based on the selected material and machine
        query = "SELECT in_process FROM materials WHERE material_id = ? AND for_machine = ?"
        process_id = cur.execute(query, (material_id, machine_id)).fetchone()
        if process_id is None:
            messagebox.showerror("Error", "No process found for the selected machine and material.")
            return
        process_id = process_id[0] 

        query = "SELECT * FROM materials WHERE for_machine = ? AND in_process = ?"
        materials = cur.execute(query, (material_id, process_id)).fetchone()
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

        post_process = cur.execute("SELECT * FROM post_processes WHERE for_machine = ?", (machine_id,)).fetchone()
        if post_process is None:
            messagebox.showerror("Error", "No post-process found for the selected machine.")
            return

        operations = cur.execute("SELECT * FROM operations WHERE for_machine = ?", (machine_id,)).fetchone()
        if operations is None:
            messagebox.showerror("Error", "No operations found for the selected machine.")
            return



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
        removal_time_constant = post_process[1] #c
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



        def material_cost_calc(parts_produced,numbers_of_builds):
            total_part_material = parts_produced * part_mass
            total_support_material = parts_produced * support_mass_per_part
            total_material_all_builds = (numbers_of_builds * machine_build_area * machine_build_height * material_density) / 1000
            recycled_material = (total_material_all_builds - total_part_material - total_support_material) * (recycling_fraction)
            material_waste = total_material_all_builds - recycled_material - total_part_material - total_support_material
            material_required = material_waste + total_support_material + total_part_material
            total_material_cost = material_required * material_cost

            return total_material_cost

        def build_prep(parts_produced,numbers_of_builds):
            build_prep_time = ((numbers_of_builds - 1) * subsequent_prep) + first_time_prep
            total_build_prep_cost = build_prep_time * salary_engineer

            return total_build_prep_cost

        def machine_cost(parts_produced,numbers_of_builds):
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

        def post_process_cost(parts_produced,numbers_of_builds):
            post_process_time_per_part = removal_time_constant * part_area**0.5
            total_post_process_time = post_process_time_per_part * parts_produced
            total_post_process_cost = total_post_process_time * salary_technician

            return total_post_process_cost
        
        def display_results(total_cost, average_cost_per_part, cost_breakdown):
            result_window = tk.Toplevel(root)
            result_window.title("Calculation Results")

            tk.Label(result_window, text=f"Total Cost: {total_cost}").pack()
            tk.Label(result_window, text=f"Average Cost per Part: {average_cost_per_part}").pack()
            tk.Label(result_window, text="Cost Breakdown:").pack()
            for key, value in cost_breakdown.items():
                tk.Label(result_window, text=f"{key}: {value}").pack()

            # Create a graph of cost per part up to 100
            fig = Figure(figsize=(5, 4), dpi=100)
            ax = fig.add_subplot(111)
            parts = list(range(1, 101))
            costs = [total_cost / part for part in parts]
            ax.plot(parts, costs)
            ax.set_xlabel('Number of Parts')
            ax.set_ylabel('Cost per Part')
            ax.set_title('Cost per Part up to 100')

            canvas = FigureCanvasTkAgg(fig, master=result_window)
            canvas.draw()
            canvas.get_tk_widget().pack()


        def total_cost(parts_produced,numbers_of_builds):
            material_cost_for_run = material_cost_calc(parts_produced,numbers_of_builds)
            build_prep_cost = build_prep(parts_produced,numbers_of_builds)
            machine_usage_cost, consumables_cost, labor_cost = machine_cost(parts_produced, numbers_of_builds)
            post_process_cost_for_run = post_process_cost(parts_produced, numbers_of_builds)

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

            display_results(total_cost, average_cost_per_part, cost_breakdown)

            return total_cost,average_cost_per_part

        totalcost, average_cost_per_part = total_cost(parts_produced, numbers_of_builds)

        messagebox.showinfo("Success", "Calculation completed successfully!")
    except Exception as e:
        messagebox.showerror("Error", str(e))


# Create the main window
root = tk.Tk()
root.title("Calculator")

# Fetch options for dropdown menus
material_options = fetch_options("SELECT material_id, material_name FROM materials")

# Add "Choose One" option
material_options = {"Choose One": None, **material_options}

# Initialize machine_options
machine_options = {}

# Create dropdown menus
Label(root, text="Pick material:").grid(row=2, column=0)
material_id_var = StringVar(root)
material_id_var.set("Choose One")  # default value
material_id_var.trace('w', update_machine_options)
material_id_menu = OptionMenu(root, material_id_var, *material_options.keys())
material_id_menu.grid(row=2, column=1)

Label(root, text="Pick machine:").grid(row=3, column=0)
machine_id_var = StringVar(root)
machine_id_var.set("Choose One")  # default value
machine_id_menu = OptionMenu(root, machine_id_var, "Choose One")
machine_id_menu.grid(row=3, column=1)


# Create and place labels and entry fields
tk.Label(root, text="Enter parts produced:").grid(row=0, column=0)
parts_produced_entry = tk.Entry(root)
parts_produced_entry.grid(row=0, column=1)

tk.Label(root, text="Enter number of builds:").grid(row=1, column=0)
numbers_of_builds_entry = tk.Entry(root)
numbers_of_builds_entry.grid(row=1, column=1)

tk.Label(root, text="Enter part mass in kg:").grid(row=4, column=0)
part_mass_entry = tk.Entry(root)
part_mass_entry.grid(row=4, column=1)

tk.Label(root, text="Enter part height in cm:").grid(row=5, column=0)
part_height_entry = tk.Entry(root)
part_height_entry.grid(row=5, column=1)

tk.Label(root, text="Enter part area in cm^2:").grid(row=6, column=0)
part_area_entry = tk.Entry(root)
part_area_entry.grid(row=6, column=1)

tk.Label(root, text="Enter support material as percent of mass (ex: 0.15):").grid(row=8, column=0)
support_material_entry = tk.Entry(root)
support_material_entry.grid(row=8, column=1)

# Create and place the submit button
submit_button = tk.Button(root, text="Submit", command=calculate)
submit_button.grid(row=9, column=0, columnspan=2)

# Run the application
root.mainloop()