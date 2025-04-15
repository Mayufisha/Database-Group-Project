import tkinter as tk
from tkinter import messagebox
import subprocess

# Setup main window
root = tk.Tk()
root.title("Login Form")
root.geometry("1080x720")
root.configure(bg='#333333')

# Create frame
frame = tk.Frame(bg='#333333')

# Creating widgets
login_label = tk.Label(frame, text="Login", bg='#333333', fg="#ebde34", font=("Arial", 30))
username_label = tk.Label(frame, text="Username", bg='#333333', fg="#FFFFFF", font=("Arial", 16))
username_entry = tk.Entry(frame, font=("Arial", 16))
password_label = tk.Label(frame, text="Password", bg='#333333', fg="#FFFFFF", font=("Arial", 16))
password_entry = tk.Entry(frame, show="*", font=("Arial", 16))
login_button = tk.Button(frame, text="Login", bg="#ebde34", fg="#333", font=("Arial", 16), command=login)
