from socket import *
import sys
import os


BUFFER_SIZE = 4096


def send_all(sock, data: bytes) -> None:
    total_sent = 0
    while total_sent < len(data):
        sent = sock.send(data[total_sent:])
        if sent == 0:
            raise RuntimeError("Socket connection broken during send")
        total_sent += sent


def recv_exact(sock, n: int) -> bytes:
    chunks = []
    bytes_received = 0

    while bytes_received < n:
        chunk = sock.recv(min(BUFFER_SIZE, n - bytes_received))
        if not chunk:
            raise RuntimeError("Socket connection broken during recv")
        chunks.append(chunk)
        bytes_received += len(chunk)

    return b"".join(chunks)


def send_line(sock, text: str) -> None:
    send_all(sock, (text + "\n").encode("utf-8"))


def recv_line(sock) -> str:
    data = bytearray()

    while True:
        ch = sock.recv(1)
        if not ch:
            raise RuntimeError("Socket closed while reading line")
        if ch == b"\n":
            break
        data.extend(ch)

    return data.decode("utf-8").strip()


def get_directory_listing() -> bytes:
    files = os.listdir(".")
    files.sort()
    listing = "\n".join(files)
    if listing:
        listing += "\n"
    return listing.encode("utf-8")


def connect_data_socket(client_ip: str, port: int):
    data_sock = socket(AF_INET, SOCK_STREAM)
    data_sock.connect((client_ip, port))
    return data_sock


def handle_ls(control_sock, client_ip: str, data_port: int) -> None:
    data = get_directory_listing()
    data_sock = connect_data_socket(client_ip, data_port)

    try:
        send_line(control_sock, "READY")
        send_line(data_sock, str(len(data)))
        send_all(data_sock, data)
    finally:
        data_sock.close()

    print("SUCCESS: ls")
    send_line(control_sock, "DONE")


def handle_get(control_sock, client_ip: str, data_port: int, filename: str) -> None:
    file_size = os.path.getsize(filename)
    data_sock = connect_data_socket(client_ip, data_port)

    try:
        send_line(control_sock, "READY")
        send_line(data_sock, str(file_size))

        with open(filename, "rb") as f:
            while True:
                chunk = f.read(BUFFER_SIZE)
                if not chunk:
                    break
                send_all(data_sock, chunk)
    finally:
        data_sock.close()

    print(f"SUCCESS: get {filename}")
    send_line(control_sock, "DONE")


def handle_put(control_sock, client_ip: str, data_port: int, filename: str, file_size: int) -> None:
    data_sock = connect_data_socket(client_ip, data_port)

    try:
        send_line(control_sock, "READY")

        with open(filename, "wb") as f:
            remaining = file_size
            while remaining > 0:
                chunk = data_sock.recv(min(BUFFER_SIZE, remaining))
                if not chunk:
                    raise RuntimeError("Client disconnected during file upload")
                f.write(chunk)
                remaining -= len(chunk)
    finally:
        data_sock.close()

    print(f"SUCCESS: put {filename}")
    send_line(control_sock, "DONE")


def handle_client(control_sock, client_addr) -> None:
    client_ip = client_addr[0]
    pending_command = None

    print(f"Client connected from {client_addr}")

    try:
        while True:
            line = recv_line(control_sock)
            if not line:
                continue

            parts = line.split()
            command = parts[0].upper()

            if command == "LS":
                pending_command = ("LS",)
                send_line(control_sock, "OK")

            elif command == "GET":
                if len(parts) != 2:
                    send_line(control_sock, "ERROR Usage: GET <filename>")
                    continue

                filename = parts[1]

                if not os.path.isfile(filename):
                    print(f"FAILURE: get {filename} (file not found)")
                    send_line(control_sock, "ERROR File not found")
                    continue

                pending_command = ("GET", filename)
                send_line(control_sock, "OK")

            elif command == "PUT":
                if len(parts) != 3:
                    send_line(control_sock, "ERROR Usage: PUT <filename> <filesize>")
                    continue

                filename = parts[1]
                try:
                    file_size = int(parts[2])
                    if file_size < 0:
                        raise ValueError
                except ValueError:
                    send_line(control_sock, "ERROR Invalid file size")
                    continue

                pending_command = ("PUT", filename, file_size)
                send_line(control_sock, "OK")

            elif command == "PORT":
                if pending_command is None:
                    send_line(control_sock, "ERROR No pending command")
                    continue

                if len(parts) != 2:
                    send_line(control_sock, "ERROR Usage: PORT <portnumber>")
                    continue

                try:
                    data_port = int(parts[1])
                    if not (0 <= data_port <= 65535):
                        raise ValueError
                except ValueError:
                    send_line(control_sock, "ERROR Invalid port number")
                    continue

                try:
                    if pending_command[0] == "LS":
                        handle_ls(control_sock, client_ip, data_port)

                    elif pending_command[0] == "GET":
                        filename = pending_command[1]
                        handle_get(control_sock, client_ip, data_port, filename)

                    elif pending_command[0] == "PUT":
                        filename = pending_command[1]
                        file_size = pending_command[2]
                        handle_put(control_sock, client_ip, data_port, filename, file_size)

                except Exception as e:
                    print(f"FAILURE: {pending_command} ({e})")
                    send_line(control_sock, f"ERROR Transfer failed: {e}")

                pending_command = None

            elif command == "QUIT":
                send_line(control_sock, "OK")
                print("Client disconnected")
                break

            else:
                send_line(control_sock, "ERROR Invalid command")

    except Exception as e:
        print(f"Connection error with {client_addr}: {e}")

    finally:
        control_sock.close()


def main():
    if len(sys.argv) != 2:
        print("Usage: python serv.py <PORTNUMBER>")
        sys.exit(1)

    try:
        server_port = int(sys.argv[1])
    except ValueError:
        print("Port number must be an integer")
        sys.exit(1)

    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.bind(("", server_port))
    server_socket.listen(1)

    print(f"FTP server listening on port {server_port}")

    try:
        while True:
            control_sock, client_addr = server_socket.accept()
            handle_client(control_sock, client_addr)
    except KeyboardInterrupt:
        print("\nServer shutting down...")
    finally:
        server_socket.close()


if __name__ == "__main__":
    main()