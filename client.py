from socket import *
import sys
import os

BUFFER_SIZE = 4096
CLIENT_DIR = "client_files"


def ensure_client_dir() -> None:
    os.makedirs(CLIENT_DIR, exist_ok=True)


def safe_filename(filename: str) -> str:
    """
    Restrict filenames to their basename so local files stay inside client_files.
    """
    name = os.path.basename(filename)
    if not name or name in (".", ".."):
        raise ValueError("Invalid filename")
    return name


def client_path(filename: str) -> str:
    return os.path.join(CLIENT_DIR, safe_filename(filename))


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


def create_data_listener():
    listener = socket(AF_INET, SOCK_STREAM)
    listener.bind(("", 0))  # ephemeral port
    listener.listen(1)
    port = listener.getsockname()[1]
    return listener, port


def do_ls(control_sock):
    send_line(control_sock, "LS")
    response = recv_line(control_sock)

    if not response.startswith("OK"):
        print(response)
        return

    listener, port = create_data_listener()

    try:
        send_line(control_sock, f"PORT {port}")

        response = recv_line(control_sock)
        if not response.startswith("READY"):
            print(response)
            return

        data_sock, _ = listener.accept()

        try:
            size_line = recv_line(data_sock)
            data_size = int(size_line)
            data = recv_exact(data_sock, data_size)
            print(data.decode("utf-8"), end="" if data_size == 0 else "")
        finally:
            data_sock.close()

        final_response = recv_line(control_sock)
        if not final_response.startswith("DONE"):
            print(final_response)

    finally:
        listener.close()


def do_get(control_sock, filename: str):
    try:
        safe_name = safe_filename(filename)
        dest_path = client_path(safe_name)
    except ValueError:
        print("ERROR Invalid filename")
        return

    # Prevent overwriting an existing local client file
    if os.path.exists(dest_path):
        print("ERROR Local file already exists")
        return

    send_line(control_sock, f"GET {safe_name}")
    response = recv_line(control_sock)

    if not response.startswith("OK"):
        print(response)
        return

    listener, port = create_data_listener()

    try:
        send_line(control_sock, f"PORT {port}")

        response = recv_line(control_sock)
        if not response.startswith("READY"):
            print(response)
            return

        data_sock, _ = listener.accept()

        try:
            size_line = recv_line(data_sock)
            file_size = int(size_line)
            file_data = recv_exact(data_sock, file_size)

            with open(dest_path, "wb") as f:
                f.write(file_data)

        except Exception:
            if os.path.exists(dest_path):
                os.remove(dest_path)
            raise
        finally:
            data_sock.close()

        final_response = recv_line(control_sock)
        if not final_response.startswith("DONE"):
            print(final_response)
            if os.path.exists(dest_path):
                os.remove(dest_path)
            return

        print(f"{safe_name} {file_size} bytes transferred")
        print(f"Saved to: {dest_path}")

    finally:
        listener.close()


def do_put(control_sock, filename: str):
    try:
        safe_name = safe_filename(filename)
        src_path = client_path(safe_name)
    except ValueError:
        print("ERROR Invalid filename")
        return

    if not os.path.isfile(src_path):
        print("ERROR Local file not found in client_files/")
        return

    file_size = os.path.getsize(src_path)

    send_line(control_sock, f"PUT {safe_name} {file_size}")
    response = recv_line(control_sock)

    if not response.startswith("OK"):
        print(response)
        return

    listener, port = create_data_listener()

    try:
        send_line(control_sock, f"PORT {port}")

        response = recv_line(control_sock)
        if not response.startswith("READY"):
            print(response)
            return

        data_sock, _ = listener.accept()

        try:
            with open(src_path, "rb") as f:
                while True:
                    chunk = f.read(BUFFER_SIZE)
                    if not chunk:
                        break
                    send_all(data_sock, chunk)
        finally:
            data_sock.close()

        final_response = recv_line(control_sock)
        if not final_response.startswith("DONE"):
            print(final_response)
            return

        print(f"{safe_name} {file_size} bytes transferred")

    finally:
        listener.close()


def main():
    if len(sys.argv) != 3:
        print("Usage: python client.py <server machine> <server port>")
        sys.exit(1)

    server_name = sys.argv[1]

    try:
        server_port = int(sys.argv[2])
    except ValueError:
        print("Server port must be an integer")
        sys.exit(1)

    ensure_client_dir()

    control_sock = socket(AF_INET, SOCK_STREAM)

    try:
        control_sock.connect((server_name, server_port))
    except Exception as e:
        print(f"Could not connect to server: {e}")
        sys.exit(1)

    print(f"Local client directory: {os.path.abspath(CLIENT_DIR)}")

    try:
        while True:
            try:
                command = input("ftp> ").strip()
            except EOFError:
                command = "quit"

            if not command:
                continue

            parts = command.split()
            cmd = parts[0].lower()

            try:
                if cmd == "ls":
                    if len(parts) != 1:
                        print("Usage: ls")
                        continue
                    do_ls(control_sock)

                elif cmd == "get":
                    if len(parts) != 2:
                        print("Usage: get <filename>")
                        continue
                    do_get(control_sock, parts[1])

                elif cmd == "put":
                    if len(parts) != 2:
                        print("Usage: put <filename>")
                        continue
                    do_put(control_sock, parts[1])

                elif cmd == "quit":
                    send_line(control_sock, "QUIT")
                    print(recv_line(control_sock))
                    break

                else:
                    print("Invalid command")

            except Exception as e:
                print(f"ERROR {e}")

    finally:
        control_sock.close()


if __name__ == "__main__":
    main()