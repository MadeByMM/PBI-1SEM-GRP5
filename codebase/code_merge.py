import sqlite3
import hashlib
import tkinter as tk
from tkinter import *
from tkinter import messagebox
from tkinter import ttk, StringVar, OptionMenu
from contextlib import closing
from PIL import Image, ImageTk
import re
import customtkinter as ctk
from functools import partial
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg



###### HISTORY PAGE

# Connect to the database
con = sqlite3.connect('nexttech_calculator.db')
cur = con.cursor()
cur.execute("""SELECT c.calculation_id, c.date, c.project_name, n.machine_name, m.material_name, c.average_cost
            FROM calculations c
            JOIN materials m ON c.material_used = m.material_id
            JOIN machines n ON c.machine_used = n.machine_id""")




##### CALCULATIONS FUNCTIONS BACKEND

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
    con = sqlite3.connect('nexttech_calculator.db')
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
        con = sqlite3.connect('database/nexttech_calculator.db')
        cur = con.cursor()

        #project
        project_name = project_name_entry.get()
        parts_produced = int(parts_produced_entry.get())
        numbers_of_builds = int(numbers_of_builds_entry.get())
        
        machine_id = machine_options[machine_id_var.get()]
        material_id = material_options[material_id_var.get()]

        # Fetch the process based on the selected material and machine
        query = "SELECT with_process FROM combination WHERE using_material = ? AND in_machine = ?"
        process_id = cur.execute(query, (material_id, machine_id)).fetchone()
        if process_id is None:
            messagebox.showerror("Error", "No process found for the selected machine and material.")
            return
        process_id = process_id[0] 

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
        
        messagebox.showinfo("Success", "Calculation completed successfully!")

def save_calculation(name_pro, machine_id_var, material_id_var, parts_produced_entry, numbers_of_builds_entry):
        global total_cost, average_cost_per_part
        con = sqlite3.connect('database/nexttech_calculator.db')
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




##### LOGIN / ADMIN 

# Users database file
con = sqlite3.connect("nexttech_users.db")
previous_frame = None
current_username = ""

# db error handling
def handle_db_error(error):
    print(f"Database error: {error}")
    messagebox.showerror("Database Error", str(error))

