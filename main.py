import os
import sys

from database import *
from encryption import *
from utils import *

from tkinter import filedialog, messagebox, simpledialog
from PIL import Image, ImageTk
from tkmacosx import Button

import tkinter as tk
import time

# Force path to find bundled site-packages (required for the MacOS app)
if getattr(sys, 'frozen', False):
    bundle_dir = os.path.dirname(sys.executable)
    sys.path.insert(0, os.path.join(bundle_dir, "Resources", "site-packages"))
else:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "site-packages"))


# Define constants for lockout time, max attempts, and token for vault verification
LOCKOUT_TIME = 300
MAX_ATTEMPTS = 5
TOKEN = "MAYANK'S SPM"
keyfile_path = os.path.expanduser("~/.secure_pm/keyfile.key")


# X Button Override Function 
def on_closing(window):
    """Ensure clean exit on window close (overrides default behavior)."""
    exit()


# Check if Vault Exists 
def vault_exists():
    """Checks if the vault metadata indicates an existing vault."""
    return get_VAULT_EXISTS()


# Sign Up Function 
def sign_up():
    if vault_exists():
        messagebox.showerror("Sign Up Failed", "Cannot Sign up. Vault already exists.")
    else:
        # Get master password input
        master_password = simpledialog.askstring("Sign Up", "Enter Master Password for your Password Vault:", show='●')
        if master_password == "" or master_password is None:
            messagebox.showerror("Sign Up Failed", "Master Password cannot be empty.")
            return

        # Verify password input
        mp_confirm = simpledialog.askstring("Sign Up", "Enter Master Password again to verify:", show='●')
        if master_password != mp_confirm:
            messagebox.showerror("Sign Up Failed", "Verification failed. Passwords do not match.")
            return

        # Hash the master password securely
        hashed_mp = hash_mp(master_password)

        # Create keyfile directory if it doesn't exist
        keyfile_folder = os.path.dirname(keyfile_path)
        if not os.path.exists(keyfile_folder):
            os.makedirs(keyfile_folder)

        # Generate keyfile and handle errors
        if not gen_keyfile(keyfile_path):
            messagebox.showerror("Sign Up Failed", "An error occurred while generating key file.")
            return

        # Encrypt a predefined token for keyfile validation
        encrypted_token = encrypt_token(TOKEN, keyfile_path)
        if encrypted_token is None:
            messagebox.showerror("Sign Up Failed", "An error occurred while encrypting token.")
            return

        # Store vault metadata and confirm success
        fill_VAULT_METADATA(True, hashed_mp, encrypted_token)
        messagebox.showinfo("Sign Up Success", "You have successfully signed up!")


# Login Function
def login():
    if not vault_exists():
        messagebox.showerror("Login Failed", "Cannot login. Vault does not exist. Please do the Sign Up first.")
        return

    # Check if lockout timer is still active after too many failed attempts
    last_failed = get_LAST_FAILED()
    if time.time() - last_failed < LOCKOUT_TIME:
        remaining_time = int(LOCKOUT_TIME - (time.time() - last_failed))
        messagebox.showerror("Login Locked", f"Too many failed attempts. Try again after {remaining_time} seconds.")
        return

    failed_count = 0
    master_password = simpledialog.askstring("Login", "Enter Master Password to open your Password Vault:", show='●')

    # Loop to allow retries for incorrect passwords
    while not verify_mp(master_password):
        failed_count += 1
        if failed_count >= MAX_ATTEMPTS:
            update_LAST_FAILED(time.time())
            messagebox.showerror("Login Failed", "Too many failed attempts. Try again after 5 minutes.")
            return
        master_password = simpledialog.askstring("Login", "Wrong Password. Try again:", show='●')

    # Verify keyfile presence and validity
    if not os.path.isfile(keyfile_path) or not verify_keyfile(keyfile_path, TOKEN):
        messagebox.showerror("Login Failed", "Keyfile Verification failed. Invalid login.")
        return

    # Derive encryption key from master password and keyfile
    key = derive_key(master_password, keyfile_path)
    if key is None:
        messagebox.showerror("Login Failed", "Key Derivation failed. Invalid login.")
        return

    # Launch main password vault window after successful login
    from password_operation import create_vault_window
    window.withdraw()
    messagebox.showinfo("Login Success", "You have successfully logged in!")
    create_vault_window(key, window)

    # Securely clear the key from memory
    key = os.urandom(32)
    del key


# Delete Old Vault Function
def delete_old():
    if messagebox.askyesno("Delete Vault", "Are you sure you want to delete the vault?"):
        if not vault_exists():
            messagebox.showerror("Delete Failed", "Vault does not exist, hence cannot be deleted.")
            return
        if not delete_keyfile(keyfile_path):
            messagebox.showerror("Delete Failed", "An error occurred. Vault cannot be deleted.")
            return
        delete_tables()
        messagebox.showinfo("Delete Success", "Vault successfully deleted.")


# Exit Function
def exit():
    if messagebox.askyesno("Exit", "Are you sure you want to exit? Unsaved data will be lost!"):
        clear_clipboard()  # Ensure clipboard is wiped
        window.destroy()  # Properly destroy window

# Create tables in the database if not already present
create_tables()
#Ensure correct database path based on execution type (script or bundled app)
get_db_path()

# Start the GUI Window Setup
window = tk.Tk()
window.title("Secure Password Manager")
window.geometry("400x300")
window.configure(bg="#00BFFF")
window.resizable(False, False)

# Center the window and set up UI
center_window(window)
window.protocol("WM_DELETE_WINDOW", lambda: on_closing(window))
add_logo(window, "#00BFFF")

# Create Main Menu Buttons
frame = tk.Frame(window, bg="#00BFFF")
frame.place(relx=0.5, rely=0.5, anchor="center")
Button(frame, text="Sign Up", command=sign_up, width=150, fg="#001F3F", font=("Tahoma", 12, "bold")).pack(pady=7)
Button(frame, text="Login", command=login, width=150, fg="#001F3F", font=("Tahoma", 12, "bold")).pack(pady=7)
Button(frame, text="Delete Vault", command=delete_old, width=150, fg="#001F3F", font=("Tahoma", 12, "bold")).pack(pady=7)
Button(frame, text="Exit", command=exit, width=150, fg="#001F3F", font=("Tahoma", 12, "bold")).pack(pady=7)

# Start the Tkinter event loop
window.mainloop()
