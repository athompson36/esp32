"""Hardware inspector commands — chip info, MAC, flash size via esptool."""

from __future__ import annotations

import glob as _glob
import re
import subprocess
import sys
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(no_args_is_help=True)
console = Console()


def _detect_ports() -> list[str]:
    patterns = ["/dev/cu.usbmodem*", "/dev/cu.usbserial*", "/dev/ttyUSB*", "/dev/ttyACM*"]
    ports: list[str] = []
    for pat in patterns:
        ports.extend(sorted(_glob.glob(pat)))
    return ports


def _run_esptool(*args: str, timeout: int = 30) -> str:
    """Run esptool and return stdout, or empty string on failure."""
    cmd = [sys.executable, "-m", "esptool", *args]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.stdout + result.stderr
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


@app.command("chip")
def inspect_chip(
    port: Optional[str] = typer.Option(None, help="Serial port (auto-detect if omitted)"),
) -> None:
    """Detect chip type and revision on a connected device."""
    if not port:
        ports = _detect_ports()
        if not ports:
            console.print("[red]No ports detected.[/red]")
            raise typer.Exit(1)
        port = ports[0]

    console.print(f"Probing [cyan]{port}[/cyan]...\n")
    output = _run_esptool("--port", port, "chip_id")

    if not output:
        console.print("[red]No response from esptool. Is the device in bootloader mode?[/red]")
        raise typer.Exit(1)

    table = Table(title="Chip Info", show_header=False, box=None)
    table.add_column("Field", style="bold")
    table.add_column("Value")

    for line in output.splitlines():
        line = line.strip()
        if "Chip is" in line:
            table.add_row("Chip", line.split("Chip is")[-1].strip())
        elif "Crystal is" in line:
            table.add_row("Crystal", line.split("Crystal is")[-1].strip())
        elif "Features:" in line:
            table.add_row("Features", line.split("Features:")[-1].strip())
        elif "MAC:" in line:
            table.add_row("MAC", line.split("MAC:")[-1].strip())
        elif "Chip ID:" in line:
            table.add_row("Chip ID", line.split("Chip ID:")[-1].strip())

    console.print(table)
    console.print(f"\n[dim]Raw output:[/dim]\n{output}")


@app.command("mac")
def inspect_mac(
    port: Optional[str] = typer.Option(None, help="Serial port (auto-detect if omitted)"),
) -> None:
    """Read the MAC address of a connected device."""
    if not port:
        ports = _detect_ports()
        if not ports:
            console.print("[red]No ports detected.[/red]")
            raise typer.Exit(1)
        port = ports[0]

    output = _run_esptool("--port", port, "read_mac")
    mac_match = re.search(r"MAC:\s*([\da-f:]{17})", output, re.IGNORECASE)
    if mac_match:
        console.print(f"MAC: [bold cyan]{mac_match.group(1)}[/bold cyan]")
    else:
        console.print("[red]Could not read MAC.[/red]")
        if output:
            console.print(f"[dim]{output}[/dim]")
        raise typer.Exit(1)


@app.command("flash-size")
def inspect_flash_size(
    port: Optional[str] = typer.Option(None, help="Serial port (auto-detect if omitted)"),
) -> None:
    """Detect flash size of a connected device."""
    if not port:
        ports = _detect_ports()
        if not ports:
            console.print("[red]No ports detected.[/red]")
            raise typer.Exit(1)
        port = ports[0]

    output = _run_esptool("--port", port, "flash_id")
    size_match = re.search(r"Detected flash size:\s*(\S+)", output)
    mfr_match = re.search(r"Manufacturer:\s*(\S+)", output)
    dev_match = re.search(r"Device:\s*(\S+)", output)

    table = Table(title="Flash Info", show_header=False, box=None)
    table.add_column("Field", style="bold")
    table.add_column("Value")

    if mfr_match:
        table.add_row("Manufacturer", mfr_match.group(1))
    if dev_match:
        table.add_row("Device", dev_match.group(1))
    if size_match:
        table.add_row("Flash size", size_match.group(1))
    else:
        console.print("[red]Could not detect flash size.[/red]")
        if output:
            console.print(f"[dim]{output}[/dim]")
        raise typer.Exit(1)

    console.print(table)


@app.command("ports")
def inspect_ports() -> None:
    """List all detected USB serial ports."""
    ports = _detect_ports()
    if not ports:
        console.print("[yellow]No USB serial ports detected.[/yellow]")
        raise typer.Exit(1)
    table = Table(title="USB Serial Ports")
    table.add_column("Port", style="cyan")
    for p in ports:
        table.add_row(p)
    console.print(table)
