# Private multiplayer baseline

Status: setup tooling prepared; Unity build and two-player acceptance **not yet run**.

This milestone proves the SDK works for both players before changing gameplay. The working mod identity is `Together Sandbox`, version `0.1.0`. Use separate Steam accounts and the same source commit for both clients and the server. Version metadata alone does not prove binaries match.

## Prerequisites

- Full checkout of this branch on each player's computer, including Git LFS content if required.
- Unity Hub and **Unity 2022.3.62f3**. Install Windows build support for the Windows test build.
- Steam running, with Unturned installed. The SDK loads large content from that installation.
- Python 3.9+ on the host for the helper. Python is a setup dependency, not a new game dependency.
- Two individual 17-digit SteamID64 values. These are not profile display names.

The initial instructions use Windows because the SDK's **Build Test** target produces a Windows executable. If either player uses macOS/Linux, record the OS and establish a matching platform build before claiming this milestone complete. No native platform build was tested here.

## Build the baseline

1. Open the checkout with Unity 2022.3.62f3 and let imports complete. Resolve compile errors before proceeding.
2. Open `Assets/GameStartup.unity`; test Play with Steam running.
3. Use **Window > Unturned > Build Tool > Build Test**. The SDK can download the Steam dedicated-server redistributables as part of this step.
4. Confirm `Builds/Test/Unturned.exe` exists and launches as a client.
5. Repeat on the other player's computer from the same source revision. Record `git rev-parse HEAD` on both machines.

The SDK can also host from the editor with **Playing in Unity > Dedicated Server In Editor**. The helper below deliberately uses a separate process and its own server ID instead of the editor's `Singleplayer` world.

Do not copy only the executable to another computer: it depends on Unity output, Steam libraries, shared files and installed content. For this first test use a complete local checkout and build on each machine. Packaging is a later task.

## Initialize once on the host

From the repository root, replace the two placeholder IDs:

```powershell
py -3 tools/multiplayer.py init --steam-id YOUR_STEAMID64 --steam-id PARTNER_STEAMID64
py -3 tools/multiplayer.py check
py -3 tools/multiplayer.py run
```

Use `python3` instead of `py -3` where appropriate. Setup prompts privately for a password and confirmation; it does not put the password in command-line history. Optional initialization arguments: `--map PEI --port 27015`.

The helper writes `Builds/Shared/Servers/TogetherBaseline/Server/Commands.dat`. This directory is already ignored by Git. It enables PvE, two slots, a password and `Whitelisted`. It includes two commented `Permit SteamID64/Name` instructions. **Permit is a runtime command in this SDK: putting an active Permit line in Commands.dat does not enroll a player.** After the server finishes loading, copy the two commands (without the leading `//`) from this local file into its console, then enter `Save`. This persists the game's allowlist for later starts. Until enrollment, the empty allowlist rejects everyone. The tool does not generate the game's binary allowlist itself.

The setup grants no administrator privileges and enables no cheats. It refuses to overwrite existing configuration; edit the local file deliberately while the server is stopped if needed. For an existing world, inspect its persisted allowlist with the server's `Permits` command and remove obsolete entries using `Unpermit SteamID64` before sharing access. Enrollment comments are instructions, not proof of the persisted allowlist's contents.

`check` validates local prerequisites and private settings. It does not prove that the executable is compatible, Steam works or peers can connect.

The launch command is:

```text
Builds/Test/Unturned.exe -batchmode -nographics +LANServer/TogetherBaseline
```

Keep `+LANServer/TogetherBaseline` last: this SDK parses everything after the selector as the server ID. The helper uses an argument array, so checkout paths with spaces do not require shell escaping. Run it from an interactive terminal and leave the server console open.

SDK builds run inside a project use `Builds/Shared` as their data root; they do not use `Builds/Test/Servers`. A packaged build outside the checkout uses its own installation root and is outside the helper's supported setup.

## Join together

1. Wait until the server finishes loading. Fix missing content, Steam initialization errors or unknown configuration commands before testing joins.
2. Launch the custom client normally on each computer. Keep each machine's Steam client running under that player's account.
3. Try Connect Directly using the server's code, or a Steam invitation. Enter the password when requested. Validate this flow on the custom build; do not assume vanilla success proves fork connectivity.
4. On the same computer/network, local IP joining is another option; the default query port is 27015. Use the host's LAN address from another computer, not that computer's own loopback address.
5. If playing across networks, test Server Code joining first. It normally uses Steam Datagram Relay without port forwarding. The code may change after restart.

Do not switch to public listing as a troubleshooting shortcut. If Server Codes fail, record the actual error before selecting Fake IP or direct IP. Direct IP hosting normally needs UDP **27015 and 27016** forwarded to the host and allowed through its firewall. Never expose remote administration ports for this milestone. Connection details must be tested on the actual router/network.

## Save and stop

Enter `Save` in the server console during play and `Shutdown` to save and stop safely. Standard hosting has no built-in autosave. Do not close the terminal or terminate the process as a normal shutdown method.

After shutdown, copy the entire `Builds/Shared/Servers/TogetherBaseline` directory to a private backup. Restore only while the server is stopped. Do not place saves, logs, player IDs or passwords in this public repository. The host must remain running and awake for the world to be available.

PvE prevents player-versus-player damage; zombies, hunger and other survival hazards remain in this baseline. Peaceful balancing belongs to milestone 2.

## Acceptance record

Copy this table into a private test note and fill in results. Update `plan.md` with the outcome, without personal identifiers or secrets.

| Check | Required result | Current result |
| --- | --- | --- |
| Build revision and identity | Both clients and server match | Not run |
| Unity compilation/content loading | No blocking errors | Not run |
| Two simultaneous players | Both approved accounts join | Not run |
| Access control | Unapproved account rejected; password enforced | Not run |
| Replication | Both observe movement, doors, storage, placement and driving | Not run |
| Needs | Hunger/thirst behave on the server and display correctly | Not run |
| Reconnect | Disconnect/rejoin preserves inventory and world state | Not run |
| Restart | Save, Shutdown, relaunch restores structures/storage/vehicles | Not run |
| Backup restore | Stopped-server restore recovers the test world | Not run |
| Remote connection, if needed | Both actual networks work | Not run |

For placement/vehicle checks, collect or craft items naturally. Temporary test-only administrator commands are optional; revoke privileges after testing. Do not confuse an in-memory save with a verified restart/restore.

Record the operating systems, host hardware, whether players share a network, source revision, connection method, test date and any sanitized error messages. Complete this gate before adding household, garage or task code.

## Tool validation

```text
python3 -m unittest discover -s tests -p test_multiplayer.py -v
```

These tests cover setup behavior, command injection rejection, overwrite prevention, launch arguments and prerequisite checks. They do not execute Unity or test multiplayer.

## Sources

- https://docs.smartlydressedgames.com/en/stable/u3-sdk/faq.html
- https://docs.smartlydressedgames.com/en/stable/servers/server-hosting.html
- https://docs.smartlydressedgames.com/en/stable/servers/server-codes.html
- https://docs.smartlydressedgames.com/en/stable/servers/port-forwarding.html
- Source: `BuildMethods.cs`, `UnturnedPaths.cs`, `CommandLine.cs`, `CommandPermit.cs`, `CommandWhitelisted.cs`, and `SaveManager.cs` in this fork.
