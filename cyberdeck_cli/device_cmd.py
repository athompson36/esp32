"""Device registry commands."""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from cyberdeck_cli.registry import load_devices, load_firmware

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command("list")
def device_list(
    mcu: Optional[str] = typer.Option(None, help="Filter by MCU (e.g. ESP32-S3)"),
) -> None:
    """List all registered devices."""
    devices = load_devices()
    if not devices:
        console.print("[yellow]No devices found in registry/devices/[/yellow]")
        raise typer.Exit(1)

    table = Table(title="Device Registry")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("MCU", style="green")
    table.add_column("Radios")
    table.add_column("Flash Methods")
    table.add_column("Firmware")

    for did, d in devices.items():
        if mcu and mcu.lower() not in d.get("mcu", "").lower():
            continue
        table.add_row(
            did,
            d.get("name", ""),
            d.get("mcu", ""),
            ", ".join(d.get("radios", [])),
            ", ".join(d.get("flash_methods", [])),
            ", ".join(d.get("compatible_firmware", [])),
        )
    console.print(table)


@app.command("show")
def device_show(device_id: str = typer.Argument(..., help="Device ID")) -> None:
    """Show full details for a device."""
    devices = load_devices()
    d = devices.get(device_id)
    if not d:
        console.print(f"[red]Device '{device_id}' not found.[/red]")
        console.print(f"Available: {', '.join(devices.keys())}")
        raise typer.Exit(1)

    console.print(f"\n[bold cyan]{d.get('name', device_id)}[/bold cyan]  ({device_id})\n")

    table = Table(show_header=False, box=None, pad_edge=False)
    table.add_column("Field", style="bold")
    table.add_column("Value")

    for key in ("mcu", "display", "battery", "storage"):
        if d.get(key):
            table.add_row(key.capitalize(), d[key])
    if d.get("radios"):
        table.add_row("Radios", ", ".join(d["radios"]))
    if d.get("flash_methods"):
        table.add_row("Flash methods", ", ".join(d["flash_methods"]))
    if d.get("compatible_firmware"):
        table.add_row("Compatible FW", ", ".join(d["compatible_firmware"]))

    cap = d.get("capability", {})
    if cap:
        table.add_row("Chip", cap.get("chip", ""))
        table.add_row("Flash size", cap.get("flash_size", ""))
        table.add_row("RF bands", ", ".join(cap.get("rf_bands", [])))
        for flag in ("can_support", "sd_support", "launcher_compatible", "secure_element"):
            table.add_row(flag.replace("_", " ").title(), "Yes" if cap.get(flag) else "No")

    console.print(table)


@app.command("compat")
def device_compat(device_id: str = typer.Argument(..., help="Device ID")) -> None:
    """Show compatible firmware for a device."""
    devices = load_devices()
    d = devices.get(device_id)
    if not d:
        console.print(f"[red]Device '{device_id}' not found.[/red]")
        raise typer.Exit(1)

    firmware = load_firmware()
    compat = d.get("compatible_firmware", [])

    console.print(f"\n[bold]Compatible firmware for [cyan]{d.get('name', device_id)}[/cyan]:[/bold]\n")

    table = Table()
    table.add_column("Firmware ID", style="cyan")
    table.add_column("Name")
    table.add_column("Toolchain")
    table.add_column("Variants")

    for fw_id in compat:
        fw = firmware.get(fw_id, {})
        variants = fw.get("variants", [])
        var_str = ", ".join(v.get("label", v.get("env", "")) for v in variants)
        table.add_row(
            fw_id,
            fw.get("name", fw_id),
            fw.get("toolchain", ""),
            var_str or "(see registry)",
        )
    if not compat:
        console.print("[yellow]No compatible firmware listed for this device.[/yellow]")
    else:
        console.print(table)