# Initialize database and create the user table
def initialize_database():
    global con
    try:
        with closing(con.cursor()) as c:
            c.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    role TEXT
                )
            ''')
            con.commit()

    except sqlite3.Error as e:
        handle_db_error(e)

# Password hashing for security
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Username must be 5-20 characters and alphanumeric
def validate_username(username):
    if not (5 <= len(username) <= 20) or not username.isalnum():
        messagebox.showwarning("Invalid Username", 
            "Username must be between 5 and 20 characters and can only contain letters and numbers.")
        return False
    
    return True

# Password creation conditions
def validate_password(password):
    if (len(password) < 8 or
        not re.search(r"[A-Z]", password) or
        not re.search(r"\d", password) or
        not re.search(r"[!@#$%^&*()_+=-]", password)):
        
        messagebox.showwarning("Invalid Password", 
            "Password must contain at least 8 characters, at least one uppercase letter, at least one number, and at least one special character.")
        return False
    
    return True

# Add a new user to the database
def add_user(new_username, password, role):
    global con
    hashed_password = hash_password(password)
    print(f"Debug: Attempting to add user '{new_username}' with role '{role}'")
    try:
        with closing(con.cursor()) as c:
            # Check if the username already exists
            c.execute("SELECT username FROM users WHERE username = ?", (new_username,))
            if c.fetchone() is not None:
                messagebox.showwarning("Sign up failed", "Username already exists.")
                return
            # If the username doesn't exist, insert the new user
            c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                            (new_username, hashed_password, role))
            con.commit()
            print(f"Debug: User '{new_username}' created successfully!")
            return True 
    except sqlite3.Error as e:
        handle_db_error(e)
        return False 

# Verify user info
def verify_user(username, password):
    global con
    hashed_password = hash_password(password)
    print(f"Debug: Attempting to verify user '{username}' with hashed password '{hashed_password}'")
    try:       
        with closing(con.cursor()) as c:
            c.execute("SELECT role FROM users WHERE username = ? AND password = ?", 
                            (username, hashed_password))
            result = c.fetchone()
            print(f"Debug: Query result - {result}")
            return result[0] if result else None
    except sqlite3.Error as e:
        handle_db_error(e)
        return None

# User login
def login():
    global current_username

    # Read values from the entry fields
    username = username_entry_login.get().strip()  # Use the renamed variable
    password = password_entry_login.get().strip()  # Use the renamed variable

    # Debug: Print username and password before verification
    print(f"Debug: Username entered: '{username}', Password entered: '{password}'")

    user_role = verify_user(username, password)
    if user_role:
        messagebox.showinfo("Login successful", f"Welcome {username}!")
        current_username = username 
        username_entry_login.delete(0, tk.END)
        password_entry_login.delete(0, tk.END)
        if user_role == "admin":
            show_frame(admin_mainpage_frame)
        else:
            show_frame(user_mainpage_frame)
    else:
        messagebox.showwarning("Login failed", "Invalid username or password.")

# admin command
def create_acc():
    global con

    username = username_entry_user_management.get().strip()
    password = password_entry_user_management.get().strip()
    role = role_entry.get()

    # Validate username and password
    if not validate_username(username):
        return
    if not validate_password(password):
        return

    # Prevent empty role
    if not role:
        messagebox.showerror("Invalid Role", "Please select a role for the user.")
        return

    # Call add_user instead of executing the SQL directly
    success = add_user(username, password, role)
    if success:
        messagebox.showinfo("Success", f"User '{username}' has been created successfully.")
        display_users()  # Refresh the user list
        clear_user_management_fields()

# admin command
def edit_acc():
    global con
    selected_item = user_tree.selection()
    if not selected_item:
        messagebox.showwarning("Edit Who?","Please select a user to edit.")
        return

    # Get the current values of the selected user
    original_username = user_tree.item(selected_item)["values"][1]
    current_role = user_tree.item(selected_item)["values"][2]

    # Open a new window for editing
    edit_window = tk.Toplevel(root)
    edit_window.title("Edit User")

    tk.Label(edit_window, text="Edit Username:").pack()
    new_username_entry = tk.Entry(edit_window)
    new_username_entry.insert(0, original_username)  # Pre-fill with the original username
    new_username_entry.pack()

    tk.Label(edit_window, text="Edit Role:").pack()
    roles = ["Admin", "User"]  # Define available roles here
    role_var_edit = tk.StringVar(edit_window)  # Create a StringVar for the role
    role_dropdown = ttk.Combobox(edit_window, textvariable=role_var_edit, values=roles, state="readonly")  # Create readonly Combobox
    role_var_edit.set(current_role)  # Set the default selection to the current role
    role_dropdown.pack()

    tk.Label(edit_window, text="New Password (leave blank to keep current password):").pack()
    new_password_entry = tk.Entry(edit_window, show="*")  # New entry for password
    new_password_entry.pack()

    def save_changes():
        new_username = new_username_entry.get().strip()
        new_password = new_password_entry.get().strip()
        new_role = role_var_edit.get()

        # Validate username
        if not validate_username(new_username):
            return
        
        # Validate password if a new one is provided
        if new_password and not validate_password(new_password):
            return
        
        try:
            with closing(con.cursor()) as c:
                # Check if the new username already exists in the database
                if new_username != original_username:
                    c.execute("SELECT username FROM users WHERE username = ?", (new_username,))
                    if c.fetchone() is not None:
                        messagebox.showwarning("Try Again","The new username is already taken.")
                        return
                
                # Update username and role in the database
                c.execute("UPDATE users SET username = ?, role = ? WHERE username = ?", (new_username, new_role, original_username))
                
                # Update password if a new one is provided
                if new_password:
                    hashed_password = hash_password(new_password)
                    c.execute("UPDATE users SET password = ? WHERE username = ?", (hashed_password, new_username))
                
                con.commit()
                
                messagebox.showinfo("User Updated", f"User '{original_username}' has been updated.")
                display_users()  # Refresh the user list
                edit_window.destroy()  # Close the edit window

        except sqlite3.Error as e:
            handle_db_error(e)

    tk.Button(edit_window, text="Save Changes", command=save_changes).pack(pady=10)
    tk.Button(edit_window, text="Cancel", command=edit_window.destroy).pack(pady=5)

# admin command
def delete_acc():
    global con
    selected_item = user_tree.selection()  # Get the selected user in the Treeview
    if not selected_item:
        messagebox.showwarning("Select User", "Please select a user to delete.")
        return

    username = user_tree.item(selected_item)["values"][1]  # Get the username of the selected user
    
    # Confirmation dialog
    confirm = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete the user '{username}'?")
    if not confirm:
        return  # Exit the function if the user chooses 'No'

    try:        
        with closing(con.cursor()) as c:
            c.execute("DELETE FROM users WHERE username = ?", (username,))
            con.commit()
            messagebox.showinfo("Success", f"User '{username}' has been deleted.")
            display_users()  # Refresh the user list
    except sqlite3.Error as e:
        handle_db_error(e)
        
# Switch frames and clear entries
def show_frame(frame):
    global previous_frame
    if frame != previous_frame:
        previous_frame = root.winfo_children()[-1]

    frame.tkraise()

    if frame == background_frame or frame == login_frame:
        root.after(100, lambda: username_entry_login.focus()) 
        root.bind('<Return>', lambda event: login())  # Bind the Return key to login
        username_entry_login.delete(0, tk.END)  # Clear username field
        password_entry_login.delete(0, tk.END)  # Clear password field
    else:
        root.unbind('<Return>')  # Unbind Return on other frames

def logout():
    show_frame(background_frame)
# clear entry fields after creating a new user
def clear_user_management_fields():
    username_entry_user_management.delete(0, tk.END)
    password_entry_user_management.delete(0, tk.END)
    role_entry.set("Choose Role")

# Function to fetch and display users
def display_users():
    global con
    # Clear the current contents of the treeview
    for row in user_tree.get_children():
        user_tree.delete(row)

    # Fetch users from the database
    try:
        with closing(con.cursor()) as c:
            c.execute("SELECT id, username, role FROM users")
            users = c.fetchall()
            print(f"Debug: Current users in DB: {users}")

            # Insert users into the treeview along with the edit option
            for user in users:
                user_tree.insert("", "end", values=user)
    except sqlite3.Error as e:
        handle_db_error(e)
# User management Page
def show_user_management_frame():
    display_users()  
    show_frame(User_Management_frame)

# back button function
def go_back():
    if previous_frame:
        show_frame(previous_frame)

# Function to create a rounded rectangle on a canvas
# Function to create a rounded rectangle on a canvas
def create_rounded_rectangle(canvas, x1, y1, x2, y2, radius=25, fill='white', outline='black', width=1):
    """Create a rounded rectangle on the canvas."""
    points = [
        x1+radius, y1, x1, y1, x1, y1+radius, # Top-left corner
        x1, y2-radius, x1, y2, x1+radius, y2, # Bottom-left corner
        x2-radius, y2, x2, y2, x2, y2-radius, # Bottom-right corner
        x2, y1+radius, x2, y1, x2-radius, y1  # Top-right corner
    ]
    return canvas.create_polygon(points, fill=fill, outline=outline, width=width, smooth=True)

def on_button_click():
    login()

def on_focus_in(entry, placeholder_text):
    """Clear the placeholder text when the entry field gets focus"""
    if entry.get() == placeholder_text:
        entry.delete(0, ctk.END)
        entry.configure(fg_color="white")  # Reset text color to white when typing starts

def on_focus_out(entry, placeholder_text):
    """Restore the placeholder text if the entry field is empty"""
    if entry.get() == '':
        entry.insert(0, placeholder_text)
        entry.configure(fg_color="#D3D3D3")

def connect_db():
    conn = sqlite3.connect("nexttech_users.db")
    return conn.cursor()

# Function to search the Treeview based on query
def search_treeview(query):
    # Clear current entries in the Treeview
    for item in user_tree.get_children():
        user_tree.delete(item)
    
    # Query the database for users matching the search query
    cursor = connect_db()
    cursor.execute("SELECT id, username, role FROM users WHERE username LIKE ? OR role LIKE ?", ('%' + query + '%', '%' + query + '%'))
    rows = cursor.fetchall()

    # Insert matching rows into the Treeview
    for row in rows:
        user_tree.insert("", "end", values=row)

# Function to connect to the database and fetch all machines data
def fetch_machines():
    with closing(sqlite3.connect("nexttech_calculator.db")) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute("SELECT * FROM machines")
            machines = cursor.fetchall()
    return machines

# Function to fetch attributes of the selected machine
def fetch_machine_attributes(selected_machine):
    with closing(sqlite3.connect("nexttech_calculator.db")) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute("SELECT * FROM machines WHERE Machine_Name=?", (selected_machine,))
            machine_attributes = cursor.fetchone()
    return machine_attributes

# Function to fetch column names from the 'machines' table
def fetch_machine_columns():
    with closing(sqlite3.connect("nexttech_calculator.db")) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute("PRAGMA table_info(machines)")
            columns_machine = cursor.fetchall()
    return [column[1] for column in columns_machine]  # Extracting the column names

# Function to create a Treeview for the selected machine
def populate_machine_treeview(frame, machine_data):

     # Clear existing data
    for row in machine_tree.get_children():
        machine_tree.delete(row)

    # Fetch the column names
    attribute_names = fetch_machine_columns()
    for i, attribute_name in enumerate(attribute_names):
        # Replace underscores with spaces in attribute names
        attribute_display_name = attribute_name.replace("_", " ")
        attribute_value = machine_data[i]  # Access each attribute's value directly from the tuple
        machine_tree.insert("", "end", values=(attribute_display_name, attribute_value))
    
def on_machine_selected(event):
    selected_machine = combobox_machine.get()
    machine_data = fetch_machine_attributes(selected_machine)
    
    print(f"Debug: Machine data fetched: {machine_data}")  # Check the fetched data
    
    if machine_data:
        populate_machine_treeview(frame, machine_data)
    else:
        messagebox.showerror("Error", "Machine not found.")

# Function to create a new machine (prompt entry fields for every attribute)
def create_new_machine():
    machine_columns = fetch_machine_columns()  # Get column names from the table
    entry_fields = {}

    # Create a new window to prompt for the machine attributes
    create_window = tk.Toplevel(root)
    create_window.title("Create New Machine")

    # Dynamically create labels and entry fields for each column in the 'machines' table
    row = 0
    for column in machine_columns[1:]:  # Skip the ID column (usually the first column)
        label = tk.Label(create_window, text=column.replace("_", " ").title() + ":")
        label.grid(row=row, column=0, padx=10, pady=5, sticky="w")
        
        entry = tk.Entry(create_window)
        entry.grid(row=row, column=1, padx=10, pady=5)
        
        entry_fields[column] = entry
        row += 1

    # Button to save the new machine to the database
    def save_new_machine():
        # Collect all values from the entry fields
        values = [entry.get() for entry in entry_fields.values()]

        if all(values):  # Ensure all fields are filled
            machine_name = values[0]  # Assuming that Machine_Name is the first column

            # Check if the machine name already exists
            with closing(sqlite3.connect("nexttech_calculator.db")) as conn:
                with closing(conn.cursor()) as cursor:
                    cursor.execute("SELECT COUNT(*) FROM machines WHERE Machine_Name = ?", (machine_name,))
                    count = cursor.fetchone()[0]

                    if count > 0:  # Machine name already exists
                        messagebox.showerror("Error", f"A machine with the name '{machine_name}' already exists.")
                        return

            # Create the insert statement dynamically
            column_names = ', '.join(entry_fields.keys())  # Join column names with commas
            placeholders = ', '.join(['?'] * len(entry_fields))  # Create placeholders for each field

            # Prepare the insert statement
            insert_query = f"INSERT INTO machines ({column_names}) VALUES ({placeholders})"
            
            with closing(sqlite3.connect("nexttech_calculator.db")) as conn:
                with closing(conn.cursor()) as cursor:
                    cursor.execute(insert_query, values)  # Pass values to be inserted
                    conn.commit()

            messagebox.showinfo("Success", "Machine created successfully.")
            create_window.destroy()  # Close the window after success
        else:
            messagebox.showerror("Error", "All fields must be filled.")

    save_button = tk.Button(create_window, text="Save", command=save_new_machine)
    save_button.grid(row=row, column=0, columnspan=2, pady=10)

# Function to edit an existing machine (prompt entry fields for every attribute)
def edit_machine():
    selected_machine = combobox_machine.get()

    if selected_machine:
        machine_columns = fetch_machine_columns()  # Get column names
        machine_data = fetch_machine_attributes(selected_machine)  # Fetch existing data

        if machine_data:
            # Create a new window to prompt for the machine attributes
            edit_window = tk.Toplevel(root)
            edit_window.title(f"Edit Machine - {selected_machine}")

            entry_fields = {}

            # Dynamically create labels and entry fields for each column in the 'machines' table
            row = 0
            for idx, column in enumerate(machine_columns[1:]):  # Skip the ID column (usually the first column)
                label = tk.Label(edit_window, text=column.replace("_", " ").title() + ":")
                label.grid(row=row, column=0, padx=10, pady=5, sticky="w")
                
                entry = tk.Entry(edit_window)
                entry.insert(0, machine_data[idx + 1])  # Set the initial value to the existing data
                entry.grid(row=row, column=1, padx=10, pady=5)
                
                entry_fields[column] = entry
                row += 1

            # Button to save the edited machine to the database
            def save_edited_machine():
                values = [entry.get() for entry in entry_fields.values()]
                if all(values):  # Ensure all fields are filled
                    new_machine_name = values[0]  # Assuming Machine_Name is the first field

                    # Check if the new machine name already exists (except for the selected machine)
                    with closing(sqlite3.connect("nexttech_calculator.db")) as conn:
                        with closing(conn.cursor()) as cursor:
                            cursor.execute(
                                "SELECT COUNT(*) FROM machines WHERE Machine_Name = ? AND Machine_Name != ?",
                                (new_machine_name, selected_machine)
                            )
                            count = cursor.fetchone()[0]

                            if count > 0:  # New machine name already exists
                                messagebox.showerror("Error", f"A machine with the name '{new_machine_name}' already exists.")
                                return

                            # Dynamically create the update query to update all fields
                            set_clause = ", ".join([f"{column} = ?" for column in machine_columns[1:]])  # Skip the ID column
                            cursor.execute(
                                f"UPDATE machines SET {set_clause} WHERE Machine_Name = ?",
                                (*values, selected_machine)  # Pass all the values and selected machine name
                            )
                            conn.commit()

                    messagebox.showinfo("Success", "Machine updated successfully.")
                    edit_window.destroy()
                else:
                    messagebox.showerror("Error", "All fields must be filled.")

            save_button = tk.Button(edit_window, text="Save", command=save_edited_machine)
            save_button.grid(row=row, column=0, columnspan=2, pady=10)
        else:
            messagebox.showerror("Error", "Machine not found.")
    else:
        messagebox.showerror("Error", "No machine selected to edit.")


# Function to delete a machine
def delete_machine():
    selected_machine = combobox_machine.get()

    if selected_machine:
        # Fetch the machine data to ensure it's the correct one
        machine_data = fetch_machine_attributes(selected_machine)
        
        if machine_data:
            # Confirm deletion with a message box
            confirm = messagebox.askyesno("Delete Machine", f"Are you sure you want to delete the machine '{selected_machine}'?")
            
            if confirm:
                with closing(sqlite3.connect("nexttech_calculator.db")) as conn:
                    with closing(conn.cursor()) as cursor:
                        # Delete the selected machine based on the Machine_Name
                        cursor.execute("DELETE FROM machines WHERE Machine_Name = ?", (selected_machine,))
                        conn.commit()
                
                messagebox.showinfo("Success", "Machine deleted successfully.")
            else:
                messagebox.showinfo("Canceled", "Machine deletion canceled.")
        else:
            messagebox.showerror("Error", "Machine not found.")
    else:
        messagebox.showerror("Error", "No machine selected to delete.")


# Function to fetch column names from the 'operations' table
def fetch_operation_columns():
    with closing(sqlite3.connect("nexttech_calculator.db")) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute("PRAGMA table_info(operations)")  # Fetch all column names
            operation_columns = cursor.fetchall()
    return [column[1] for column in operation_columns]  # Extract and return column names

# Function to fetch all operations IDs for combobox
def fetch_operations():
    with closing(sqlite3.connect("nexttech_calculator.db")) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute("SELECT operations_id FROM operations")
            operations = cursor.fetchall()
    return [operation for operation in operations]  # Extract operation IDs

# Function to fetch attributes of the selected operation by ID
def fetch_operation_attributes(selected_operation):
    with closing(sqlite3.connect("nexttech_calculator.db")) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute("SELECT * FROM operations WHERE operations_id=?", (selected_operation,))
            operation_attributes = cursor.fetchone()
    return operation_attributes

# Function to create a Treeview for the selected operation
def populate_operation_treeview(frame, operation_data):
    # Clear existing data
    for row in operation_tree.get_children():
        operation_tree.delete(row)
    
    # Fetch the column names
    attribute_names = fetch_operation_columns()
    
    # Populate the Treeview with the operation data
    for i, attribute_name in enumerate(attribute_names):
        # Ensure there is data for each attribute
        if i < len(operation_data):
            attribute_display_name = attribute_name.replace("_", " ")
            attribute_value = operation_data[i]
            operation_tree.insert("", "end", values=(attribute_display_name, attribute_value))

# Event handler for selecting an operation in the combobox
def on_operation_selected(event):
    selected_operation_id = combobox_operation.get()  # Retrieve selected operation ID
    if selected_operation_id.isdigit():  # Ensure it’s a valid integer ID
        operation_data = fetch_operation_attributes(int(selected_operation_id))
        if operation_data:
            populate_operation_treeview(price_change_frame, operation_data)
        else:
            messagebox.showerror("Error", "Operation not found.")

# Function to create a new operation (prompt entry fields for every attribute)
def create_new_operation():
    operation_columns = fetch_operation_columns()  # Get column names from the table
    entry_fields = {}

    # Create a new window to prompt for the operation attributes
    create_window = tk.Toplevel(root)
    create_window.title("Create New Operation")

    # Dynamically create labels and entry fields for each column in the 'operations' table
    row = 0
    for column in operation_columns[0:]:  # Start from column=0
        label = tk.Label(create_window, text=column.replace("_", " ").title() + ":")
        label.grid(row=row, column=0, padx=10, pady=5, sticky="w")
        
        entry = tk.Entry(create_window)
        entry.grid(row=row, column=1, padx=10, pady=5)
        
        entry_fields[column] = entry
        row += 1

    # Button to save the new operation to the database
    def save_new_operation():
        # Collect all values from the entry fields
        values = [entry.get() for entry in entry_fields.values()]

        if all(values):  # Ensure all fields are filled
            operations_id = values[0]  # Assuming that Operation_Name is the first column

            # Check if the operation name already exists
            with closing(sqlite3.connect("nexttech_calculator.db")) as conn:
                with closing(conn.cursor()) as cursor:
                    cursor.execute("SELECT COUNT(*) FROM operations WHERE operations_id = ?", (operations_id,))
                    count = cursor.fetchone()[0]

                    if count > 0:  # Operation name already exists
                        messagebox.showerror("Error", f"An operation with the name '{operations_id}' already exists.")
                        return

            # Create the insert statement dynamically
            column_names = ', '.join(entry_fields.keys())  # Join column names with commas
            placeholders = ', '.join(['?'] * len(entry_fields))  # Create placeholders for each field

            # Prepare the insert statement
            insert_query = f"INSERT INTO operations ({column_names}) VALUES ({placeholders})"
            
            with closing(sqlite3.connect("nexttech_calculator.db")) as conn:
                with closing(conn.cursor()) as cursor:
                    cursor.execute(insert_query, values)  # Pass values to be inserted
                    conn.commit()

            messagebox.showinfo("Success", "Operation created successfully.")
            create_window.destroy()  # Close the window after success
        else:
            messagebox.showerror("Error", "All fields must be filled.")

    save_button = tk.Button(create_window, text="Save", command=save_new_operation)
    save_button.grid(row=row, column=0, columnspan=2, pady=10)

# Function to edit an existing operation (prompt entry fields for every attribute)
def edit_operation():
    selected_operation = combobox_operation.get()

    if selected_operation:
        operation_columns = fetch_operation_columns()  # Get column names
        operation_data = fetch_operation_attributes(selected_operation)  # Fetch existing data

        if operation_data:
            # Create a new window to prompt for the operation attributes
            edit_window = tk.Toplevel(root)
            edit_window.title(f"Edit Operation - {selected_operation}")

            entry_fields = {}

            # Dynamically create labels and entry fields for each column in the 'operations' table
            row = 0
            for idx, column in enumerate(operation_columns[1:]):  # Skip the ID column (usually the first column)
                label = tk.Label(edit_window, text=column.replace("_", " ").title() + ":")
                label.grid(row=row, column=0, padx=10, pady=5, sticky="w")
                
                entry = tk.Entry(edit_window)
                entry.insert(0, operation_data[idx + 1])  # Set the initial value to the existing data
                entry.grid(row=row, column=1, padx=10, pady=5)
                
                entry_fields[column] = entry
                row += 1

            # Button to save the edited operation to the database
            def save_edited_operation():
                values = [entry.get() for entry in entry_fields.values()]
                if all(values):  # Ensure all fields are filled
                    with closing(sqlite3.connect("nexttech_calculator.db")) as conn:
                        with closing(conn.cursor()) as cursor:
                            # Dynamically create the update query to update all fields
                            set_clause = ", ".join([f"{column} = ?" for column in operation_columns[1:]])  # Skip the ID column
                            cursor.execute(
                                f"UPDATE operations SET {set_clause} WHERE Operation_id = ?",
                                (*values, selected_operation)  # Pass all the values and selected operation name
                            )
                            conn.commit()
                    messagebox.showinfo("Success", "Operation updated successfully.")
                    edit_window.destroy()
                else:
                    messagebox.showerror("Error", "All fields must be filled.")

            save_button = tk.Button(edit_window, text="Save", command=save_edited_operation)
            save_button.grid(row=row, column=0, columnspan=2, pady=10)
        else:
            messagebox.showerror("Error", "Operation not found.")
    else:
        messagebox.showerror("Error", "No operation selected to edit.")

# Function to delete an operation
def delete_operation():
    selected_operation = combobox_operation.get()

    if selected_operation:
        # Fetch the operation data to ensure it's the correct one
        operation_data = fetch_operation_attributes(selected_operation)
        
        if operation_data:
            # Confirm deletion with a message box
            confirm = messagebox.askyesno("Delete Operation", f"Are you sure you want to delete the operation '{selected_operation}'?")
            
            if confirm:
                with closing(sqlite3.connect("nexttech_calculator.db")) as conn:
                    with closing(conn.cursor()) as cursor:
                        # Delete the selected operation based on the Operations_id
                        cursor.execute("DELETE FROM operations WHERE Operation_id = ?", (selected_operation,))
                        conn.commit()
                
                messagebox.showinfo("Success", "Operation deleted successfully.")
            else:
                messagebox.showinfo("Canceled", "Operation deletion canceled.")
        else:
            messagebox.showerror("Error", "Operation not found.")
    else:
        messagebox.showerror("Error", "No operation selected to delete.")

#########PROCESSEs##############

# Function to connect to the database and fetch all processes data
def fetch_processes():
    with closing(sqlite3.connect("nexttech_calculator.db")) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute("SELECT * FROM processes")
            processes = cursor.fetchall()
    return processes

# Function to fetch attributes of the selected process
def fetch_process_attributes(selected_process):
    with closing(sqlite3.connect("nexttech_calculator.db")) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute("SELECT * FROM processes WHERE Process_Name=?", (selected_process,))
            process_attributes = cursor.fetchone()
    return process_attributes

# Function to fetch column names from the 'processes' table
def fetch_process_columns():
    with closing(sqlite3.connect("nexttech_calculator.db")) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute("PRAGMA table_info(processes)")
            columns_processes = cursor.fetchall()
    return [column[1] for column in columns_processes]  # Extracting the column names

# Function to create a Treeview for the selected process
def populate_process_treeview(frame, process_data):
    # Clear existing data
    for row in process_tree.get_children():
        process_tree.delete(row)
    # Fetch the column names
    attribute_names = fetch_process_columns()
    for i, attribute_name in enumerate(attribute_names):
        # Replace underscores with spaces in attribute names
        attribute_display_name = attribute_name.replace("_", " ")
        attribute_value = process_data[i]  # Access each attribute's value directly from the tuple
        process_tree.insert("", "end", values=(attribute_display_name, attribute_value))

def on_process_selected(event):
    selected_process = combobox_process.get()
    process_data = fetch_process_attributes(selected_process)
    print(f"Debug: Process data fetched: {process_data}")  # Check the fetched data
    if process_data:
        populate_process_treeview(frame, process_data)
    else:
        messagebox.showerror("Error", "Process not found.")

# Function to create a new process (prompt entry fields for every attribute)
def create_new_process():
    process_columns = fetch_process_columns()  # Get column names from the table
    entry_fields = {}

    # Create a new window to prompt for the process attributes
    create_window = tk.Toplevel(root)
    create_window.title("Create New Process")

    # Dynamically create labels and entry fields for each column in the 'processes' table
    row = 0
    for column in process_columns[1:]:  # Skip the ID column (usually the first column)
        label = tk.Label(create_window, text=column.replace("_", " ").title() + ":")
        label.grid(row=row, column=0, padx=10, pady=5, sticky="w")
        
        entry = tk.Entry(create_window)
        entry.grid(row=row, column=1, padx=10, pady=5)
        
        entry_fields[column] = entry
        row += 1

    # Button to save the new process to the database
    def save_new_process():
        # Collect all values from the entry fields
        values = [entry.get() for entry in entry_fields.values()]

        if all(values):  # Ensure all fields are filled
            process_name = values[0]  # Assuming that Process_Name is the first column

            # Check if the process name already exists
            with closing(sqlite3.connect("nexttech_calculator.db")) as conn:
                with closing(conn.cursor()) as cursor:
                    cursor.execute("SELECT COUNT(*) FROM processes WHERE Process_Name = ?", (process_name,))
                    count = cursor.fetchone()[0]

                    if count > 0:  # Process name already exists
                        messagebox.showerror("Error", f"A process with the name '{process_name}' already exists.")
                        return

            # Create the insert statement dynamically
            column_names = ', '.join(entry_fields.keys())  # Join column names with commas
            placeholders = ', '.join(['?'] * len(entry_fields))  # Create placeholders for each field

            # Prepare the insert statement
            insert_query = f"INSERT INTO processes ({column_names}) VALUES ({placeholders})"
            
            with closing(sqlite3.connect("nexttech_calculator.db")) as conn:
                with closing(conn.cursor()) as cursor:
                    cursor.execute(insert_query, values)  # Pass values to be inserted
                    conn.commit()

            messagebox.showinfo("Success", "Process created successfully.")
            create_window.destroy()  # Close the window after success
        else:
            messagebox.showerror("Error", "All fields must be filled.")

    save_button = tk.Button(create_window, text="Save", command=save_new_process)
    save_button.grid(row=row, column=0, columnspan=2, pady=10)

# Function to edit an existing process (prompt entry fields for every attribute)
def edit_process():
    selected_process = combobox_process.get()

    if selected_process:
        process_columns = fetch_process_columns()  # Get column names
        process_data = fetch_process_attributes(selected_process)  # Fetch existing data

        if process_data:
            # Create a new window to prompt for the process attributes
            edit_window = tk.Toplevel(root)
            edit_window.title(f"Edit Process - {selected_process}")

            entry_fields = {}

            # Dynamically create labels and entry fields for each column in the 'processes' table
            row = 0
            for idx, column in enumerate(process_columns[1:]):  # Skip the ID column (usually the first column)
                label = tk.Label(edit_window, text=column.replace("_", " ").title() + ":")
                label.grid(row=row, column=0, padx=10, pady=5, sticky="w")
                
                entry = tk.Entry(edit_window)
                entry.insert(0, process_data[idx + 1])  # Set the initial value to the existing data
                entry.grid(row=row, column=1, padx=10, pady=5)
                
                entry_fields[column] = entry
                row += 1

            # Button to save the edited process to the database
            def save_edited_process():
                values = [entry.get() for entry in entry_fields.values()]
                if all(values):  # Ensure all fields are filled
                    with closing(sqlite3.connect("nexttech_calculator.db")) as conn:
                        with closing(conn.cursor()) as cursor:
                            # Dynamically create the update query to update all fields
                            set_clause = ", ".join([f"{column} = ?" for column in process_columns[1:]])  # Skip the ID column
                            cursor.execute(
                                f"UPDATE processes SET {set_clause} WHERE Process_Name = ?",
                                (*values, selected_process)  # Pass all the values and selected process name
                            )
                            conn.commit()
                    messagebox.showinfo("Success", "Process updated successfully.")
                    edit_window.destroy()
                else:
                    messagebox.showerror("Error", "All fields must be filled.")

            save_button = tk.Button(edit_window, text="Save", command=save_edited_process)
            save_button.grid(row=row, column=0, columnspan=2, pady=10)
        else:
            messagebox.showerror("Error", "Process not found.")
    else:
        messagebox.showerror("Error", "No process selected to edit.")

# Function to delete a process
def delete_process():
    selected_process = combobox_process.get()

    if selected_process:
        # Fetch the process data to ensure it's the correct one
        process_data = fetch_process_attributes(selected_process)
        
        if process_data:
            # Confirm deletion with a message box
            confirm = messagebox.askyesno("Delete Process", f"Are you sure you want to delete the process '{selected_process}'?")
            
            if confirm:
                with closing(sqlite3.connect("nexttech_calculator.db")) as conn:
                    with closing(conn.cursor()) as cursor:
                        # Delete the selected process based on the Process_Name
                        cursor.execute("DELETE FROM processes WHERE Process_Name = ?", (selected_process,))
                        conn.commit()
                
                messagebox.showinfo("Success", "Process deleted successfully.")
            else:
                messagebox.showinfo("Canceled", "Process deletion canceled.")
        else:
            messagebox.showerror("Error", "Process not found.")
    else:
        messagebox.showerror("Error", "No process selected to delete.")
######## MATERIALS########

# Function to connect to the database and fetch all materials data
def fetch_materials():
    with closing(sqlite3.connect("nexttech_calculator.db")) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute("SELECT * FROM materials")
            materials = cursor.fetchall()
    return materials

# Function to fetch attributes of the selected material
def fetch_material_attributes(selected_material):
    with closing(sqlite3.connect("nexttech_calculator.db")) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute("SELECT * FROM materials WHERE Material_Name=?", (selected_material,))
            material_attributes = cursor.fetchone()
    return material_attributes

# Function to fetch column names from the 'materials' table
def fetch_material_columns():
    with closing(sqlite3.connect("nexttech_calculator.db")) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute("PRAGMA table_info(materials)")
            columns_materials = cursor.fetchall()
    return [column[1] for column in columns_materials]  # Extracting the column names

# Function to create a Treeview for the selected material
def populate_material_treeview(frame, material_data):
    # Clear existing data
    for row in material_tree.get_children():
        material_tree.delete(row)
    # Fetch the column names
    attribute_names = fetch_material_columns()
    for i, attribute_name in enumerate(attribute_names):
        # Replace underscores with spaces in attribute names
        attribute_display_name = attribute_name.replace("_", " ")
        attribute_value = material_data[i]  # Access each attribute's value directly from the tuple
        material_tree.insert("", "end", values=(attribute_display_name, attribute_value))

def on_material_selected(event):
    selected_material = combobox_material.get()
    material_data = fetch_material_attributes(selected_material)
    print(f"Debug: Material data fetched: {material_data}")  # Check the fetched data
    if material_data:
        populate_material_treeview(frame, material_data)
    else:
        messagebox.showerror("Error", "Material not found.")

# Function to create a new material (prompt entry fields for every attribute)
def create_new_material():
    material_columns = fetch_material_columns()  # Get column names from the table
    entry_fields = {}

    # Create a new window to prompt for the material attributes
    create_window = tk.Toplevel(root)
    create_window.title("Create New Material")

    # Dynamically create labels and entry fields for each column in the 'materials' table
    row = 0
    for column in material_columns[1:]:  # Skip the ID column (usually the first column)
        label = tk.Label(create_window, text=column.replace("_", " ").title() + ":")
        label.grid(row=row, column=0, padx=10, pady=5, sticky="w")
        
        entry = tk.Entry(create_window)
        entry.grid(row=row, column=1, padx=10, pady=5)
        
        entry_fields[column] = entry
        row += 1

    # Button to save the new material to the database
    def save_new_material():
        # Collect all values from the entry fields
        values = [entry.get() for entry in entry_fields.values()]

        if all(values):  # Ensure all fields are filled
            material_name = values[0]  # Assuming that Material_Name is the first column

            # Check if the material name already exists
            with closing(sqlite3.connect("nexttech_calculator.db")) as conn:
                with closing(conn.cursor()) as cursor:
                    cursor.execute("SELECT COUNT(*) FROM materials WHERE Material_Name = ?", (material_name,))
                    count = cursor.fetchone()[0]

                    if count > 0:  # Material name already exists
                        messagebox.showerror("Error", f"A material with the name '{material_name}' already exists.")
                        return

            # Create the insert statement dynamically
            column_names = ', '.join(entry_fields.keys())  # Join column names with commas
            placeholders = ', '.join(['?'] * len(entry_fields))  # Create placeholders for each field

            # Prepare the insert statement
            insert_query = f"INSERT INTO materials ({column_names}) VALUES ({placeholders})"
            
            with closing(sqlite3.connect("nexttech_calculator.db")) as conn:
                with closing(conn.cursor()) as cursor:
                    cursor.execute(insert_query, values)  # Pass values to be inserted
                    conn.commit()

            messagebox.showinfo("Success", "Material created successfully.")
            create_window.destroy()  # Close the window after success
        else:
            messagebox.showerror("Error", "All fields must be filled.")

    save_button = tk.Button(create_window, text="Save", command=save_new_material)
    save_button.grid(row=row, column=0, columnspan=2, pady=10)

# Function to edit an existing material (prompt entry fields for every attribute)
def edit_material():
    selected_material = combobox_material.get()

    if selected_material:
        material_columns = fetch_material_columns()  # Get column names
        material_data = fetch_material_attributes(selected_material)  # Fetch existing data

        if material_data:
            # Create a new window to prompt for the material attributes
            edit_window = tk.Toplevel(root)
            edit_window.title(f"Edit Material - {selected_material}")

            entry_fields = {}

            # Dynamically create labels and entry fields for each column in the 'materials' table
            row = 0
            for idx, column in enumerate(material_columns[1:]):  # Skip the ID column (usually the first column)
                label = tk.Label(edit_window, text=column.replace("_", " ").title() + ":")
                label.grid(row=row, column=0, padx=10, pady=5, sticky="w")
                
                entry = tk.Entry(edit_window)
                entry.insert(0, material_data[idx + 1])  # Set the initial value to the existing data
                entry.grid(row=row, column=1, padx=10, pady=5)
                
                entry_fields[column] = entry
                row += 1

            # Button to save the edited material to the database
            def save_edited_material():
                values = [entry.get() for entry in entry_fields.values()]
                if all(values):  # Ensure all fields are filled
                    with closing(sqlite3.connect("nexttech_calculator.db")) as conn:
                        with closing(conn.cursor()) as cursor:
                            # Dynamically create the update query to update all fields
                            set_clause = ", ".join([f"{column} = ?" for column in material_columns[1:]])  # Skip the ID column
                            cursor.execute(
                                f"UPDATE materials SET {set_clause} WHERE Material_Name = ?",
                                (*values, selected_material)  # Pass all the values and selected material name
                            )
                            conn.commit()
                    messagebox.showinfo("Success", "Material updated successfully.")
                    edit_window.destroy()
                else:
                    messagebox.showerror("Error", "All fields must be filled.")

            save_button = tk.Button(edit_window, text="Save", command=save_edited_material)
            save_button.grid(row=row, column=0, columnspan=2, pady=10)
        else:
            messagebox.showerror("Error", "Material not found.")
    else:
        messagebox.showerror("Error", "No material selected to edit.")

# Function to delete a material
def delete_material():
    selected_material = combobox_material.get()

    if selected_material:
        # Fetch the material data to ensure it's the correct one
        material_data = fetch_material_attributes(selected_material)
        
        if material_data:
            # Confirm deletion with a message box
            confirm = messagebox.askyesno("Delete Material", f"Are you sure you want to delete the material '{selected_material}'?")
            
            if confirm:
                with closing(sqlite3.connect("nexttech_calculator.db")) as conn:
                    with closing(conn.cursor()) as cursor:
                        # Delete the selected material based on the Material_Name
                        cursor.execute("DELETE FROM materials WHERE Material_Name = ?", (selected_material,))
                        conn.commit()
                
                messagebox.showinfo("Success", "Material deleted successfully.")
            else:
                messagebox.showinfo("Canceled", "Material deletion canceled.")
        else:
            messagebox.showerror("Error", "Material not found.")
    else:
        messagebox.showerror("Error", "No material selected to delete.")

# MAIN WINDOW
root = tk.Tk()
root.title("Nexttech Calculator")
root.iconbitmap("next.ico")
root.geometry("1280x720")  # Set initial app window size
root.config(background ="#333333" )
root.grid_rowconfigure(0, weight=1)  # Allow row 0 to expand
root.grid_columnconfigure(0, weight=1)  # Allow column 0 to expand
# PARENT FRAMES

# Parent frame of login_frame
background_frame = tk.Frame(root, background="#333333")
background_frame.grid(row=0, column=0, sticky="nsew")
# Footer text on login page
footer_label = tk.Label(background_frame, text="IBA Nexttech © 2024 - PBI-1SEM-GRP5", bg="#333333", fg="white", font=("Inter", 8))
footer_label.grid(row=9, column=2, columnspan=1, pady=(10, 5), sticky="s")

for i in range(10):
    background_frame.grid_rowconfigure(i, weight=1) 
for i in range(5):
    background_frame.grid_columnconfigure(i, weight=1)

# Nexttech Logo on login screen
image = Image.open("Nexttech logo.png")  
image = image.resize((108, 108), Image.Resampling.LANCZOS)  # Resize image if needed
tk_image = ImageTk.PhotoImage(image)

# Add the image to the frame using a Label
image_label = tk.Label(background_frame, image=tk_image, bg="#333333")
image_label.grid(row=2, column=2, padx=0, pady=(0, 20))

# Create a canvas with a rounded rectangle to simulate rounded corners
canvas = tk.Canvas(background_frame, width=250, height=150, bg="#333333", bd=0, highlightthickness=0)
canvas.grid(row=3, column=2, columnspan=1, rowspan=1, padx=0, pady=0)

# Draw a rounded rectangle on the canvas for the login frame
create_rounded_rectangle(canvas, 0, 0, 250, 150, radius=25, fill="#D9D9D9")

# Create an image button
image_path = "button login.png"  # Replace with your image file path
image = Image.open(image_path)
image = image.resize((75, 40), Image.Resampling.LANCZOS)  # Resize to a button-friendly size
photo_image = ImageTk.PhotoImage(image)

# Login frame
login_frame = tk.Frame(background_frame, background="#D9D9D9")
login_frame.grid(row=3, column=2, columnspan=1, rowspan=1, padx=0, pady=0)
login_frame.bind("<Return>", lambda event: login())

# Round image button
image_button = tk.Button(login_frame, image=photo_image, command=on_button_click,bg="#D9D9D9", bd=0, activebackground="#D9D9D9")  # Remove border for a clean look
image_button.grid(row=2, columnspan=2, sticky="e", padx=25)

tk.Label(login_frame, text="Username:",bg="#D9D9D9",font=("Inter", 15)).grid(row=0, column=0, padx=5, pady=5)
username_entry_login = tk.Entry(login_frame, width=10, font=("Inter", 14))
username_entry_login.grid(row=0, column=1, padx=5, pady=5)

tk.Label(login_frame, text="Password:",bg="#D9D9D9",font=("Inter", 15)).grid(row=1, column=0, padx=5, pady=5)
password_entry_login = tk.Entry(login_frame, show='*', width=10, font=("Inter", 14))
password_entry_login.grid(row=1, column=1, padx=5, pady=5)

# button down below is deaktivatet and replaced with image button

#login_button = tk.Button(login_frame, text="Login",bg="#ffffff",font=("Inter", 15),relief="flat", command=login, width=5)
#login_button.grid(row=2, columnspan=2, sticky="e", padx=25)

# Frame for "user" login
user_mainpage_frame = tk.Frame(root)

ctk.CTkButton(
    user_mainpage_frame,
    text="New Calculation", 
    command=lambda: show_frame(New_calculation_frame), 
    corner_radius=10, 
    fg_color="#D9D9D9", 
    text_color="#000000",
    font=("Inter", 15),
    width=180, 
    height=50
).grid(row=1, column=0, padx=5, sticky="nw")

ctk.CTkButton(
    user_mainpage_frame,
    text="Calculation History", 
    command=lambda: show_frame(Calculation_history_frame), 
    corner_radius=10, 
    fg_color="#D9D9D9", 
    text_color="#000000",
    font=("Inter", 15),
    width=180, 
    height=50
).grid(row=2, column=0, padx=5, sticky="nw")

ctk.CTkButton(
    user_mainpage_frame,
    text="Log out", 
    command=logout, 
    corner_radius=10, 
    fg_color="#D9D9D9", 
    text_color="#000000",
    font=("Inter", 15),
    width=180, 
    height=50
).grid(row=10, column=0, padx=5, sticky="nw")

for i in range(20):  
    user_mainpage_frame.grid_rowconfigure(i, weight=1)
for i in range(12):
    user_mainpage_frame.grid_columnconfigure(0, weight=1)

# Frame for "admin" login
admin_mainpage_frame = tk.Frame(root)

ctk.CTkButton(
    admin_mainpage_frame, 
    text="New Calculation", 
    command=lambda: show_frame(New_calculation_frame), 
    corner_radius=10, 
    fg_color="#D9D9D9", 
    text_color="#000000",
    font=("Inter", 15),
    width=180, 
    height=50
).grid(row=1, column=0, padx=5, sticky="nw")

ctk.CTkButton(
    admin_mainpage_frame, 
    text="Calculation History", 
    command=lambda: show_frame(Calculation_history_frame), 
    corner_radius=10, 
    fg_color="#D9D9D9", 
    text_color="#000000",
    font=("Inter", 15),
    width=180, 
    height=50
).grid(row=2, column=0, padx=5, sticky="nw")

ctk.CTkButton(
    admin_mainpage_frame, 
    text="Price Settings", 
    command=lambda: show_frame(price_settings_frame), 
    corner_radius=10, 
    fg_color="#D9D9D9", 
    text_color="#000000",
    font=("Inter", 15),
    width=180, 
    height=50
).grid(row=3, column=0, padx=5, sticky="nw")

ctk.CTkButton(
    admin_mainpage_frame, 
    text="User Management", 
    command=show_user_management_frame, 
    corner_radius=10, 
    fg_color="#D9D9D9", 
    text_color="#000000",
    font=("Inter", 15),
    width=180, 
    height=50
).grid(row=4, column=0, padx=5, sticky="nw")

ctk.CTkButton(
    admin_mainpage_frame, 
    text="Log out", 
    command=logout, 
    corner_radius=10, 
    fg_color="#D9D9D9", 
    text_color="#000000",
    font=("Inter", 15),
    width=180, 
    height=50
).grid(row=10, column=0, padx=5, sticky="nw")

for i in range(20):  
    admin_mainpage_frame.grid_rowconfigure(i, weight=1)
for i in range(12):
    admin_mainpage_frame.grid_columnconfigure(i, weight=1)

# New calculation frame
New_calculation_frame = tk.Frame(root)

ctk.CTkButton(
    New_calculation_frame, 
    text="Back", 
    command=go_back, 
    corner_radius=10, 
    fg_color="#D9D9D9", 
    text_color="#000000",
    font=("Inter", 15),
    width=180, 
    height=50
).place(x=25, y=25)

for i in range(20):  
    New_calculation_frame.grid_rowconfigure(i, weight=1)
for i in range(12):
    New_calculation_frame.grid_columnconfigure(i, weight=1)

# Calculation History frame
Calculation_history_frame = tk.Frame(root)

ctk.CTkButton(
    Calculation_history_frame, 
    text="Back", 
    command=go_back, 
    corner_radius=10, 
    fg_color="#D9D9D9", 
    text_color="#000000",
    font=("Inter", 15),
    width=180, 
    height=50
).grid(row=10, column=0, padx=5, sticky="nw")

for i in range(20):  
    Calculation_history_frame.grid_rowconfigure(i, weight=1)
for i in range(12):
    Calculation_history_frame.grid_columnconfigure(i, weight=1)

# Frame for user management
User_Management_frame = tk.Frame(root)
#gray frame 
add_user_frame = tk.Frame(User_Management_frame, width=510, height=650, bg="#D9D9D9", bd=0, relief="solid", highlightbackground="#00A3EE", highlightthickness=2)
add_user_frame.grid(row=1, column=1, rowspan=28, columnspan=8, padx=10, pady=10, sticky="nsew")

tk.Label(add_user_frame, text="New user",font=("Inter", 18), fg="#00A3EE",  bg="#D9D9D9").grid(row=0, column=2, sticky="w", padx=(10, 5), pady=20)

# Username entry
username_entry_user_management = ctk.CTkEntry(add_user_frame, font=("Inter", 12), fg_color="#FFFFFF")  # Set default placeholder color
username_entry_user_management.grid(row=2, column=2, sticky="w", pady=5)
username_entry_user_management.insert(0, "Enter username")  # Placeholder text

# Bind events for username field
username_entry_user_management.bind("<FocusIn>", lambda event: on_focus_in(username_entry_user_management, "Enter username"))
username_entry_user_management.bind("<FocusOut>", lambda event: on_focus_out(username_entry_user_management, "Enter username"))

# Password entry
password_entry_user_management = ctk.CTkEntry(add_user_frame, font=("Inter", 12), fg_color="#FFFFFF")  
password_entry_user_management.grid(row=4, column=2, sticky="w", pady=5)
password_entry_user_management.insert(0, "Enter password")  

# Bind events for password field
password_entry_user_management.bind("<FocusIn>", lambda event: on_focus_in(password_entry_user_management, "Enter password"))
password_entry_user_management.bind("<FocusOut>", lambda event: on_focus_out(password_entry_user_management, "Enter password"))

# Role entry
role_options = ["Admin", "User"]  # Define available roles
role_entry = ttk.Combobox(add_user_frame, values=role_options,font=("Inter", 12), state="readonly")
role_entry.grid(row=6, column=2, sticky="w",pady=5)
role_entry.set("Choose Role")

tk.Label(
    User_Management_frame, 
    text="Registered Users", 
    font=("Inter", 20), 
    fg="#D9D9D9",  # Font color
    bg="#333333"   # Label background color
).grid(row=1, column=10, columnspan=3, sticky="nsew")

# Search
placeholder_text = "Search in users"
search_entry = ctk.CTkEntry(User_Management_frame, font=("Inter", 14), fg_color="#FFFFFF")
search_entry.grid(row=2, column=10, pady=5, sticky="nsew")
search_entry.insert(0, placeholder_text)

# Bind focus in and out events for placeholder functionality
search_entry.bind("<FocusIn>", lambda event: on_focus_in(search_entry, placeholder_text))
search_entry.bind("<FocusOut>", lambda event: on_focus_out(search_entry, placeholder_text))

style = ttk.Style()
style.configure("Custom.Treeview", font=("Inter", 12))  # Set font and size
style.configure("Custom.Treeview.Heading", font=("Inter", 14, "bold"))  # Header font

# Customizing Treeview
style.map("Custom.Treeview", background=[("selected", "#D9D9D9")])  # Row selection color
style.configure("Custom.Treeview", background="#D9D9D9", fieldbackground="#D9D9D9")  # Default row and cell background

# Customizing Treeview Header
style.configure("Custom.Treeview.Heading", foreground="#000000", font=("Inter", 14))  # Header background color and text color
style.map("Custom.Treeview.Heading", background=[("active", "#000000")])  # Active header color

# Treeview with scrollbar
user_tree = ttk.Treeview(User_Management_frame, style="Custom.Treeview", columns=("ID", "Username", "Role"), show="headings")
user_tree.heading("ID", text="ID")
user_tree.heading("Username", text="Username")
user_tree.heading("Role", text="Role")

# Set column widths and alignment for Treeview
user_tree.column("ID", width=50, anchor="center")
user_tree.column("Username", width=200, anchor="center")
user_tree.column("Role", width=100, anchor="center")
user_tree.grid(row=3, column=10, rowspan=6, columnspan=3, sticky="nsew")  # Placing Treeview in upper right

search_entry.bind("<KeyRelease>", lambda event: search_treeview(search_entry.get()))

# Add scrollbar for Treeview
user_scrollbar = ttk.Scrollbar(User_Management_frame, orient="vertical", command=user_tree.yview)
user_tree.configure(yscroll=user_scrollbar.set)

# Place scrollbar in the grid, ensuring it stays within the height of the Treeview
user_scrollbar.grid(row=3, column=13, rowspan=6, sticky="nsw")  # The scrollbar aligns with Treeview
style.configure("TScrollbar", gripcount=0, background="#00A3EE", troughcolor="#D9D9D9", bordercolor="#00A3EE")

# Ensure the frame can stretch and the Treeview + Scrollbar can fill the entire area
User_Management_frame.grid_rowconfigure(1, weight=1)  # Ensures the first row expands vertically
User_Management_frame.grid_columnconfigure(10, weight=1)  # Ensures column 10 expands horizontally (for Treeview)
User_Management_frame.grid_columnconfigure(13, weight=0)  # Scrollbar column doesn't need to expand horizontally

# Optionally, ensure the Treeview expands vertically across the grid row
User_Management_frame.grid_rowconfigure(1, weight=1) 

# Buttons
ctk.CTkButton(
    add_user_frame, 
    text="Create new user", 
    command=create_acc, 
    corner_radius=10, 
    fg_color="#ffffff", 
    text_color="#000000",
    font=("Inter", 15),
    width=90, 
    height=30
).grid(row=7, column=2, padx=5,pady=10,sticky="e")

ctk.CTkButton(
    User_Management_frame, 
    text="Refresh Users", 
    command=display_users, 
    corner_radius=10, 
    fg_color="#D9D9D9", 
    text_color="#000000",
    font=("Inter", 15),
    width=90, 
    height=30
).grid(row=10, column=10, padx=5, sticky="nw")

ctk.CTkButton(
    User_Management_frame, 
    text="Delete User", 
    command=delete_acc, 
    corner_radius=10, 
    fg_color="#D9D9D9", 
    text_color="#000000",
    font=("Inter", 15),
    width=90, 
    height=30
).grid(row=10, column=12, padx=5, sticky="nw")

ctk.CTkButton(
    User_Management_frame, 
    text="Edit User", 
    command=edit_acc, 
    corner_radius=10, 
    fg_color="#D9D9D9", 
    text_color="#000000",
    font=("Inter", 15),
    width=90, 
    height=30
).grid(row=10, column=11, padx=5, sticky="nw")

ctk.CTkButton(
    User_Management_frame, 
    text="Back", 
    command=go_back, 
    corner_radius=10, 
    fg_color="#D9D9D9", 
    text_color="#000000",
    font=("Inter", 15),
    width=180, 
    height=50
).grid(row=1, column=0, padx=5, sticky="nw")

 # adjust row/column for user_management_frame
for i in range(30):  
    User_Management_frame.grid_rowconfigure(i, weight=1)
for i in range(15):
    User_Management_frame.grid_columnconfigure(i, weight=1)

for i in range(5):
    add_user_frame.grid_columnconfigure(i, weight=1)

price_settings_frame = tk.Frame(root)
for i in range(30):  
    price_settings_frame.grid_rowconfigure(i, weight=1)
for i in range(15):
    price_settings_frame.grid_columnconfigure(i, weight=1)

ctk.CTkButton(
    price_settings_frame, 
    text="Back", 
    command=go_back, 
    corner_radius=10, 
    fg_color="#D9D9D9", 
    text_color="#000000",
    font=("Inter", 15),
    width=180, 
    height=50
).grid(row=10, column=0, padx=5, sticky="nw")

frames = [
    background_frame, user_mainpage_frame, admin_mainpage_frame,
    New_calculation_frame, Calculation_history_frame,
    User_Management_frame, price_settings_frame
    ]
# POSITION PARENT FRAMES IN ROOT, ALLOW THEM EXPAND WITH ROOT, BG COLOR
for frame in frames:
    frame.grid(row=0, column=0, sticky="nsew")  # Grid all frames to the same position
    frame.grid_rowconfigure(0, weight=1)  # Allow frames to expand vertically
    frame.grid_columnconfigure(0, weight=1)  # Allow frames to expand horizontally
    frame.config(background="#333333") 

price_change_frame = tk.Frame(price_settings_frame, width=800, height=650, bg="#D9D9D9", bd=0, relief="solid",highlightcolor="#00A3EE", highlightbackground="#00A3EE", highlightthickness=2)
price_change_frame.grid(row=1, column=1, rowspan=28, columnspan=2, padx=10, pady=10, sticky="nsew")
price_change_frame.grid_propagate(False)

# borders for dividing price_change_frame in 4
price_label_row = tk.Label(price_change_frame, text="", bg="#00A3EE", )
price_label_row.grid(row=3, column=0, columnspan=15,sticky="ew")

price_label_col = tk.Label(price_change_frame, text="", bg="#00A3EE", width=2)
price_label_col.grid(row=0, column=4, rowspan=30, sticky="ns")

for i in range(10):  
    price_change_frame.grid_rowconfigure(i, weight=1)
for i in range(15):
    price_change_frame.grid_columnconfigure(i, weight=1)
price_change_frame.grid_rowconfigure(4, weight=1, minsize=1)  

### MACHINES GUI
machines = fetch_machines()
machine_names = [machine[1] for machine in machines]  

# Combobox to select machine (placed in price_change_frame)
combobox_machine = ttk.Combobox(price_change_frame, values=machine_names, state="readonly")
combobox_machine.grid(row=0, column=0, padx=10, pady=10)
combobox_machine.set("Select printer")
combobox_machine.bind("<<ComboboxSelected>>", on_machine_selected)

# Frame to hold the Treeview and scrollbar
treeview_frame_machine = tk.Frame(price_change_frame)
treeview_frame_machine.grid(row=2, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")
treeview_frame_machine.grid_rowconfigure(0, weight=1)
treeview_frame_machine.grid_columnconfigure(0, weight=1)

# machine treeview
columns_machine = ["Attribute", "Value"]
machine_tree = ttk.Treeview(treeview_frame_machine, columns=columns_machine, show="headings", height=6)
machine_tree.heading("Attribute", text="Attribute")
machine_tree.heading("Value", text="Value")
machine_tree.grid(row=0, column=0, sticky="nsew")

# Machine scrollbar
machine_scrollbar = ttk.Scrollbar(treeview_frame_machine, orient="vertical", command=machine_tree.yview)
machine_tree.configure(yscroll=machine_scrollbar.set)
machine_scrollbar.grid(row=0, column=1, sticky="ns")

# machine buttons
create_button_machine = tk.Button(price_change_frame, text="Create Machine", command=create_new_machine)
create_button_machine.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")

edit_button_machine = tk.Button(price_change_frame, text="Edit Machine", command=edit_machine)
edit_button_machine.grid(row=1, column=1, padx=10, pady=5, sticky="nsew")

delete_button_machine = tk.Button(price_change_frame, text="Delete Machine", command=delete_machine)
delete_button_machine.grid(row=1, column=2, padx=10, pady=5, sticky="nsew")

operations = fetch_operations()
operation_names = [operation[0] for operation in operations]  


###  OPERATIONS GUI

# Combobox to select operation (placed in price_change_frame)
combobox_operation = ttk.Combobox(price_change_frame, values=operation_names, state="readonly")
combobox_operation.grid(row=0, column=5, padx=10, pady=10)
combobox_operation.set("Select operation")
combobox_operation.bind("<<ComboboxSelected>>", on_operation_selected)

# Frame to hold the Treeview and scrollbar
treeview_frame_operations = tk.Frame(price_change_frame)
treeview_frame_operations.grid(row=2, column=5, columnspan=3, padx=10, pady=10, sticky="nsew")
treeview_frame_operations.grid_rowconfigure(0, weight=1)
treeview_frame_operations.grid_columnconfigure(0, weight=1)

# operation treeview
columns_operation = ["Attribute", "Value"]
operation_tree = ttk.Treeview(treeview_frame_operations, columns=columns_operation, show="headings", height=6)
operation_tree.heading("Attribute", text="Attribute")
operation_tree.heading("Value", text="Value")
operation_tree.grid(row=0, column=0, sticky="nsew")


# Scrollbar for the Treeview
scrollbar = ttk.Scrollbar(treeview_frame_operations, orient="vertical", command=operation_tree.yview)
scrollbar.grid(row=0, column=1, sticky="ns")
operation_tree.config(yscrollcommand=scrollbar.set)

# Buttons
create_button = tk.Button(price_change_frame, text="Create New Operation", command=create_new_operation)
create_button.grid(row=1, column=5, padx=10, pady=5)

edit_button = tk.Button(price_change_frame, text="Edit Operation", command=edit_operation)
edit_button.grid(row=1, column=6, padx=10, pady=5)

delete_button = tk.Button(price_change_frame, text="Delete Operation", command=delete_operation)
delete_button.grid(row=1, column=7, padx=10, pady=5)

##### PROCESSES USER INTERFACE
processes = fetch_processes()
process_names = [process[1] for process in processes]  

# Combobox to select process (placed in price_change_frame)
combobox_process = ttk.Combobox(price_change_frame, values=process_names, state="readonly")
combobox_process.grid(row=4, column=0, padx=10, pady=10)
combobox_process.set("Select process")
combobox_process.bind("<<ComboboxSelected>>", on_process_selected)

# Frame to hold the Treeview and scrollbar
treeview_frame_process = tk.Frame(price_change_frame)
treeview_frame_process.grid(row=6, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")
treeview_frame_process.grid_rowconfigure(0, weight=1)
treeview_frame_process.grid_columnconfigure(0, weight=1)

# Process treeview
columns_process = ["Attribute", "Value"]
process_tree = ttk.Treeview(treeview_frame_process, columns=columns_process, show="headings", height=6)
process_tree.grid(row=0, column=0, sticky="nsew")

# Adding headers
for col in columns_process:
    process_tree.heading(col, text=col)

# Scrollbar for the Treeview
scrollbar = ttk.Scrollbar(treeview_frame_process, orient="vertical", command=process_tree.yview)
scrollbar.grid(row=0, column=1, sticky="ns")
process_tree.config(yscrollcommand=scrollbar.set)

# Buttons
create_button = tk.Button(price_change_frame, text="Create New Process", command=create_new_process)
create_button.grid(row=5, column=0, padx=10, pady=5)

edit_button = tk.Button(price_change_frame, text="Edit Process", command=edit_process)
edit_button.grid(row=5, column=1, padx=10, pady=5)

delete_button = tk.Button(price_change_frame, text="Delete Process", command=delete_process)
delete_button.grid(row=5, column=2, padx=10, pady=5)

#### MATERIALS USER INTERFACE

materials = fetch_materials()
material_names = [material[1] for material in materials]  

# Combobox to select material (placed in price_change_frame)
combobox_material = ttk.Combobox(price_change_frame, values=material_names, state="readonly")
combobox_material.grid(row=4, column=5, padx=10, pady=10)
combobox_material.set("Select material")
combobox_material.bind("<<ComboboxSelected>>", on_material_selected)

# Frame to hold the Treeview and scrollbar
treeview_frame_material = tk.Frame(price_change_frame)
treeview_frame_material.grid(row=6, column=5, columnspan=3, padx=10, pady=10, sticky="nsew")
treeview_frame_material.grid_rowconfigure(0, weight=1)
treeview_frame_material.grid_columnconfigure(0, weight=1)

# Material treeview
columns_material = ["Attribute", "Value"]
material_tree = ttk.Treeview(treeview_frame_material, columns=columns_material, show="headings", height=6)
material_tree.grid(row=0, column=0, sticky="nsew")

# Adding headers
for col in columns_material:
    material_tree.heading(col, text=col)

# Scrollbar for the Treeview
scrollbar = ttk.Scrollbar(treeview_frame_material, orient="vertical", command=material_tree.yview)
scrollbar.grid(row=0, column=1, sticky="ns")
material_tree.config(yscrollcommand=scrollbar.set)

# Buttons
create_button = tk.Button(price_change_frame, text="Create New Material", command=create_new_material)
create_button.grid(row=5, column=5, padx=10, pady=5)

edit_button = tk.Button(price_change_frame, text="Edit Material", command=edit_material)
edit_button.grid(row=5, column=6, padx=10, pady=5)

delete_button = tk.Button(price_change_frame, text="Delete Material", command=delete_material)
delete_button.grid(row=5, column=7, padx=10, pady=5)

#### CALCULATION PAGE

# Fetch options for dropdown menus
material_options = fetch_options("SELECT material_id, material_name FROM materials")

# Add "Choose One" option
material_options = {"Choose One": None, **material_options}

# Initialize machine_options
machine_options = {}

#Frame around calculation
frame2 = ctk.CTkFrame(New_calculation_frame,
                    fg_color=("#CDCCCC"),
                    bg_color=("#333333"),
                    height=670,
                    width=510)
frame2.place(x=740, y=25)

#Headline Calculation
overskrift2 = ctk.CTkLabel(New_calculation_frame, text = "Calculation",
                        font = ("Arial",32, "bold"),
                        text_color=("#0377AC"),
                        bg_color =("#CDCCCC"),width=300, justify=CENTER)
overskrift2.place(x=840, y=35,)

# Save button, MISSING A COMMAND
save_button = ctk.CTkButton(New_calculation_frame, command=lambda: save_calculation(name_pro, machine_id_var, material_id_var, parts_produced_entry, numbers_of_builds_entry),
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
frame1 = ctk.CTkFrame(New_calculation_frame,
                    fg_color=("#CDCCCC"),
                    bg_color=("#333333"),
                    height=670,
                    width=480)
frame1.place(x=231, y=25)

#Headline
overskrift1 = ctk.CTkLabel(New_calculation_frame, text = "New calculation",
                        font = ("Arial",32, "bold"),
                        text_color=("#0377AC"),
                        bg_color =("#CDCCCC"),width=300, justify=CENTER)
overskrift1.place(x=321, y=35,)



# Name project, MISSING A COMMAND
name_pro = ctk.CTkEntry(New_calculation_frame,
                        placeholder_text="Name your project",
                        font=("Arial", 20),
                        text_color=("#0377AC"),
                        fg_color=("#FFFFFF"), bg_color=("#CDCCCC"),
                        height=35, width=300,
                        corner_radius=20, border_color="#0377AC", border_width=2)
name_pro.place(x=321, y=85)


#Pick Machine; dropdown menus
label4 = ctk.CTkLabel(New_calculation_frame, text="Pick machine:", font=("Arial", 18), text_color=("#0377AC"), bg_color=("#CDCCCC"),
                    anchor="e", width=180)
label4.place(x=270, y=320)

machine_id_var = StringVar(root)
machine_id_var.set("Choose One")  # default value
machine_id_menu = OptionMenu(New_calculation_frame, machine_id_var, "Choose One")
machine_id_menu.place(x=480, y=320)

# Pick Materials; dropdown menus
label3 = ctk.CTkLabel(New_calculation_frame, text="Pick material:", font=("Arial", 18), text_color=("#0377AC"), bg_color=("#CDCCCC"),
                    anchor="e", width=180)
label3.place(x=270, y=270)

material_id_var = StringVar(New_calculation_frame)
material_id_var.set("Choose One")  # default value
material_id_var.trace_add('write', partial(update_machine_options, machine_id_var, material_id_var, machine_id_menu, material_options))
material_id_menu = OptionMenu(New_calculation_frame, material_id_var, *material_options.keys())
material_id_menu.place(x=480, y=270)

# Enter parts produced
label1 = ctk.CTkLabel(New_calculation_frame, text="Enter parts produced:", font=("Arial", 18), text_color=("#0377AC"), bg_color=("#CDCCCC"),
                    anchor="e", width=180)
label1.place(x=270, y=170)
parts_produced_entry = ctk.CTkEntry(New_calculation_frame, fg_color=("#FFFFFF"), bg_color=("#CDCCCC"), height=30, width=177, corner_radius=20, border_color="#0377AC", border_width=2)
parts_produced_entry.place(x=480, y=170)

# Enter number of builds
label2 = ctk.CTkLabel(New_calculation_frame, text="Enter number of builds:", font=("Arial", 18), text_color=("#0377AC"), bg_color=("#CDCCCC"),
                    anchor="e", width=180)
label2.place(x=270, y=220)
numbers_of_builds_entry = ctk.CTkEntry(New_calculation_frame, fg_color=("#FFFFFF"), bg_color=("#CDCCCC"), height=30, width=177, corner_radius=20, border_color="#0377AC", border_width=2)
numbers_of_builds_entry.place(x=480, y=220)

# Enter part mass in kg 
label5 = ctk.CTkLabel(New_calculation_frame, text="Enter part mass in kg:", font=("Arial", 18), text_color=("#0377AC"), bg_color=("#CDCCCC"),
                    anchor="e", width=180)
label5.place(x=270, y=370)
part_mass_entry = ctk.CTkEntry(New_calculation_frame, fg_color=("#FFFFFF"), bg_color=("#CDCCCC"), height=30, width=177, corner_radius=20, border_color="#0377AC", border_width=2,
                             placeholder_text="Kg.", placeholder_text_color=("#7A7A7A"))
part_mass_entry.place(x=480, y=370)

# Enter part height in cm
label6 = ctk.CTkLabel(New_calculation_frame, text="Enter part height in cm:", font=("Arial", 18), text_color=("#0377AC"), bg_color=("#CDCCCC"),
                    anchor="e", width=180)
label6.place(x=270, y=420)
part_height_entry = ctk.CTkEntry(New_calculation_frame, fg_color=("#FFFFFF"), bg_color=("#CDCCCC"), height=30, width=177, corner_radius=20, border_color="#0377AC", border_width=2,
                               placeholder_text="cm", placeholder_text_color=("#7A7A7A"))
part_height_entry.place(x=480, y=420)

# Enter part area in cm^2
label7 = ctk.CTkLabel(New_calculation_frame, text="Enter part area in cm^2:", font=("Arial", 18), text_color=("#0377AC"), bg_color=("#CDCCCC"),
                    anchor="e", width=180)
label7.place(x=270, y=470)
part_area_entry = ctk.CTkEntry(New_calculation_frame, fg_color=("#FFFFFF"), bg_color=("#CDCCCC"), height=30, width=177, corner_radius=20, border_color="#0377AC", border_width=2,
                                    placeholder_text="cm^2", placeholder_text_color=("#7A7A7A"))
part_area_entry.place(x=480, y=470)

# Enter support material as percent of mass
label8 = ctk.CTkLabel(New_calculation_frame, text="Enter support material:", font=("Arial", 18), text_color=("#0377AC"), bg_color=("#CDCCCC"),
                    anchor="e", width=180)
label8.place(x=270, y=520)
support_material_entry = ctk.CTkEntry(New_calculation_frame, fg_color=("#FFFFFF"), bg_color=("#CDCCCC"), height=30, width=177, corner_radius=20, border_color="#0377AC", border_width=2,
                                    placeholder_text="percent of mass (ex.0.15)", placeholder_text_color=("#7A7A7A"))
support_material_entry.place(x=480, y=520)

# Reset button, MISSING A COMMAND
reset_button = ctk.CTkButton(New_calculation_frame,
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
submit_button = ctk.CTkButton(New_calculation_frame, command=lambda: calculate(name_pro, machine_id_var, material_id_var, parts_produced_entry, numbers_of_builds_entry, part_mass_entry, material_id_menu, material_options, part_height_entry, part_area_entry, support_material_entry),
                        text="Submit",
                        font=("Arial", 24),
                        text_color=("#FFFFFF"),
                        fg_color=("#77AC03"),
                        bg_color=("#CDCCCC"),
                        height=40, width=150,
                        hover_color="#527605",
                        corner_radius=20)
submit_button.place(x=500, y=620)

###### HISTORY PAGE

headers = ["ID", "Date", "Project Name", "Machine", "Material", "Cost per part", "Details"]
sort_order = ["ASC", "DESC"]
current_order = [0, 0, 0, 0]

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

    details_window = Toplevel(Calculation_history_frame)
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
    for widget in Calculation_history_frame.winfo_children():
        if isinstance(widget, ctk.CTkLabel) or isinstance(widget, ctk.CTkButton):
            widget.destroy()

    for j, header in enumerate(headers):
        header_button = ctk.CTkButton(Calculation_history_frame, text=header,text_color="black", font=("Arial", 16, "bold"), fg_color="#C6C5C5",border_width=2 ,border_color="#0377AC", command=lambda j=j: sort_by_column(j))
        header_button.grid(row=0, column=j, padx=10, pady=5)

    rows = cur.fetchall()
    for i, row in enumerate(rows):
        for j, value in enumerate(row):
            cell = ctk.CTkLabel(Calculation_history_frame, text=value, font=("Arial", 12), text_color="#0377AC")
            cell.grid(row=i+1, column=j, padx=10, pady=5)
        details_button = ctk.CTkButton(Calculation_history_frame, text="Details", font=("Arial", 10), command=lambda row=row: view_details(row[0]))
        details_button.grid(row=i+1, column=6, padx=10, pady=5)

for j, header in enumerate(headers):
    header_label = ctk.CTkLabel(Calculation_history_frame, text=header, font=("Arial", 16, "bold"))
    header_label.grid(row=0, column=j, padx=10, pady=5)
update_table()
while True:
    rows = cur.fetchall()
    if not rows:
        break

    for i, row in enumerate(rows):
        for i, row in enumerate(rows):
            for j, value in enumerate(row):
                cell = ctk.CTkLabel(Calculation_history_frame, text=value, font=("Arial", 12),text_color="#0377AC")
                cell.grid(row=i+1, column=j, padx=10, pady=5)
                details_button = ctk.CTkButton(Calculation_history_frame, text="Details", font=("Arial", 10))
                details_button.grid(row=i+1, column=4, padx=10, pady=5)

initialize_database()
show_frame(background_frame)
root.after(100, lambda: username_entry_login.focus())
root.after(500, lambda: show_frame(login_frame))
root.mainloop()