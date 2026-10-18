"""Prepare and launch a private SDK server from a full project checkout (Python 3.9+)."""

import argparse
import getpass
import json
import os
from pathlib import Path
import re
import subprocess
import sys


SERVER_ID = "TogetherBaseline"


def single_line(value, label):
    if not value.strip() or any(ord(c) < 32 for c in value) or "\x7f" in value:
        raise ValueError(f"{label} must be a non-empty single line without control characters")
    return value


def render_commands(steam_ids, password, map_name, port):
    if len(steam_ids) != 2 or len(set(steam_ids)) != 2:
        raise ValueError("Provide exactly two different SteamID64 values")
    if any(not re.fullmatch(r"7656119[0-9]{10}", value) for value in steam_ids):
        raise ValueError("Each player must use their 17-digit individual SteamID64")
    single_line(password, "Password")
    single_line(map_name, "Map")
    if not 1024 <= port <= 65534:
        raise ValueError("Port must be between 1024 and 65534 (the server also uses port + 1)")
    lines = [
        "Name Together Sandbox - Private Baseline",
        f"Map {map_name}",
        "MaxPlayers 2",
        "PvE",
        "Perspective Both",
        f"Port {port}",
        "Whitelisted",
        f"Password {password}",
        "// After the server finishes loading, enter these commands in its console:",
        f"// Permit {steam_ids[0]}/PlayerOne",
        f"// Permit {steam_ids[1]}/PlayerTwo",
        "// Then enter Save to persist the allowlist.",
    ]
    return "\n".join(lines) + "\n"


def prepare(root, steam_ids, password, map_name, port):
    shared = root / "Builds" / "Shared"
    if not (shared / "ModInfo.json").is_file():
        raise ValueError("Not a full U3-SDK checkout: Builds/Shared/ModInfo.json is missing")
    content = render_commands(steam_ids, password, map_name, port)
    destination = shared / "Servers" / SERVER_ID / "Server" / "Commands.dat"
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation: rerunning setup must never replace a world configuration.
    with destination.open("x", encoding="utf-8", newline="\n") as stream:
        if os.name != "nt":
            os.fchmod(stream.fileno(), 0o600)
        stream.write(content)
    return destination


def build_identity(root):
    identity = json.loads((root / "Builds" / "Shared" / "ModInfo.json").read_text(encoding="utf-8"))
    return identity["Name"], ".".join(str(identity[key]) for key in
                                     ("Major_Version", "Minor_Version", "Patch_Version"))


def server_command(executable):
    # CommandLine.tryGetServer takes the entire string following +LANServer/ as the ID.
    # Therefore the server selector MUST be the last argument.
    return [str(executable), "-batchmode", "-nographics", f"+LANServer/{SERVER_ID}"]


def preflight(root, executable):
    if not (root / "ProjectSettings" / "ProjectVersion.txt").is_file():
        raise ValueError("Use a full project checkout, not just a copied executable")
    name, version = build_identity(root)
    if not executable.is_file():
        raise ValueError(f"Build missing: {executable}. Build it in Unity first; see docs/multiplayer-baseline.md")
    if os.name != "nt" and not os.access(executable, os.X_OK):
        raise ValueError("The selected executable is not executable")
    config = root / "Builds" / "Shared" / "Servers" / SERVER_ID / "Server" / "Commands.dat"
    if not config.is_file():
        raise ValueError("Private server configuration missing. Run the init command first")
    lines = set(config.read_text(encoding="utf-8").splitlines())
    if not {"Whitelisted", "MaxPlayers 2", "PvE"}.issubset(lines):
        raise ValueError("Private baseline requires Whitelisted, MaxPlayers 2 and PvE")
    permits = [line for line in lines if line.startswith("// Permit ")]
    passwords = [line for line in lines if line.startswith("Password ") and line[9:].strip()]
    if len(permits) != 2 or len(passwords) != 1:
        raise ValueError("Private baseline requires two commented enrollment commands and a password")
    return name, version


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[1])
    commands = parser.add_subparsers(dest="action", required=True)
    init = commands.add_parser("init", help="Create local configuration; refuses to overwrite it")
    init.add_argument("--steam-id", action="append", required=True, help="Repeat for each of the two players")
    init.add_argument("--map", default="PEI", dest="map_name")
    init.add_argument("--port", type=int, default=27015)
    for action in ("check", "run"):
        command = commands.add_parser(action, help="Check prerequisites" if action == "check" else "Start private server")
        command.add_argument("--executable", type=Path, default=Path("Builds/Test/Unturned.exe"),
                             help="Path relative to the checkout; defaults to Windows development build")
    args = parser.parse_args(argv)
    root = args.project_root.resolve()
    try:
        if args.action == "init":
            password = getpass.getpass("Choose a private server password: ")
            if password != getpass.getpass("Confirm password: "):
                raise ValueError("Passwords do not match")
            destination = prepare(root, args.steam_id, password, args.map_name, args.port)
            print(f"Created {destination}. Configuration contains private player IDs and a password; do not share it.")
            return 0
        executable = args.executable
        if not executable.is_absolute():
            executable = root / executable
        executable = executable.resolve()
        # A build outside this checkout can resolve a different root and load the wrong world.
        try:
            executable.relative_to(root / "Builds")
        except ValueError:
            raise ValueError("Select a build inside this checkout's Builds directory") from None
        name, version = preflight(root, executable)
        print(f"Configured identity: {name} {version}. Both clients must be built from the same commit.")
        print(f"Server ID: {SERVER_ID}. Save with Save; stop safely with Shutdown.")
        print("On first startup, enter the two Permit commands from Commands.dat in the server console, then Save.")
        print("Preflight does not verify Unity compilation, Steam connectivity, asset loading or multiplayer.")
        if args.action == "run":
            print("Starting server. Keep this console open and use Shutdown before closing it.", flush=True)
            return subprocess.call(server_command(executable), cwd=executable.parent)
        return 0
    except (ValueError, OSError, KeyError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
