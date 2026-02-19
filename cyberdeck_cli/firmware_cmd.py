"""Firmware registry commands."""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from cyberdeck_cli.registry import load_firmware

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command("list")
def firmware_list(
    device: Optional[str] = typer.Option(None, help="Filter by compatible device ID"),
) -> None:
    """List all registered firmware."""
    firmware = load_firmware()
    if not firmware:
        console.print("[yellow]No firmware found in registry/firmware/[/yellow]")
        raise typer.Exit(1)

    table = Table(title="Firmware Registry")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Toolchain", style="green")
    table.add_column("License")
    table.add_column("Devices")
    table.add_column("Variants")

    for fid, fw in firmware.items():
        devs = fw.get("compatible_devices", [])
        if device and device not in devs:
            continue
        variants = fw.get("variants", [])
        table.add_row(
            fid,
            fw.get("name", ""),
            fw.get("toolchain", ""),
            fw.get("upstream", {}).get("license", ""),
            ", ".join(devs),
            str(len(variants)),
        )
    console.print(table)


@app.command("show")
def firmware_show(firmware_id: str = typer.Argument(..., help="Firmware ID")) -> None:
    """Show full details for a firmware entry."""
    firmware = load_firmware()
    fw = firmware.get(firmware_id)
    if not fw:
        console.print(f"[red]Firmware '{firmware_id}' not found.[/red]")
        console.print(f"Available: {', '.join(firmware.keys())}")
        raise typer.Exit(1)

    console.print(f"\n[bold cyan]{fw.get('name', firmware_id)}[/bold cyan]  ({firmware_id})\n")

    info = Table(show_header=False, box=None, pad_edge=False)
    info.add_column("Field", style="bold")
    info.add_column("Value")
    info.add_row("Description", fw.get("description", ""))
    info.add_row("Toolchain", fw.get("toolchain", ""))
    info.add_row("Framework", fw.get("framework", ""))

    upstream = fw.get("upstream", {})
    if upstream:
        info.add_row("Repo", upstream.get("repo", ""))
        info.add_row("Branch", upstream.get("branch", ""))
        info.add_row("License", upstream.get("license", ""))

    info.add_row("Devices", ", ".join(fw.get("compatible_devices", [])))
    info.add_row("Artifact", fw.get("artifact_pattern", ""))

    bf = fw.get("build_flags", {})
    if bf:
        info.add_row("Build flags", ", ".join(f"{k}={v}" for k, v in bf.items()))

    console.print(info)

    variants = fw.get("variants", [])
    if variants:
        console.print("\n[bold]Variants:[/bold]\n")
        vt = Table()
        vt.add_column("Env", style="cyan")
        vt.add_column("Label")
        vt.add_column("Description")
        for v in variants:
            vt.add_row(v.get("env", ""), v.get("label", ""), v.get("description", ""))
        console.print(vt)


@app.command("variants")
def firmware_variants(firmware_id: str = typer.Argument(..., help="Firmware ID")) -> None:
    """List build variants for a firmware."""
    firmware = load_firmware()
    fw = firmware.get(firmware_id)
    if not fw:
        console.print(f"[red]Firmware '{firmware_id}' not found.[/red]")
        raise typer.Exit(1)

    variants = fw.get("variants", [])
    if not variants:
        console.print(f"[yellow]No variants defined for {firmware_id}.[/yellow]")
        raise typer.Exit(0)

    table = Table(title=f"Variants — {fw.get('name', firmware_id)}")
    table.add_column("Env", style="cyan")
    table.add_column("Label")
    table.add_column("Description")
    for v in variants:
        table.add_row(v.get("env", ""), v.get("label", ""), v.get("description", ""))
    console.print(table)
