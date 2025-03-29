from encryption import * 
from database import *
from utils import *
from tkinter import filedialog, messagebox, simpledialog
from tkmacosx import Button

import tkinter as tk
import os
import time
import threading
import sys
import select

# === X Button Override Function ===
# Ensures the vault properly logs out when the window is closed
def on_closing(vault_window):
    handle_vault_action(5)

#=============== AutoLogout System ===============#
INACTIVITY_TIMEOUT = 30  # Time (in seconds) before auto-logout triggers
last_activity_time = time.time()  # Track last activity time
logout_active = False  # Controls if auto-logout thread runs
force_logout = False  # Tracks if logout was forced due to inactivity

# Resets the inactivity timer on user interaction
def reset_timer(event=None):
    global last_activity_time, force_logout
    last_activity_time = time.time()

# Handles auto-logout by tracking inactivity
def auto_logout():
    global logout_active, force_logout
    while logout_active:
        if time.time() - last_activity_time > INACTIVITY_TIMEOUT:
            logout_active = False
            force_logout = True  # Mark that the logout was due to inactivity
            break
        time.sleep(1)  # Sleep for a second before checking again
    handle_vault_action(5)  # Trigger logout

# Creates the vault window after successful login
# Initializes auto-logout and binds event listeners for user interaction

def create_vault_window(key, window):
    global logout_active, force_logout, last_activity_time

    # Reset and start auto-logout tracking
    last_activity_time = time.time()
    logout_active = True
    force_logout = False

    # Create a new window for the vault
    vault_window = tk.Toplevel()
    vault_window.title("Password Vault")
    vault_window.geometry("500x400")
    vault_window.configure(bg="#1E90FF") 

    center_window(vault_window)  # Centers the window on the screen
    add_logo(vault_window, "#1E90FF")  # Adds a logo if implemented in utils

    # Start auto-logout timer
    if not hasattr(window, 'auto_logout_thread'):
        window.auto_logout_thread = threading.Thread(target=auto_logout, daemon=True)
        window.auto_logout_thread.start()

    # Reset inactivity timer on any key or mouse click
    vault_window.bind_all("<KeyPress>", reset_timer)
    vault_window.bind_all("<Button-1>", reset_timer)

    # Handle X button closure
    vault_window.protocol("WM_DELETE_WINDOW", lambda: on_closing(vault_window))
    
    # =============== Vault Functionalities =============== #

    # Save a new password
    def save_new_password():
        website = simpledialog.askstring("Save New Password", "Enter the website name:")
        if not website:
            messagebox.showerror("Error", "Website name cannot be empty.")
            return

        username = simpledialog.askstring("Save New Password", "Enter the username:")

        # Ask user if they want to enter a custom password
        choice = messagebox.askyesno("Password Choice", "Do you want to create a custom password? (Yes for custom, No for random)")
        if choice:
            password = simpledialog.askstring("Custom Password", "Enter your custom password:", show='●')
            if not password:
                messagebox.showerror("Error", "Password cannot be empty.")
                return
        else:
            password = get_random_password()

        # Store the password in database, mark it 'c' for custom or 'r' for random
        insert_password(website, username, encrypt_password(password, key), 'c' if choice else 'r')

    # Retrieve and display a saved password
    def retrieve_password_and_username():
        website = simpledialog.askstring("Retrieve Password", "Enter the website name:")
        if not website:
            messagebox.showerror("Error", "Website name cannot be empty.")
            return

        encrypted_password = get_password(website)
        if encrypted_password is None:
            return

        decrypted_password = decrypt_password(encrypted_password, key)
        display_password(decrypted_password, website)

    # Delete a saved password
    def delete_password():
        website = simpledialog.askstring("Delete Password", "Enter the website name:")
        if not website:
            messagebox.showerror("Error", "Website name cannot be empty.")
            return

        if not messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete the password for this website?"):
            return

        delete_passwordEntry(website)

    # List all websites stored in the vault
    def list_websites():
        websites = get_all_websites()
        if not websites:
            messagebox.showinfo("No Websites", "No websites found in the vault.")
        else:
            website_list = '\n'.join([f"{index + 1}. {website}" for index, website in enumerate(websites)])
            messagebox.showinfo("Saved Websites", f"Websites saved in your vault:\n{website_list}")

    # Handles user actions in the vault
    global handle_vault_action
    def handle_vault_action(choice):
        if choice == 1:
            save_new_password()
        elif choice == 2:
            retrieve_password_and_username()
        elif choice == 3:
            delete_password()
        elif choice == 4:
            list_websites()
        elif choice == 5:
            # Handles logout, ensuring key is wiped and clipboard cleared
            if force_logout or messagebox.askyesno("Logout", "Are you sure you want to logout?"):
                clear_clipboard()
                key = os.urandom(32)
                del key
                window.deiconify()
                vault_window.destroy()
                if force_logout:
                    messagebox.showinfo("Auto Logout", "Vault locked due to inactivity.")
                else:
                    messagebox.showinfo("Logout", "You have logged out successfully.")
            return
        else:
            messagebox.showerror("Invalid Choice", "Please select a valid option.")

    # =============== Buttons Setup =============== #
    frame = tk.Frame(vault_window, bg="#1E90FF")
    frame.place(relx=0.5, rely=0.5, anchor="center")
    Button(frame, text="Save New Password", command=lambda: handle_vault_action(1), width=180, fg="#001F3F", font=("Tahoma", 12, "bold")).pack(pady=7)
    Button(frame, text="Retrieve Password", command=lambda: handle_vault_action(2), width=180, fg="#001F3F", font=("Tahoma", 12, "bold")).pack(pady=7)
    Button(frame, text="Delete Password", command=lambda: handle_vault_action(3), width=180, fg="#001F3F", font=("Tahoma", 12, "bold")).pack(pady=7)
    Button(frame, text="List Websites", command=lambda: handle_vault_action(4), width=180, fg="#001F3F", font=("Tahoma", 12, "bold")).pack(pady=7)
    Button(frame, text="Logout", command=lambda: handle_vault_action(5), width=180, fg="#001F3F", font=("Tahoma", 12, "bold")).pack(pady=7)

    vault_window.mainloop()  # Start the vault window event loop

