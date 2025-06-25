# 🔐 Secure Password Manager

A lightweight, secure, and user-friendly password manager built with Python. This application provides a classic GUI interface for storing, retrieving, and managing your passwords within an **encrypted local vault** — ensuring your credentials are safe, even if the vault is compromised.

---

## 🚀 Features

- **🔑 Two-Fold Security**
  - Decryption requires both **Master Password** and locally stored **Keyfile**, reducing exposure to offline attacks.

- **🖥️ User-Friendly Interface**
  - Built using **Tkinter** for a simple, responsive, and secure desktop experience.

- **🔒 AES Encryption**
  - All stored passwords are encrypted using the **Cryptography** library with AES standards.

- **⚙️ Random Password Generator**
  - Generate strong, random passwords for websites automatically.

- **📋 Clipboard Management**
  - Retrieved passwords are copied to the clipboard and automatically cleared after a short delay.

- **⏱️ Auto Logout on Inactivity**
  - Users are logged out automatically after a period of inactivity in the vault window.

- **🚫 Login Lockout**
  - After 5 failed login attempts, the app locks for 5 minutes to prevent brute-force attacks.

---

## 🛠️ Technologies Used

### 🧑‍💻 Programming Language:
- **Python**

### 📚 Libraries & Frameworks:
- **Tkinter** – GUI development
- **Argon2** – Secure hashing of Master Passwords
- **Cryptography** – AES encryption/decryption
- **Tkmacosx** – Enhanced macOS-compatible buttons
- **Pillow (PIL)** – Displaying images/logos in the GUI
- **Pyperclip** – Secure clipboard operations

### 🗃️ Database:
- **SQLite** – Local encrypted storage of password entries

### 📦 Packaging:
- **Platypus (macOS)** – Converts Python script into a standalone macOS app

---







