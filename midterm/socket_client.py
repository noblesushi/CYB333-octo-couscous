#!/usr/bin/env python3
"""Demonstration TCP socket client.

This module connects to a TCP socket server at a specified host and port,
sends one or more messages, receives responses, and prints clear output for
socket connection demonstrations.

Examples:
    python socket_client.py --host 127.0.0.1 --port 333
    python socket_client.py --host localhost --port 333 --message "Hello"
"""

from __future__ import annotations

import argparse
import ipaddress
import socket
import sys
from typing import Optional

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 333
DEFAULT_TIMEOUT = 3.0
BUFFER_SIZE = 1024
DEFAULT_MESSAGE = "Hello from socket_client"
DISCONNECT_MESSAGE = "quit"



def validate_port(port_value: str) -> int:
    """Validate and convert a user-supplied TCP port number.

    Args:
        port_value: Port value supplied by the user.

    Returns:
        The validated port number.

    Raises:
        argparse.ArgumentTypeError: If the port is invalid.
    """
    try:
        port = int(port_value)
    except (TypeError, ValueError) as exc:
        raise argparse.ArgumentTypeError("Port must be an integer.") from exc

    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("Port must be between 1 and 65535.")

    return port



def validate_host(host_value: str) -> str:
    """Validate a user-supplied host value.

    Accepts localhost, IPv4, or IPv6 addresses.

    Args:
        host_value: Host value supplied by the user.

    Returns:
        The validated host string.

    Raises:
        argparse.ArgumentTypeError: If the host is not accepted.
    """
    if host_value == "localhost":
        return host_value

    try:
        ipaddress.ip_address(host_value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "Host must be 'localhost' or a valid IP address."
        ) from exc

    return host_value



def validate_timeout(timeout_value: str) -> float:
    """Validate and convert a timeout value.

    Args:
        timeout_value: Timeout value supplied by the user.

    Returns:
        The validated timeout.

    Raises:
        argparse.ArgumentTypeError: If the timeout is invalid.
    """
    try:
        timeout = float(timeout_value)
    except (TypeError, ValueError) as exc:
        raise argparse.ArgumentTypeError("Timeout must be a number.") from exc

    if timeout <= 0:
        raise argparse.ArgumentTypeError("Timeout must be greater than zero.")

    return timeout



def send_and_receive(client_socket: socket.socket, message: str) -> bool:
    """Send a message to the server and read the response.

    Args:
        client_socket: Connected client socket.
        message: Message to send.

    Returns:
        True if the exchange succeeded, else False.
    """
    try:
        print(f"[CLIENT] Sending message to server: {message}", flush=True)
        client_socket.sendall(message.encode("utf-8"))
    except OSError as exc:
        print(f"[CLIENT] Failed to send message: {exc}", file=sys.stderr, flush=True)
        return False

    try:
        response = client_socket.recv(BUFFER_SIZE)
    except OSError as exc:
        print(
            f"[CLIENT] Failed to receive response from server: {exc}",
            file=sys.stderr,
            flush=True,
        )
        return False

    if not response:
        print("[CLIENT] Server closed the connection unexpectedly.", flush=True)
        return False

    decoded_response = response.decode("utf-8", errors="replace")
    print(f"[CLIENT] Response received from server: {decoded_response}", flush=True)
    return True



def connect_to_server(
    host: str,
    port: int,
    message: str = DEFAULT_MESSAGE,
    timeout: float = DEFAULT_TIMEOUT,
    disconnect_message: str = DISCONNECT_MESSAGE,
) -> int:
    """Connect to a TCP server, exchange messages, and disconnect cleanly.

    Args:
        host: Target hostname or IP address.
        port: Target TCP port.
        message: Primary message to send to the server.
        timeout: Socket timeout in seconds.
        disconnect_message: Message used to request graceful disconnection.

    Returns:
        Exit status code. Zero indicates success.
    """
    print("[CLIENT] Socket client starting...", flush=True)
    print(f"[CLIENT] Target server: {host}:{port}", flush=True)
    print(f"[CLIENT] Attempting connection with timeout={timeout} seconds.", flush=True)

    try:
        with socket.create_connection((host, port), timeout=timeout) as client_socket:
            print("[CLIENT] Connection established successfully.", flush=True)
            print("[CLIENT] Beginning message exchange demonstration.", flush=True)

            if not send_and_receive(client_socket, message):
                return 1

            print("[CLIENT] Demonstrating graceful disconnect...", flush=True)
            if not send_and_receive(client_socket, disconnect_message):
                return 1

            print("[CLIENT] Clean disconnection process complete.", flush=True)
            print("[CLIENT] Client socket closing normally.", flush=True)
            return 0
    except socket.timeout:
        print(
            f"[CLIENT] ERROR: Connection to {host}:{port} timed out after {timeout} seconds.",
            file=sys.stderr,
            flush=True,
        )
    except ConnectionRefusedError:
        print(
            f"[CLIENT] ERROR: Connection refused by {host}:{port}. Server may not be running.",
            file=sys.stderr,
            flush=True,
        )
    except OSError as exc:
        print(
            f"[CLIENT] ERROR: Failed to connect to {host}:{port}: {exc}",
            file=sys.stderr,
            flush=True,
        )

    return 1



def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Optional argument list.

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(description="Run a TCP socket client.")
    parser.add_argument(
        "--host",
        type=validate_host,
        default=DEFAULT_HOST,
        help="Target host. Must be localhost or a valid IP address.",
    )
    parser.add_argument(
        "--port",
        type=validate_port,
        default=DEFAULT_PORT,
        help="Target TCP port. Defaults to 333.",
    )
    parser.add_argument(
        "--message",
        default=DEFAULT_MESSAGE,
        help="Message to send after connecting.",
    )
    parser.add_argument(
        "--timeout",
        type=validate_timeout,
        default=DEFAULT_TIMEOUT,
        help="Socket timeout in seconds. Defaults to 3.0.",
    )
    return parser.parse_args(argv)



def main() -> int:
    """Program entry point.

    Returns:
        Exit status code.
    """
    args = parse_args()
    return connect_to_server(
        host=args.host,
        port=args.port,
        message=args.message,
        timeout=args.timeout,
    )


if __name__ == "__main__":
    sys.exit(main())
