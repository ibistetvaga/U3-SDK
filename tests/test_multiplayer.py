import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest


spec = importlib.util.spec_from_file_location("multiplayer", Path(__file__).resolve().parents[1] / "tools/multiplayer.py")
multiplayer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(multiplayer)
IDS = ["76561198000000001", "76561198000000002"]


class MultiplayerSetupTests(unittest.TestCase):
    def test_private_configuration_and_exact_permit_syntax(self):
        content = multiplayer.render_commands(IDS, "local-secret", "PEI", 27015)
        self.assertIn("Whitelisted\n", content)
        self.assertIn("MaxPlayers 2\n", content)
        self.assertIn(f"// Permit {IDS[1]}/PlayerTwo\n", content)
        self.assertFalse(any(line.startswith("Permit ") for line in content.splitlines()))
        self.assertNotIn("Cheats", content)

    def test_rejects_command_injection_and_invalid_players(self):
        for password in ("", "secret\nCheats", "secret\rOwner x", "secret\x00"):
            with self.subTest(password=repr(password)), self.assertRaises(ValueError):
                multiplayer.render_commands(IDS, password, "PEI", 27015)
        for players in ([IDS[0]], [IDS[0], IDS[0]], ["../escape", IDS[1]]):
            with self.subTest(players=players), self.assertRaises(ValueError):
                multiplayer.render_commands(players, "secret", "PEI", 27015)
        with self.assertRaises(ValueError):
            multiplayer.render_commands(IDS, "secret", "PEI\nCheats", 27015)
        with self.assertRaises(ValueError):
            multiplayer.render_commands(IDS, "secret", "PEI", 65535)

    def test_existing_configuration_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shared = root / "Builds/Shared"
            shared.mkdir(parents=True)
            (shared / "ModInfo.json").write_text("{}")
            path = multiplayer.prepare(root, IDS, "original", "PEI", 27015)
            original = path.read_bytes()
            with self.assertRaises(FileExistsError):
                multiplayer.prepare(root, IDS, "replacement", "PEI", 27015)
            self.assertEqual(path.read_bytes(), original)
            if os.name != "nt":
                self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_launch_selector_is_last_and_is_a_single_argument(self):
        executable = Path("folder with spaces/Unturned.exe")
        command = multiplayer.server_command(executable)
        self.assertEqual(command[0], str(executable))
        self.assertEqual(command[-1], "+LANServer/TogetherBaseline")
        self.assertIn("-nographics", command)

    def test_preflight_requires_build_and_private_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "Builds/Shared").mkdir(parents=True)
            (root / "ProjectSettings").mkdir()
            (root / "ProjectSettings/ProjectVersion.txt").write_text("m_EditorVersion: 2022.3.62f3")
            (root / "Builds/Shared/ModInfo.json").write_text(json.dumps({
                "Name": "Together Sandbox", "Major_Version": 0, "Minor_Version": 1, "Patch_Version": 0}))
            executable = root / "Builds/Unturned.exe"
            with self.assertRaises(ValueError):
                multiplayer.preflight(root, executable)
            executable.touch()
            executable.chmod(0o700)
            with self.assertRaises(ValueError):
                multiplayer.preflight(root, executable)
            path = multiplayer.prepare(root, IDS, "secret", "PEI", 27015)
            self.assertEqual(multiplayer.preflight(root, executable), ("Together Sandbox", "0.1.0"))
            path.write_text(path.read_text().replace("Whitelisted\n", ""))
            with self.assertRaises(ValueError):
                multiplayer.preflight(root, executable)


if __name__ == "__main__":
    unittest.main()
