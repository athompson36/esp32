"""Cyberdeck Manager CLI entry point."""

from __future__ import annotations

import typer

from cyberdeck_cli.device_cmd import app as device_app
from cyberdeck_cli.firmware_cmd import app as firmware_app
from cyberdeck_cli.flash_cmd import app as flash_app
from cyberdeck_cli.inspect_cmd import app as inspect_app

app = typer.Typer(
    name="cyberdeck",
    help="Device, firmware, flash, and hardware lifecycle manager for the ESP32 lab.",
    no_args_is_help=True,
)

app.add_typer(device_app, name="device", help="Device registry operations")
app.add_typer(firmware_app, name="firmware", help="Firmware registry operations")
app.add_typer(flash_app, name="flash", help="Flash and backup operations")
app.add_typer(inspect_app, name="inspect", help="Hardware inspector")


@app.callback()
def _global_opts() -> None:
    """Cyberdeck Manager — unified lab CLI."""


if __name__ == "__main__":
    app()
