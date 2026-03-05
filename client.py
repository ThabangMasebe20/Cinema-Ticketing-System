import socket
import json
import tkinter as tk
from tkinter import messagebox

def send_request(command, data=None):
    try:
        with socket.socket() as s:
            s.connect(('127.0.0.1', 9000))
            request = {"command": command}
            if data:
                request["data"] = data
            s.sendall(json.dumps(request).encode())
            response = json.loads(s.recv(4096).decode())
            return response
    except Exception as e:
        return {"status": "error", "message": str(e)}

def send_request(command, data=None):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('127.0.0.1', 9000))
            request = {"command": command}
            if data:
                request["data"] = data
            s.sendall(json.dumps(request).encode())
            response = json.loads(s.recv(4096).decode())
            return response
    except Exception as e:
        return {"status": "error", "message": str(e)}

def load_movies():
    res = send_request("get_movies")
    if res["status"] == "success":
        movie_list.delete(0, tk.END)
        global movies
        movies = res["data"]
        for m in movies:
            movie_list.insert(tk.END, f"{m['movie_id']} - {m['title']} (Tickets: {m['tickets_available']})")
    else:
        messagebox.showerror("Error", res["message"])

def buy_tickets():
    try:
        selection = movie_list.curselection()
        if not selection:
            messagebox.showwarning("Select", "Select a movie first.")
            return
        
        index = selection[0]
        movie = movies[index]
        movie_id = movie["movie_id"]
        customer_name = name_entry.get()
        tickets = int(ticket_entry.get())

        if not customer_name:
            messagebox.showwarning("Name", "Enter customer name.")
            return

        data = {
            "movie_id": movie_id,
            "customer_name": customer_name,
            "number_of_tickets": tickets
        }
        res = send_request("record_sale", data)
        if res["status"] == "success":
            total = res["total"]
            messagebox.showinfo("Success", f"Sale complete. Total: R{total:.2f}")
            with open("receipt.txt", "w") as f:
                f.write(f"Movie ID: {movie_id}\nCustomer: {customer_name}\nTickets: {tickets}\nTotal: R{total:.2f}")
            load_movies()
        else:
            messagebox.showerror("Error", res["message"])
    except ValueError:
        messagebox.showerror("Invalid", "Please enter a valid number of tickets.")

# UI
root = tk.Tk()
root.title("NewLine Cinema Client")

tk.Label(root, text="Customer Name:").pack()
name_entry = tk.Entry(root)
name_entry.pack()

tk.Label(root, text="Number of Tickets:").pack()
ticket_entry = tk.Entry(root)
ticket_entry.pack()

tk.Button(root, text="Buy Tickets", command=buy_tickets).pack(pady=5)

movie_list = tk.Listbox(root, width=50)
movie_list.pack(pady=10)

tk.Button(root, text="Refresh Movies", command=load_movies).pack(pady=5)

load_movies()
root.mainloop()