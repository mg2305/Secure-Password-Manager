from tkinter import messagebox
import sqlite3
import time
import sys

# Define global database name
global DB_NAME 
DB_NAME = 'gui_spm.db'

# === Ensure correct database path based on execution type (script or bundled app) ===
def get_db_path():
    if getattr(sys, 'frozen', False):
        global DB_NAME
        # If running as a bundled Platypus app
        base_path = os.path.abspath(os.path.dirname(sys.executable))
        DB_NAME = os.path.join(base_path, "../Resources", "gui_spm.db")
    else:
        # Running as a regular script
        DB_NAME = "gui_spm.db"


# === Vault Metadata Operations ===

# Check if the vault already exists
def get_VAULT_EXISTS():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''SELECT * FROM VAULT_METADATA ORDER BY ROWID ASC LIMIT 1''')
    result = cursor.fetchone()
    conn.close()
    return result[0]

# Get the hashed master password from the metadata table
def get_MP_HASH():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''SELECT * FROM VAULT_METADATA ORDER BY ROWID ASC LIMIT 1''')
    result = cursor.fetchone()
    conn.close()
    return result[1]

# Get the encrypted token from the metadata table
def get_ENC_TOKEN():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''SELECT * FROM VAULT_METADATA ORDER BY ROWID ASC LIMIT 1''')
    result = cursor.fetchone()
    conn.close()
    return result[2]

# Initialize the VAULT_METADATA table after successful sign-up
def fill_VAULT_METADATA(vault_exists, mp_hash, enc_token):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''DELETE FROM VAULT_METADATA''')  # Clear old metadata
    cursor.execute('''INSERT INTO VAULT_METADATA (VAULT_EXISTS, MP_HASH, ENC_TOKEN) VALUES(?, ?, ?)''', 
                   (vault_exists, mp_hash, enc_token))
    conn.commit()
    conn.close()


# === Table Creation and Deletion Operations ===

# Create the PASSWORDS, VAULT_METADATA, and T_LAST_FAILED tables if they don't exist
def create_tables():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Create the table for storing website passwords
    table1 = '''CREATE TABLE PASSWORDS (
            Website TEXT NOT NULL,
            UserName TEXT,
            Password BLOB NOT NULL
            ); '''
    cursor.execute(f"PRAGMA table_info({'PASSWORDS'})")
    if cursor.fetchone() is None:
        cursor.execute(table1)

    # Create the vault metadata table
    table2 = '''CREATE TABLE VAULT_METADATA (
            VAULT_EXISTS INTEGER NOT NULL,
            MP_HASH TEXT,
            ENC_TOKEN BLOB
            );'''
    cursor.execute(f"PRAGMA table_info({'VAULT_METADATA'})")
    if cursor.fetchone() is None:
        cursor.execute(table2)
        cursor.execute(''' INSERT INTO VAULT_METADATA VALUES (0, NULL, NULL)''')

    # Create the table to track last failed login attempt
    table3 = '''CREATE TABLE T_LAST_FAILED (
            LAST_FAILED REAL 
            );'''
    cursor.execute(f"PRAGMA table_info({'T_LAST_FAILED'})")
    if cursor.fetchone() is None:
        cursor.execute(table3)
        cursor.execute(''' INSERT INTO T_LAST_FAILED (LAST_FAILED) VALUES(?)''', (time.time() - 300,))

    conn.commit()
    conn.close()


# Delete all data from tables (reset vault)
def delete_tables():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''DELETE FROM PASSWORDS''')
    cursor.execute('''DELETE FROM VAULT_METADATA''')
    cursor.execute('''DELETE FROM T_LAST_FAILED''')

    # Reset metadata and failed login timer
    cursor.execute(''' INSERT INTO VAULT_METADATA VALUES (0, NULL, NULL)''')
    cursor.execute(''' INSERT INTO T_LAST_FAILED (LAST_FAILED) VALUES(?)''', (time.time() - 300,))

    conn.commit()
    conn.close()


# === Password Management Operations ===

# Check if a password for a specific website already exists
def websitePassword_exists(website):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''SELECT 1 FROM PASSWORDS WHERE Website = ? LIMIT 1''', (website,))
    result = cursor.fetchone()
    conn.close()
    return result is not None


# Delete a password entry for a website
def delete_passwordEntry(website):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if not websitePassword_exists(website):
        messagebox.showerror("Error", "Cannot delete Website's password because it doesn't exist.")
        return
    cursor.execute('''DELETE FROM PASSWORDS WHERE Website = ?''', (website,))
    messagebox.showinfo("Success", "Website's Password successfully deleted.")
    conn.commit()
    conn.close()


# Insert a new website password entry
def insert_password(website, username, password, choice):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if websitePassword_exists(website):
        messagebox.showerror("Error", "Cannot insert Website's password because it already exists. Delete the old one to insert new.")
        return
    cursor.execute('''INSERT INTO PASSWORDS VALUES (?, ?, ?)''', (website, username, password))
    messagebox.showinfo("Success", "Password saved successfully!" if choice == 'c' else "Password generated and saved successfully!")
    conn.commit()
    conn.close()


# Retrieve a website's password
def get_password(website):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if not websitePassword_exists(website):
        messagebox.showerror("Error", "Cannot retrieve Website's password because it doesn't exist.")
        return None
    cursor.execute('''SELECT * FROM PASSWORDS WHERE Website = ?''', (website,))
    result = cursor.fetchone()
    conn.close()
    messagebox.showinfo("Username", f"Username for {website}: {result[1]}")
    return result[2]

# List all websites saved in the vault
def get_all_websites():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''SELECT * FROM PASSWORDS''')
    result = cursor.fetchall()
    conn.close()
    return [row[0] for row in result]


# === Failed Login Tracking Operations ===

# Get the last failed login time
def get_LAST_FAILED():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''SELECT * FROM T_LAST_FAILED''')
    result = cursor.fetchone()
    conn.close()
    return result[0]


# Update the last failed login time
def update_LAST_FAILED(newTime):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''DELETE FROM T_LAST_FAILED''')
    cursor.execute('''INSERT INTO T_LAST_FAILED VALUES (?)''', (newTime,))
    conn.commit()
    conn.close()




