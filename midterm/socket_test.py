#!/usr/bin/env python3
"""Demonstration test harness for the socket server and client.

This script starts the server in a background process, runs the required test
cases, and prints demonstration-friendly output for screenshots.

Test cases:
    1. Successful connection and message exchange.
    2. Server receiving messages from client.
    3. Client receiving responses from server.
    4. Error handling when server is not running.
    5. Bad connection to localhost on port 35999.
    6. Bad connection to Martian IP on port 333.
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path
from typing import Sequence

SERVER_PORT = 333
TEST_TIMEOUT_SECONDS = 8
SERVER_STARTUP_DELAY_SECONDS = 1.0
SCRIPT_DIRECTORY = Path(__file__).resolve().parent
SERVER_SCRIPT = SCRIPT_DIRECTORY / "socket_server.py"
CLIENT_SCRIPT = SCRIPT_DIRECTORY / "socket_client.py"



def run_command(command: Sequence[str], label: str) -> subprocess.CompletedProcess[str] | None:
    """Run a subprocess command and print its output.

    Args:
        command: Command to execute.
        label: Label used in demonstration output.

    Returns:
        CompletedProcess on success, else None.
    """
    print(f"\n[TEST] {label}", flush=True)
    print(f"[TEST] Command: {' '.join(command)}", flush=True)

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=TEST_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        print(f"[TEST] ERROR: Command timed out: {exc}", file=sys.stderr, flush=True)
        return None
    except OSError as exc:
        print(f"[TEST] ERROR: Failed to execute command: {exc}", file=sys.stderr, flush=True)
        return None

    if result.stdout:
        print("[TEST] STDOUT:", flush=True)
        print(result.stdout.rstrip(), flush=True)

    if result.stderr:
        print("[TEST] STDERR:", flush=True)
        print(result.stderr.rstrip(), flush=True)

    print(f"[TEST] Return code: {result.returncode}", flush=True)
    return result



def start_server() -> subprocess.Popen[str] | None:
    """Start the socket server in the background.

    Returns:
        Popen process for the server, or None if startup failed.
    """
    server_command = [sys.executable, str(SERVER_SCRIPT), "--port", str(SERVER_PORT)]
    print("[TEST] Starting server for demonstration...", flush=True)
    print(f"[TEST] Command: {' '.join(server_command)}", flush=True)

    try:
        server_process = subprocess.Popen(
            server_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except OSError as exc:
        print(f"[TEST] ERROR: Failed to start server: {exc}", file=sys.stderr, flush=True)
        return None

    time.sleep(SERVER_STARTUP_DELAY_SECONDS)

    if server_process.poll() is not None:
        try:
            stdout_output, stderr_output = server_process.communicate(timeout=2)
        except (subprocess.TimeoutExpired, OSError):
            stdout_output, stderr_output = "", ""

        print("[TEST] ERROR: Server exited unexpectedly during startup.", file=sys.stderr, flush=True)
        if stdout_output:
            print(stdout_output.rstrip(), flush=True)
        if stderr_output:
            print(stderr_output.rstrip(), file=sys.stderr, flush=True)
        return None

    print("[TEST] Server is running and should be listening for connections.", flush=True)
    return server_process



def stop_server(server_process: subprocess.Popen[str]) -> None:
    """Stop the background server process and print captured output.

    Args:
        server_process: Running server process.
    """
    print("\n[TEST] Stopping server after demonstration...", flush=True)

    try:
        server_process.terminate()
        server_process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        print("[TEST] Server did not stop in time. Killing process.", flush=True)
        server_process.kill()
    except OSError as exc:
        print(f"[TEST] ERROR: Failed to stop server cleanly: {exc}", file=sys.stderr, flush=True)

    try:
        stdout_output, stderr_output = server_process.communicate(timeout=2)
    except (subprocess.TimeoutExpired, OSError):
        stdout_output, stderr_output = "", ""

    if stdout_output:
        print("\n[TEST] Captured server STDOUT:", flush=True)
        print(stdout_output.rstrip(), flush=True)

    if stderr_output:
        print("\n[TEST] Captured server STDERR:", flush=True)
        print(stderr_output.rstrip(), flush=True)



def main() -> int:
    """Program entry point.

    Returns:
        Exit status code.
    """
    if not SERVER_SCRIPT.exists() or not CLIENT_SCRIPT.exists():
        print(
            "[TEST] ERROR: socket_server.py and socket_client.py must be present.",
            file=sys.stderr,
            flush=True,
        )
        return 1

    print("[TEST] Socket connection demonstration starting.", flush=True)
    print("[TEST] Required cases: success path, message exchange, bad cases, and clean disconnect.", flush=True)

    server_process = start_server()
    if server_process is None:
        return 1

    overall_success = True

    try:
        success_case = run_command(
            [
                sys.executable,
                str(CLIENT_SCRIPT),
                "--host",
                "localhost",
                "--port",
                "333",
                "--message",
                "Test message from client to server",
            ],
            "Successful connection and message exchange",
        )
        if success_case is None or success_case.returncode != 0:
            overall_success = False

        bad_localhost_case = run_command(
            [
                sys.executable,
                str(CLIENT_SCRIPT),
                "--host",
                "localhost",
                "--port",
                "35999",
                "--message",
                "This should fail because the server is not listening on port 35999",
            ],
            "Error handling when connecting to inactive localhost port 35999",
        )
        if bad_localhost_case is None or bad_localhost_case.returncode == 0:
            overall_success = False

        martian_case = run_command(
            [
                sys.executable,
                str(CLIENT_SCRIPT),
                "--host",
                "240.0.0.1",
                "--port",
                "333",
                "--message",
                "This should fail because the address is invalid for the test scenario",
                "--timeout",
                "2",
            ],
            "Error handling when connecting to Martian IP 240.0.0.1 on port 333",
        )
        if martian_case is None or martian_case.returncode == 0:
            overall_success = False
    finally:
        stop_server(server_process)

    inactive_server_case = run_command(
        [
            sys.executable,
            str(CLIENT_SCRIPT),
            "--host",
            "localhost",
            "--port",
            "333",
            "--message",
            "This should fail because the server has been stopped",
        ],
        "Error handling when server is not running on localhost:333",
    )
    if inactive_server_case is None or inactive_server_case.returncode == 0:
        overall_success = False

    print("\n[TEST] Demonstration complete.", flush=True)
    if overall_success:
        print("[TEST] All required demonstration scenarios behaved as expected.", flush=True)
        return 0

    print("[TEST] One or more demonstration scenarios did not behave as expected.", flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())
