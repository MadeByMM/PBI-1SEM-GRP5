import sqlite3
import hashlib
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from contextlib import closing
from PIL import Image, ImageTk
import re

# Users database file
con = sqlite3.connect("codebase/nexttech_users.db")
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

    # Clear entries only when switching from the login page
    if frame == login_frame:
        username_entry_login.delete(0, tk.END)
        password_entry_login.delete(0, tk.END)
        username_entry_login.focus()  
        root.bind('<Return>', lambda event: login())     
    else:
        root.unbind('<Return>')  # Unbind Enter on other frames

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
    
# MAIN WINDOW
root = tk.Tk()
root.title("Nexttech Calculator")
root.iconbitmap("codebase/next.ico")
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
image = Image.open("codebase/Nexttech logo.png")  
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
image_path = "codebase/button login.png"  # Replace with your image file path
image = Image.open(image_path)
image = image.resize((75, 40), Image.Resampling.LANCZOS)  # Resize to a button-friendly size
photo_image = ImageTk.PhotoImage(image)

# Login frame
login_frame = tk.Frame(background_frame, background="#D9D9D9")
login_frame.grid(row=3, column=2, columnspan=1, rowspan=1, padx=0, pady=0)

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
tk.Label(user_mainpage_frame, text="User Main Page", font=("Arial", 16)).grid(row=0, column=0, pady=10)

tk.Button(user_mainpage_frame, text="New Calculation", command=lambda: show_frame(New_calculation_frame)).grid(row=1, column=0, pady=20)
tk.Button(user_mainpage_frame, text="Calculation History", command= lambda: show_frame(Calculation_history_frame)).grid(row=2, column=0, pady=20)
tk.Button(user_mainpage_frame, text="Log out", command=lambda: show_frame(login_frame)).grid(row=3, column=0, pady=10)

# Frame for "admin" login
admin_mainpage_frame = tk.Frame(root)
tk.Label(admin_mainpage_frame, text="Admin Main Page", font=("Arial", 16)).grid(row=0, column=0, pady=10)

tk.Button(admin_mainpage_frame, text="New Calculation", command=lambda: show_frame(New_calculation_frame)).grid(row=1, column=0, pady=20)
tk.Button(admin_mainpage_frame, text="Calculation History", command=lambda: show_frame(Calculation_history_frame)).grid(row=2, column=0, pady=20)
tk.Button(admin_mainpage_frame, text="Price Settings", command= lambda: show_frame(price_settings_frame)).grid(row=3, column=0, pady=20)
tk.Button(admin_mainpage_frame, text="User Management", command=show_user_management_frame).grid(row=4, column=0, pady=20)
tk.Button(admin_mainpage_frame, text="Log out", command=lambda: show_frame(login_frame)).grid(row=5, column=0, pady=10)

# New calculation frame
New_calculation_frame = tk.Frame(root)
tk.Button(New_calculation_frame, text="Back", command=go_back).grid(row=0, column=0, pady=10, columnspan=2)

# Calculation History frame
Calculation_history_frame = tk.Frame(root)
tk.Button(Calculation_history_frame, text="Back", command=go_back).grid(row=0, column=0, pady=10, columnspan=2)

# "manage users" for admin login
User_Management_frame = tk.Frame(root)
tk.Label(User_Management_frame, text="User Settings", font=("Arial", 16)).grid(row=0, column=0, pady=10, columnspan=2)

# Username entry for acc creation
tk.Label(User_Management_frame, text="Username:").grid(row=1, column=0)
username_entry_user_management = tk.Entry(User_Management_frame)  # New entry
username_entry_user_management.grid(row=1, column=1)

# Password entry for acc creation
tk.Label(User_Management_frame, text="Password:").grid(row=2, column=0)
password_entry_user_management = tk.Entry(User_Management_frame, show="*")  # New entry
password_entry_user_management.grid(row=2, column=1)

# Role entry for account creation
tk.Label(User_Management_frame, text="Role:").grid(row=3, column=0)
role_options = ["Admin", "User"]  # Define available roles
role_entry = ttk.Combobox(User_Management_frame, values=role_options, state="readonly")
role_entry.grid(row=3, column=1)
role_entry.set("Choose Role")  # role entry prompt

# Create Treeview
user_tree = ttk.Treeview(User_Management_frame, columns=("ID", "Username", "Role"), show="headings")
user_tree.heading("ID", text="ID")
user_tree.heading("Username", text="Username")
user_tree.heading("Role", text="Role")

# Set column widths
user_tree.column("ID", width=50, anchor="center")         # Center align ID column
user_tree.column("Username", width=200, anchor="center")  # Center align Username column
user_tree.column("Role", width=100, anchor="center")      # Center align Role column

user_tree.grid(row=4, column=0, columnspan=2)

# Add scrollbar to users table
scrollbar = ttk.Scrollbar(User_Management_frame, orient="vertical", command=user_tree.yview)
user_tree.configure(yscroll=scrollbar.set)
scrollbar.grid(row=4, column=2, sticky='ns')

# create, delete, edit, refresh, back buttons
tk.Button(User_Management_frame, text="Create", command=create_acc).grid(row=5, column=0, pady=10)
tk.Button(User_Management_frame, text="Refresh Users", command=display_users).grid(row=6, column=0, pady=5)
tk.Button(User_Management_frame, text="Delete User", command=delete_acc).grid(row=7, column=0, pady=5)
tk.Button(User_Management_frame, text="Edit User", command=edit_acc).grid(row=8, column=0, pady=5)
tk.Button(User_Management_frame, text="Back", command=go_back).grid(row=9, column=0, pady=10)

price_settings_frame = tk.Frame(root)
tk.Button(price_settings_frame, text="Back", command=go_back).grid(row=0, column=0, pady=10, columnspan=2)

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
    frame.config(background="#333333") # Frame background color

initialize_database()
show_frame(background_frame)
root.after(100, lambda: username_entry_login.focus())
root.after(500, lambda: show_frame(login_frame))
root.mainloop()
