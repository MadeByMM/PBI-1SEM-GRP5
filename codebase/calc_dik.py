import sqlite3
import hashlib
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from contextlib import closing
from PIL import Image, ImageTk
import re
import customtkinter as ctk
import sqlite3



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
    conn = sqlite3.connect("codebase/nexttech_users.db")
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
).grid(row=10, column=0, padx=5, sticky="nw")

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
scrollbar = ttk.Scrollbar(User_Management_frame, orient="vertical", command=user_tree.yview)
user_tree.configure(yscroll=scrollbar.set)

# Place scrollbar in the grid, ensuring it stays within the height of the Treeview
scrollbar.grid(row=3, column=13, rowspan=6, sticky="nsw")  # The scrollbar aligns with Treeview
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
#gray frame 
price_change_frame = tk.Frame(price_settings_frame, width=510, height=650, bg="#D9D9D9", bd=0, relief="solid", highlightbackground="#00A3EE", highlightthickness=2)
price_change_frame.grid(row=1, column=1, rowspan=28, columnspan=2, padx=10, pady=10, sticky="nsew")

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

for i in range(30):  
    price_settings_frame.grid_rowconfigure(i, weight=1)
for i in range(15):
    price_settings_frame.grid_columnconfigure(i, weight=1)

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

initialize_database()
show_frame(background_frame)
root.after(100, lambda: username_entry_login.focus())
root.after(500, lambda: show_frame(login_frame))
root.mainloop()




