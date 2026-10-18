# Together Sandbox development plan

## Goal and authorization

Create a private two-player couples' life simulation using this U3-SDK fork: a shared home, everyday routines, decorating, driving and open-ended exploration. First playable loop: join together, furnish a home, cook, drive out exploring, return, save, and resume later.

The owner authorized implementation of this plan on 2026-10-18. Continue routine work without repeated confirmation. Stop and report significant scope changes, destructive migrations, licensing/asset issues, or blockers. Do not mark milestones complete without their acceptance evidence. Keep progress and decisions in this file.

## Baseline and decisions

- Starting SDK commit: `aba323a81558487ad8d2167ac20da9c0fd72b6d9` (v3.26.3.12).
- Unity: **2022.3.62f3**, matching `ProjectSettings/ProjectVersion.txt`.
- Working mod identity: **Together Sandbox 0.1.0**. This is provisional branding; all peers need matching identity and builds.
- C#, existing Unity project, existing network transport and Steam identity. Avoid engine upgrades or replacing networking initially.
- Initially use the SDK's Windows development build for both clients and a separate headless server process. This is a documented starting path, not an assumption that both players have Windows. Other operating systems require a tested build path before acceptance.
- Use an isolated server ID `TogetherBaseline`, two player slots, a password and a two-player allowlist. Start with PEI and vanilla needs; tune gameplay after baseline verification.
- Reuse installed Unturned content through the SDK. Do not commit or redistribute the core asset bundle. Preserve SDK license and third-party notices.
- Host OS, guest OS, whether players share a network, and host hardware remain unknown. Do not configure public hosting or assume remote connectivity works until tested.

## Milestones

### 1. Baseline multiplayer — in progress, runtime blocked

Deliver matching builds, repeatable private server setup, and a tested join/save/reconnect path.

- [x] Inspect SDK build, mod identity, server argument parsing and save paths.
- [x] Add `tools/multiplayer.py` for local setup, preflight and launch without overwriting existing configuration.
- [x] Add private server setup and manual acceptance instructions in `docs/multiplayer-baseline.md`.
- [ ] Build the untouched gameplay with Unity 2022.3.62f3 on supported player hardware.
- [ ] Both players connect using separate Steam accounts and matching custom builds.
- [ ] Verify movement, building, storage, vehicle driving, hunger and thirst replication.
- [ ] Save, shut down, restart and reconnect with the same world and inventories.
- [ ] Reject an unapproved Steam account; verify the password requirement.
- [ ] Verify remote joining if players use different networks.
- [ ] Back up and restore the server folder; record build revision and results.

No gameplay milestone depends on an unverified baseline. See the acceptance record for outstanding local checks.

### 2. Peaceful shared home

- Introduce a household with the two Steam IDs, home location and shared access policy.
- First test existing group permissions for doors, furniture, storage and vehicles.
- Disable unwanted hostile spawns, PvP, home damage and building decay through configuration where possible. PvE alone does not remove other hazards.
- Slow hunger/thirst, eliminate starvation death, and avoid penalties while the server is stopped.
- Add a return-home action and shared home/storage behavior.
- Acceptance: both players independently use and modify the same home; permissions and needs survive a restart.

### 3. Building and decoration

- Inventory available placeable furniture separately from static map scenery.
- Start with existing construction placement; add a categorized catalogue, preview, rotation, movement and removal.
- Use free construction first, with optional resource costs later.
- Preserve storage contents during movement/removal. Add undo only with safe state handling.
- Acceptance: both players can decorate and edit a small home without lost contents or divergent placement, including after restart.

### 4. Car ownership and garage

- Add independent persistent car IDs, vehicle asset GUIDs, household ownership and access.
- Track stored/active/transitioning state; retain fuel, health, battery, tires, paint and location.
- Validate proximity, permissions, occupancy and clear spawn space on the server.
- Reconcile interrupted operations on startup. Never treat temporary network instance IDs as durable ownership.
- Initially reject garage storage when a vehicle contains cargo or attached constructions until those snapshots are supported.
- Acceptance: store/retrieve preserves state; simultaneous requests and interrupted operations cannot duplicate or lose cars.

### 5. Shared daily routines

- Add a shared board and event-driven progress for harvesting, cooking, delivering supplies, refueling and visiting destinations.
- Reuse existing quest features where suitable; avoid polling UI text.
- Default to in-game daily resets and no missed-session penalties. Rewards apply once.
- Cleaning/laundry require new interactions and are later content, not assumed vanilla mechanics.
- Acceptance: three tasks progress through real gameplay for both players, reset predictably and persist without duplicate rewards.

### 6. Exploration and atmosphere

- Add destinations and activities, expand furnishings and tune day/night and travel.
- Consider sleep, comfort and hygiene only after the core loop is enjoyable.
- Acceptance: a full shared evening of home life, driving and exploration with a successful save/resume.

## Implementation practices

- Keep feature code separate under `Household`, `Building`, `Needs`, `Garage`, `Tasks`, `Persistence`, `UI`, and `Integration`; select the exact assembly layout after reviewing Unity assembly references.
- Minimize upstream edits. Prefer existing events and manager methods over runtime patches.
- The server owns household, garage, task and placement decisions. Validate all client requests.
- Perform Unity object mutations on the game thread. Use configuration for rates and content lists.
- Use stable Steam IDs, asset GUIDs and generated persistent IDs. Keep runtime network identifiers transient.
- Keep original saves for world entities; separately version custom records. Atomic JSON is adequate for the initial prototype; consider SQLite for garage operations. A database transaction does not atomically save the game world: reconciliation is still required.
- Integrate periodic saving with `SaveManager` hooks and add backups before real home-building sessions. Standard server saving is manual until autosave is implemented.
- Test failures with consequences: duplicate cars/rewards, lost storage, permission bypass, reconnects and recovery. Run two-client checks for replication changes.
- Use small commits, pinned baseline revisions, explicit save migrations, and Git LFS for large custom assets. Never commit player IDs, passwords, tokens, saves or logs.

## Progress log

### 2026-10-18

- Recorded the approved design and staged baseline setup tooling. No gameplay systems changed.
- Source review caught that `Permit` only runs after the server starts. Setup keeps enrollment commands commented and documents one-time console enrollment plus `Save`; it does not assume startup configuration can populate the allowlist.
- Git transport from the workspace failed because the configured proxy was unreachable. The GitHub connector remains available for repository reads and commits.
- This environment has no Unity editor, installed Unturned content or two Steam clients. Compilation, content loading, hosting and end-to-end multiplayer cannot be verified here. This is a significant milestone blocker, not a passed baseline.
- Continue with runtime acceptance on player hardware before implementing milestone 2. The user's authorization for subsequent milestones remains in effect.

## References

- SDK README: https://github.com/ibistetvaga/U3-SDK/blob/main/README.md
- SDK build/server FAQ: https://docs.smartlydressedgames.com/en/stable/u3-sdk/faq.html
- Hosting and saves: https://docs.smartlydressedgames.com/en/stable/servers/server-hosting.html
- Server Codes: https://docs.smartlydressedgames.com/en/stable/servers/server-codes.html
- Port forwarding: https://docs.smartlydressedgames.com/en/stable/servers/port-forwarding.html
- License: `LICENSE.txt`; content notices: `THIRDPARTYNOTICES.txt`.
