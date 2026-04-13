#!/usr/bin/env python3
"""Demonstration TCP socket server.

This module starts a TCP server that listens on a specified host and port,
accepts client connections, receives messages, sends responses, and prints
clear demonstration output for screenshots and grading.

Example:
    python socket_server.py --host 127.0.0.1 --port 333
"""

from __future__ import annotations

import argparse
import socket
import sys
from typing import Optional

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 333
BUFFER_SIZE = 1024
BACKLOG = 5
DISCONNECT_MESSAGE = "quit"


def validate_port(port_value: str) -> int:
    """Validate and convert a user-supplied TCP port number.

    Args:
        port_value: Port value supplied by the user.

    Returns:
        The validated port number.

    Raises:
        argparse.ArgumentTypeError: If the value is not a valid TCP port.
    """
    try:
        port = int(port_value)
    except (TypeError, ValueError) as exc:
        raise argparse.ArgumentTypeError("Port must be an integer.") from exc

    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("Port must be between 1 and 65535.")

    return port


def build_response(message: str) -> str:
    """Create a server response for a received client message.

    Args:
        message: Message received from the client.

    Returns:
        A response string to send back to the client.
    """
    if message.strip().lower() == DISCONNECT_MESSAGE:
        return "SERVER: Disconnect request acknowledged. Closing connection."

    return f"SERVER: Message received and processed -> {message}"



def handle_client(client_socket: socket.socket, client_address: tuple[str, int]) -> None:
    """Handle an individual client connection.

    Args:
        client_socket: Connected client socket.
        client_address: Client IP address and source port.
    """
    client_label = f"{client_address[0]}:{client_address[1]}"
    print(f"[SERVER] Client connected from {client_label}.", flush=True)
    print("[SERVER] Waiting for messages from client...", flush=True)

    while True:
        try:
            data = client_socket.recv(BUFFER_SIZE)
        except OSError as exc:
            print(
                f"[SERVER] Error receiving data from {client_label}: {exc}",
                file=sys.stderr,
                flush=True,
            )
            break

        if not data:
            print(
                "[SERVER] Client closed the connection without sending more data.",
                flush=True,
            )
            break

        decoded_message = data.decode("utf-8", errors="replace")
        print(f"[SERVER] Received from client: {decoded_message}", flush=True)
        print("[SERVER] Processing message...", flush=True)

        response = build_response(decoded_message)
        try:
            client_socket.sendall(response.encode("utf-8"))
        except OSError as exc:
            print(
                f"[SERVER] Error sending response to {client_label}: {exc}",
                file=sys.stderr,
                flush=True,
            )
            break

        print(f"[SERVER] Sent response to client: {response}", flush=True)

        if decoded_message.strip().lower() == DISCONNECT_MESSAGE:
            print("[SERVER] Graceful disconnect requested by client.", flush=True)
            break

    print(f"[SERVER] Closing connection to {client_label}.", flush=True)



def run_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> int:
    """Run the TCP socket server.

    Args:
        host: Interface or IP address to bind.
        port: TCP port to listen on.

    Returns:
        Exit status code.
    """
    print("[SERVER] Socket server starting...", flush=True)
    print(f"[SERVER] Binding to {host}:{port}", flush=True)

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((host, port))
            server_socket.listen(BACKLOG)

            print("[SERVER] Server script is now running.", flush=True)
            print(f"[SERVER] Listening for connections on {host}:{port}", flush=True)
            print("[SERVER] Press Ctrl+C to stop the server.", flush=True)

            while True:
                print("[SERVER] Waiting for a client connection...", flush=True)
                try:
                    client_socket, client_address = server_socket.accept()
                except OSError as exc:
                    print(
                        f"[SERVER] Failed to accept connection: {exc}",
                        file=sys.stderr,
                        flush=True,
                    )
                    continue

                with client_socket:
                    handle_client(client_socket, client_address)

    except KeyboardInterrupt:
        print("\n[SERVER] Shutdown requested by user.", flush=True)
        print("[SERVER] Server stopped cleanly.", flush=True)
        return 0
    except OSError as exc:
        print(
            f"[SERVER] Failed to start or run server on {host}:{port}: {exc}",
            file=sys.stderr,
            flush=True,
        )
        return 1

    return 0



def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Optional argument list.

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(description="Run a TCP socket server.")
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help="Host or interface to bind to. Defaults to 127.0.0.1.",
    )
    parser.add_argument(
        "--port",
        type=validate_port,
        default=DEFAULT_PORT,
        help="TCP port to listen on. Defaults to 333.",
    )
    return parser.parse_args(argv)



def main() -> int:
    """Program entry point.

    Returns:
        Exit status code.
    """
    args = parse_args()
    return run_server(host=args.host, port=args.port)


if __name__ == "__main__":
    sys.exit(main())
