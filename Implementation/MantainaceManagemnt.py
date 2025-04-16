import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector

def connect_db():
    return mysql.connector.connect(
        host="ls-d3311d7ae41e61c25d492ef874e447d39eb24c2b.cz88m42um6aw.ca-central-1.rds.amazonaws.com",
        user="dbmasteruser",
        password="M(;+O4+>L{PM~c;tCmd)XEt]9?y9sAe{",
        database="corporate"
    )
