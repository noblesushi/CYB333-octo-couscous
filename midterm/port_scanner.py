"""Simple TCP port scanner with demonstration-oriented stdout output.

This module provides helper functions for scanning a host's common ports or a
custom port range. It includes input validation, conservative socket handling,
and timestamped logging suitable for terminal screenshots during demonstrations.
"""

from __future__ import annotations

import ipaddress
import socket
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Optional, Sequence


DEFAULT_COMMON_PORTS = (
    21, 22, 23, 57, 80, 88, 115, 123, 143, 161, 389, 443, 587, 873, 8080
)


@dataclass(frozen=True)
class PortResult:
    """Represents the outcome of scanning a single TCP port.

    Attributes:
        port: The scanned TCP port number.
        is_open: Whether the connection attempt succeeded.
        detail: A short human-readable description of the result.
    """

    port: int
    is_open: bool
    detail: str


class PortScannerError(Exception):
    """Raised when scanner input validation or host resolution fails."""


def timestamp() -> str:
    """Return the current local timestamp for stdout logging.

    Returns:
        A timestamp string suitable for terminal output.
    """

    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log(message: str) -> None:
    """Print a timestamped log message.

    Args:
        message: The message to print.
    """

    print(f"[{timestamp()}] {message}")


def validate_port(port: int) -> int:
    """Validate a single TCP port number.

    Args:
        port: The candidate port value.

    Returns:
        The validated port number.

    Raises:
        PortScannerError: If the port is not a valid integer in range.
    """

    min_port = 1
    max_port = 65535

    if not isinstance(port, int):
        raise PortScannerError(f"Port must be an integer: {port!r}")

    if port < min_port or port > max_port:
        raise PortScannerError(
            f"Port must be between {min_port} and {max_port}: {port}"
        )

    return port


def validate_port_range(
    start_port: Optional[int],
    end_port: Optional[int],
) -> None:
    """Validate a TCP port range.

    Args:
        start_port: The inclusive start port.
        end_port: The inclusive end port.

    Raises:
        PortScannerError: If the range is invalid.
    """

    if start_port is None and end_port is None:
        return

    if start_port is None or end_port is None:
        raise PortScannerError(
            "Both start_port and end_port must be provided together."
        )

    validate_port(start_port)
    validate_port(end_port)

    if start_port > end_port:
        raise PortScannerError(
            "Start port must be less than or equal to end port: "
            f"{start_port} > {end_port}"
        )


