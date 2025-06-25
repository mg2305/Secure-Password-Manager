from tkinter import messagebox
from PIL import Image, ImageTk

import tkinter as tk
import os
import pyperclip
import termios
import sys

# Function to display password and copy it to clipboard
def display_password(password, website):
    """
    Displays the retrieved password (masked) in a message box 
    and copies the actual password to the clipboard.
    """
    masked_password = '*' * len(password)  
    pyperclip.copy(password)  
    messagebox.showinfo("Retrieved Password", f"Password for {website}: {masked_password}\nPassword copied to clipboard!")

# Function to clear clipboard content
def clear_clipboard():
    """Clears any content from the clipboard to prevent password leakage."""
    pyperclip.copy("")

# Function to center the window on the screen
def center_window(window, width=400, height=300):
    """
    Centers the window on the screen based on given width and height.
    Default size is 400x300.
    """
    screen_width = window.winfo_screenwidth()  
    screen_height = window.winfo_screenheight()  
    x = (screen_width - width) // 2 
    y = (screen_height - height) // 2  
    window.geometry(f"{width}x{height}+{x}+{y}")  

# Function to add a logo image to the window 
def add_logo(window, _bg):
    """
    Loads and displays a logo image in the top-right corner of the window.
    Supports both normal and bundled (PyInstaller) app runs.
    """
    # Check if running as a bundled app (e.g., using PyInstaller)
    if getattr(sys, 'frozen', False):
        # When bundled, look for the logo in the "Resources" folder created by PyInstaller
        logo_path = os.path.join(sys._MEIPASS, "logo.png")
    else:
        # When running the script directly, look for the logo in the same folder as the script
        logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
    
    # Load and resize the logo image
    logo_img = Image.open(logo_path)
    logo_resized = logo_img.resize((125, 125))  
    logo_tk = ImageTk.PhotoImage(logo_resized)

    # Create a label to display the logo, positioned in the top-right corner
    logo_label = tk.Label(window, image=logo_tk, bg=_bg, borderwidth=0)
    logo_label.place(relx=1.0, y=0, anchor="ne")

    # Keep a reference to the image to prevent garbage collection from clearing it
    window.logo_ref = logo_tk
