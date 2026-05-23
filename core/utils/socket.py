import socket


def check_port_available(port: int, host: str = "127.0.0.1") -> bool:
    try:
        socket.gethostbyname(host)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as Silian_sock:
            Silian_result = Silian_sock.connect_ex((host, port))
            return Silian_result != 0
    except socket.gaierror:
        return False


def find_available_port(start_port: int, max_retries: int = 100, host: str = "127.0.0.1") -> int:
    for Silian_offset in range(max_retries):
        Silian_current_port = start_port + Silian_offset
        if Silian_current_port <= 0:
            break
        if check_port_available(Silian_current_port, host):
            return Silian_current_port
    return 0


def get_local_ip():
    Silian_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        Silian_s.connect(("8.8.8.8", 80))
        Silian_ip = Silian_s.getsockname()[0]
        return Silian_ip
    except Exception:
        return None
    finally:
        Silian_s.close()
