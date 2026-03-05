import socket
import sqlite3
import json
import threading

def init_db():
    conn = sqlite3.connect('cinema.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS movies (
        movie_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        cinema_room INTEGER,
        release_date TEXT,
        end_date TEXT,
        tickets_available INTEGER,
        ticket_price REAL
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS sales (
        movie_id INTEGER PRIMARY KEY AUTOINCREMENT,
        movie_id INTEGER,
        customer_name TEXT,
        number_of_tickets INTEGER,
        total REAL,
        FOREIGN KEY(movie_id) REFERENCES movies(movie_id)
    )''')

    # Insert 7 movies only if movies table is empty
    c.execute("SELECT COUNT(*) FROM movies")
    if c.fetchone()[0] == 0:
        movies = [
            ('The Passion of Christ', 1, '2024-01-01', '2024-02-01', 100, 50.0),
            ('The Second Coming of The Messiah', 2, '2024-01-05', '2024-02-10', 120, 60.0),
            ('Inception: Dream Again', 3, '2024-01-10', '2024-02-15', 80, 70.0),
            ('Toy Story 5', 4, '2024-01-15', '2024-02-20', 90, 55.0),
            ('Fast & Curious', 5, '2024-01-20', '2024-02-25', 110, 65.0),
            ('The Joker Returns', 6, '2024-01-25', '2024-03-01', 95, 45.0),
            ('Encanto 2', 7, '2024-01-30', '2024-03-05', 105, 75.0),
        ]
        c.executemany("INSERT INTO movies (title, cinema_room, release_date, end_date, tickets_available, ticket_price) VALUES (?, ?, ?, ?, ?, ?)", movies)

    conn.commit()
    conn.close()

def handle_client(client_socket):
    conn = sqlite3.connect('cinema.db')
    c = conn.cursor()

    try:
        while True:
            data = client_socket.recv(4096)
            if not data:
                break
            request = json.loads(data.decode())
            command = request.get("command")
            payload = request.get("data", {})

            if command == "get_movies":
                c.execute("SELECT * FROM movies")
                rows = c.fetchall()
                columns = [desc[0] for desc in c.description]
                movies = []
                for row in rows:
                    movie = dict(zip(columns, row))
                    movies.append(movie)
                client_socket.sendall(json.dumps({"status": "success", "data": movies}).encode())

            elif command == "record_sale":
                movie_id = payload["movie_id"]
                customer = payload["customer_name"]
                tickets = payload["number_of_tickets"]

                c.execute("SELECT tickets_available, ticket_price FROM movies WHERE movie_id=?", (movie_id,))
                result = c.fetchone()
                if result and result[0] >= tickets:
                    total = result[1] * tickets
                    c.execute("INSERT INTO sales (movie_id, customer_name, number_of_tickets, total) VALUES (?, ?, ?, ?)",
                              (movie_id, customer, tickets, total))
                    c.execute("UPDATE movies SET tickets_available = tickets_available - ? WHERE movie_id = ?", (tickets, movie_id))
                    conn.commit()
                    client_socket.sendall(json.dumps({"status": "success", "total": total}).encode())
                else:
                    client_socket.sendall(json.dumps({"status": "error", "message": "Not enough tickets"}).encode())

            else:
                client_socket.sendall(json.dumps({"status": "error", "message": "Invalid command"}).encode())
    except Exception as e:
        client_socket.sendall(json.dumps({"status": "error", "message": str(e)}).encode())
    finally:
        client_socket.close()
        conn.close()

if __name__ == "__main__":
    init_db()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('127.0.0.1', 9000))
    server.listen(5)
    print("Server listening on port 9000...")

    while True:
        client_socket, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(client_socket,))
        thread.daemon = True
        thread.start()