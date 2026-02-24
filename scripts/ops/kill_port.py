"""
Kill processes occupying specific ports on Windows.

Solves the recurring "zombie process" problem where uvicorn/python processes
survive after their parent dies and keep holding the socket.

Usage:
    python scripts/ops/kill_port.py 9325 5173
    python scripts/ops/kill_port.py --all-gimo
"""

import subprocess
import sys


def get_pids_on_port(port: int) -> set[int]:
    """Find all PIDs listening on a given port using netstat."""
    pids: set[int] = set()
    try:
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        for line in result.stdout.splitlines():
            # Match LISTENING or TIME_WAIT on our port
            if f":{port}" in line and ("LISTENING" in line or "TIME_WAIT" in line):
                parts = line.split()
                if parts:
                    try:
                        pid = int(parts[-1])
                        if pid > 0:
                            pids.add(pid)
                    except ValueError:
                        continue
    except Exception as e:
        print(f"  [WARN] netstat failed: {e}")
    return pids


def get_pids_on_port_powershell(port: int) -> set[int]:
    """Fallback: use PowerShell Get-NetTCPConnection for more reliable results."""
    pids: set[int] = set()
    try:
        cmd = (
            f"Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue "
            f"| Select-Object -ExpandProperty OwningProcess"
        )
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", cmd],
            capture_output=True,
            text=True,
            timeout=10,
        )
        for line in result.stdout.strip().splitlines():
            line = line.strip()
            if line.isdigit():
                pid = int(line)
                if pid > 0:
                    pids.add(pid)
    except Exception as e:
        print(f"  [WARN] PowerShell fallback failed: {e}")
    return pids


def kill_pid(pid: int) -> bool:
    """Kill a process by PID. Returns True if successful."""
    try:
        result = subprocess.run(
            ["taskkill", "/F", "/PID", str(pid)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except Exception:
        return False


def kill_pid_powershell(pid: int) -> bool:
    """Fallback: kill via PowerShell (handles edge cases taskkill misses)."""
    try:
        cmd = f"Stop-Process -Id {pid} -Force -ErrorAction SilentlyContinue"
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", cmd],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except Exception:
        return False


def free_port(port: int) -> int:
    """Kill all processes on a port. Returns number of processes killed."""
    # Try netstat first, then PowerShell fallback
    pids = get_pids_on_port(port)
    if not pids:
        pids = get_pids_on_port_powershell(port)

    if not pids:
        print(f"  Port {port}: already free")
        return 0

    killed = 0
    for pid in pids:
        print(f"  Port {port}: killing PID {pid}...", end=" ")
        if kill_pid(pid):
            print("OK (taskkill)")
            killed += 1
        elif kill_pid_powershell(pid):
            print("OK (powershell)")
            killed += 1
        else:
            print("FAILED (zombie?)")
    return killed


GIMO_PORTS = [9325, 5173]


def main():
    args = sys.argv[1:]

    if not args:
        print("Usage: python kill_port.py <port> [port2 ...] | --all-gimo")
        sys.exit(1)

    if "--all-gimo" in args:
        ports = GIMO_PORTS
    else:
        ports = []
        for a in args:
            try:
                ports.append(int(a))
            except ValueError:
                print(f"  [WARN] Ignoring invalid port: {a}")

    print(f"Freeing ports: {ports}")
    total = 0
    for port in ports:
        total += free_port(port)

    if total > 0:
        print(f"\nKilled {total} process(es). Waiting 2s for socket cleanup...")
        import time

        time.sleep(2)
    else:
        print("\nAll ports were already free.")


if __name__ == "__main__":
    main()