def normalize_host(host: str) -> str:
    """Validate and normalize a host string.

    Args:
        host: A hostname or IP address.

    Returns:
        The normalized host string.

    Raises:
        PortScannerError: If the host is empty or invalid.
    """

    if not isinstance(host, str):
        raise PortScannerError("Host must be a string.")

    cleaned_host = host.strip()
    if not cleaned_host:
        raise PortScannerError("Host must not be empty.")

    try:
        ipaddress.ip_address(cleaned_host)
        return cleaned_host
    except ValueError:
        pass

    try:
        socket.getaddrinfo(cleaned_host, None, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise PortScannerError(
            f"Host name could not be resolved: {cleaned_host}"
        ) from exc
    except OSError as exc:
        raise PortScannerError(
            f"Host validation failed for {cleaned_host}: {exc}"
        ) from exc

    return cleaned_host


def build_scan_ports(
    start_port: Optional[int] = None,
    end_port: Optional[int] = None,
    common_ports: Optional[Sequence[int]] = None,
) -> List[int]:
    """Construct the ordered list of ports to scan.

    If a range is provided, the returned list contains each port in the
    inclusive range. If no range is provided, only the common ports are used.

    Args:
        start_port: The inclusive start port.
        end_port: The inclusive end port.
        common_ports: Optional replacement set of common ports.

    Returns:
        A deduplicated list of ports to scan.

    Raises:
        PortScannerError: If any provided ports are invalid.
    """

    validate_port_range(start_port, end_port)

    selected_common_ports = (
        tuple(common_ports) if common_ports is not None else DEFAULT_COMMON_PORTS
    )
    validated_common_ports = [validate_port(port) for port in selected_common_ports]

    ports: List[int] = []
    seen = set()

    if start_port is None and end_port is None:
        for port in validated_common_ports:
            if port not in seen:
                ports.append(port)
                seen.add(port)
    else:
        for port in range(start_port, end_port + 1):
            validated_port = validate_port(port)
            if validated_port not in seen:
                ports.append(validated_port)
                seen.add(validated_port)

    return ports


def scan_port(host: str, port: int, timeout: float = 0.5) -> PortResult:
    """Attempt a TCP connection to a single host and port.

    Args:
        host: The target host.
        port: The target TCP port.
        timeout: Socket timeout in seconds.

    Returns:
        A PortResult describing whether the port was open.

    Raises:
        PortScannerError: If input validation fails.
    """

    normalized_host = normalize_host(host)
    validated_port = validate_port(port)

    if not isinstance(timeout, (int, float)):
        raise PortScannerError("Timeout must be numeric.")
    if timeout <= 0:
        raise PortScannerError("Timeout must be greater than zero.")

    sock: Optional[socket.socket] = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(float(timeout))
        result_code = sock.connect_ex((normalized_host, validated_port))

        if result_code == 0:
            return PortResult(validated_port, True, "open")
        return PortResult(
            validated_port,
            False,
            f"closed or filtered (code {result_code})",
        )
    except socket.gaierror as exc:
        return PortResult(validated_port, False, f"name resolution error: {exc}")
    except socket.timeout:
        return PortResult(validated_port, False, "timed out")
    except OSError as exc:
        return PortResult(validated_port, False, f"socket error: {exc}")
    finally:
        if sock is not None:
            try:
                sock.close()
            except OSError as exc:
                log(
                    f"Warning: failed to close socket on port "
                    f"{validated_port}: {exc}"
                )


def scan_ports(
    host: str,
    start_port: Optional[int] = None,
    end_port: Optional[int] = None,
    timeout: float = 0.5,
    common_ports: Optional[Sequence[int]] = None,
) -> List[PortResult]:
    """Scan a host across common ports and, optionally, a custom port range.

    Args:
        host: The target host.
        start_port: The inclusive start port.
        end_port: The inclusive end port.
        timeout: Socket timeout in seconds.
        common_ports: Optional replacement list of common ports.

    Returns:
        A list of per-port scan results.

    Raises:
        PortScannerError: If validation fails before scanning begins.
    """

    normalized_host = normalize_host(host)
    ports_to_scan = build_scan_ports(start_port, end_port, common_ports)

    log(
        f"Starting scan for host={normalized_host} | "
        f"ports_to_scan={len(ports_to_scan)} | timeout={timeout:.2f}s"
    )

    results: List[PortResult] = []
    started = time.perf_counter()
    for port in ports_to_scan:
        result = scan_port(normalized_host, port, timeout=timeout)
        results.append(result)
        state = "OPEN" if result.is_open else "CLOSED"
        log(f"Port {result.port:>5}: {state} | {result.detail}")

    elapsed = time.perf_counter() - started
    open_ports = [result.port for result in results if result.is_open]
    log(
        f"Completed scan for host={normalized_host} | open_ports={open_ports or 'none'} "
        f"| scanned={len(results)} | elapsed={elapsed:.2f}s"
    )
    return results


def summarize_results(host: str, results: Iterable[PortResult]) -> None:
    """Print a concise summary of scan outcomes.

    Args:
        host: The scanned host.
        results: The results to summarize.
    """

    result_list = list(results)
    open_ports = [result.port for result in result_list if result.is_open]
    closed_ports = [result.port for result in result_list if not result.is_open]

    log(f"Summary for {host}:")
    log(f"  Open ports   : {open_ports if open_ports else 'none detected'}")
    log(f"  Closed ports : {len(closed_ports)}")


def run_demo_case(
    title: str,
    host: str,
    start_port: Optional[int] = None,
    end_port: Optional[int] = None,
    timeout: float = 0.5,
    common_ports: Optional[Sequence[int]] = None,
) -> None:
    """Run a demonstration case and print any validation or scan errors.

    Args:
        title: A human-readable case label.
        host: The target host.
        start_port: The inclusive start port.
        end_port: The inclusive end port.
        timeout: Socket timeout in seconds.
        common_ports: Optional replacement list of common ports.
    """

    log("=" * 78)
    log(f"DEMO CASE: {title}")
    try:
        results = scan_ports(
            host=host,
            start_port=start_port,
            end_port=end_port,
            timeout=timeout,
            common_ports=common_ports,
        )
        summarize_results(host, results)
    except PortScannerError as exc:
        log(f"Validation error: {exc}")
    except Exception as exc:  # pylint: disable=broad-except
        log(f"Unexpected error during demo case '{title}': {exc}")


def demonstrate_invalid_inputs() -> None:
    """Demonstrate required invalid-input and unreachable-host error handling."""

    log("=" * 78)
    log("DEMO CASE: Invalid port input handling")
    for start_port, end_port in ((0, 10), (100, 99), (1, 70000)):
        try:
            log(f"Testing invalid range start_port={start_port}, end_port={end_port}")
            build_scan_ports(start_port=start_port, end_port=end_port)
        except PortScannerError as exc:
            log(f"Caught expected validation error: {exc}")

    log("=" * 78)
    log("DEMO CASE: Unreachable or invalid host handling")
    for host in ("256.256.256.256", "no-such-host.invalid"):
        try:
            log(f"Testing host validation for {host}")
            scan_ports(host=host, start_port=1, end_port=3, timeout=0.25)
        except PortScannerError as exc:
            log(f"Caught expected host error: {exc}")


def main() -> int:
    """Execute the required demonstration sequence.

    Returns:
        Process exit code.
    """

    log("Port scanner demonstration started.")
    log(
        "Targets: localhost (127.0.0.1) and scanme.nmap.org | "
        "Range demonstration: first 100 ports"
    )

    run_demo_case(
        title="Common ports on localhost (default common port list)",
        host="127.0.0.1",
    )

    run_demo_case(
        title="Custom port range on localhost (ports 1-100)",
        host="127.0.0.1",
        start_port=1,
        end_port=100,
    )

    run_demo_case(
        title="Selected ports on scanme.nmap.org using common port list",
        host="scanme.nmap.org",
    )

    run_demo_case(
        title="Performance demonstration on scanme.nmap.org (ports 1-100)",
        host="scanme.nmap.org",
        start_port=1,
        end_port=100,
        timeout=0.35,
    )

    demonstrate_invalid_inputs()

    log("Port scanner demonstration completed.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        log("Execution interrupted by user.")
        sys.exit(1)
    except Exception as exc:  # pylint: disable=broad-except
        log(f"Fatal error: {exc}")
        sys.exit(1)
