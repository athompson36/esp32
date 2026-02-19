"""Flash and backup CLI commands."""

from __future__ import annotations

import glob as _glob
import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from cyberdeck_cli.registry import load_devices

app = typer.Typer(no_args_is_help=True)
console = Console()


def _detect_ports() -> list[str]:
    """Return available /dev/cu.usb* serial ports (macOS) or /dev/ttyUSB* (Linux)."""
    patterns = ["/dev/cu.usbmodem*", "/dev/cu.usbserial*", "/dev/ttyUSB*", "/dev/ttyACM*"]
    ports: list[str] = []
    for pat in patterns:
        ports.extend(sorted(_glob.glob(pat)))
    return ports


@app.command("detect")
def flash_detect() -> None:
    """Detect connected USB serial ports."""
    ports = _detect_ports()
    if not ports:
        console.print("[yellow]No USB serial ports detected.[/yellow]")
        console.print("Tip: connect a device, or put it in bootloader mode (hold BOOT, press RESET).")
        raise typer.Exit(1)

    table = Table(title="Detected Serial Ports")
    table.add_column("Port", style="cyan")
    for p in ports:
        table.add_row(p)
    console.print(table)


@app.command("backup")
def flash_backup(
    port: Optional[str] = typer.Option(None, help="Serial port (auto-detect if omitted)"),
    device: str = typer.Option("t_beam_1w", help="Device ID for chip/flash-size lookup"),
    output: str = typer.Option("backup.bin", help="Output file path"),
    size: str = typer.Option("", help="Flash size override (e.g. 0x800000 for 8MB)"),
) -> None:
    """Read full flash to a local file via esptool."""
    if not port:
        ports = _detect_ports()
        if not ports:
            console.print("[red]No ports detected. Connect a device.[/red]")
            raise typer.Exit(1)
        port = ports[0]
        console.print(f"Auto-detected port: [cyan]{port}[/cyan]")

    devices = load_devices()
    d = devices.get(device, {})
    chip = d.get("capability", {}).get("chip", "esp32s3")
    flash_sz = size or d.get("capability", {}).get("flash_size", "8MB")
    if flash_sz.upper().endswith("MB"):
        flash_sz = hex(int(flash_sz[:-2]) * 1024 * 1024)

    cmd = [
        sys.executable, "-m", "esptool",
        "--chip", chip,
        "--port", port,
        "read_flash", "0", flash_sz, output,
    ]
    console.print(f"[bold]Running:[/bold] {' '.join(cmd)}\n")
    result = subprocess.run(cmd, timeout=1800)
    if result.returncode == 0:
        console.print(f"\n[green]Backup saved to {output}[/green]")
    else:
        console.print(f"\n[red]esptool exited with code {result.returncode}[/red]")
        raise typer.Exit(result.returncode)


@app.command("write")
def flash_write(
    binary: str = typer.Argument(..., help="Path to .bin firmware file"),
    port: Optional[str] = typer.Option(None, help="Serial port (auto-detect if omitted)"),
    device: str = typer.Option("t_beam_1w", help="Device ID for chip lookup"),
    offset: str = typer.Option("0x0", help="Flash offset (0x0 for factory, 0x10000 for app)"),
) -> None:
    """Write a firmware binary to flash via esptool."""
    if not Path(binary).is_file():
        console.print(f"[red]File not found: {binary}[/red]")
        raise typer.Exit(1)

    if not port:
        ports = _detect_ports()
        if not ports:
            console.print("[red]No ports detected. Connect a device.[/red]")
            raise typer.Exit(1)
        port = ports[0]
        console.print(f"Auto-detected port: [cyan]{port}[/cyan]")

    devices = load_devices()
    d = devices.get(device, {})
    chip = d.get("capability", {}).get("chip", "esp32s3")

    cmd = [
        sys.executable, "-m", "esptool",
        "--chip", chip,
        "--port", port,
        "write_flash", offset, binary,
    ]
    console.print(f"[bold]Running:[/bold] {' '.join(cmd)}\n")
    result = subprocess.run(cmd, timeout=600)
    if result.returncode == 0:
        console.print(f"\n[green]Flash complete.[/green]")
    else:
        console.print(f"\n[red]esptool exited with code {result.returncode}[/red]")
        raise typer.Exit(result.returncode)
