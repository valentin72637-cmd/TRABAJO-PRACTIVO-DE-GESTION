"""Pruebas del asistente: sin usar la base del proyecto."""
import sqlite3
from contextlib import closing
import tempfile
import unittest
from pathlib import Path
from getpass import GetPassWarning
from unittest.mock import patch
from backend.manage import ask_new_password, password_problem, inspect_account, backup_database


class RecoveryWizardTests(unittest.TestCase):
    def test_retries_empty_short_published_and_mismatched(self):
        answers = ["", "corta", "Admin123!", "Frase personal de prueba", "No coincide",
                   "Frase personal de prueba", "Frase personal de prueba"]
        with patch("backend.manage.getpass", side_effect=answers), patch("builtins.print") as output:
            self.assertEqual(ask_new_password(), "Frase personal de prueba")
            text = " ".join(str(call.args) for call in output.call_args_list)
            self.assertIn("menos de 8", text)
            self.assertIn("publicada", text)
            self.assertIn("no coinciden", text)
            self.assertNotIn("Frase personal de prueba", text)

    def test_password_validation_boundaries(self):
        self.assertIsNotNone(password_problem("x"*7))
        self.assertIsNone(password_problem("x"*8))
        self.assertIsNone(password_problem("x"*128))
        self.assertIsNotNone(password_problem("x"*129))
        self.assertIsNotNone(password_problem("Cliente123!"))

    def test_no_echo_fallback(self):
        with patch("backend.manage.getpass", side_effect=GetPassWarning("No TTY")), patch("builtins.print"):
            with self.assertRaises(GetPassWarning):
                ask_new_password()

    def test_missing_path_does_not_create_a_database(self):
        with tempfile.TemporaryDirectory(prefix="segurar-recovery-test-") as folder:
            missing = Path(folder) / "missing.db"
            with self.assertRaises(FileNotFoundError):
                inspect_account(missing, "missing@example.com")
            self.assertFalse(missing.exists())

    def test_backup_preserves_users_and_relations(self):
        with tempfile.TemporaryDirectory(prefix="segurar-recovery-test-") as folder:
            source = Path(folder) / "fixture.db"
            with closing(sqlite3.connect(source)) as db:
                db.executescript("""
                    CREATE TABLE usuarios(id INTEGER PRIMARY KEY, email TEXT, role TEXT);
                    CREATE TABLE polizas(id INTEGER PRIMARY KEY, cliente_id INTEGER REFERENCES usuarios(id));
                    INSERT INTO usuarios VALUES(1,'fixture@example.com','cliente');
                    INSERT INTO polizas VALUES(1,1);
                """)
            target = backup_database(source)
            self.assertNotEqual(source, target)
            self.assertEqual(inspect_account(source, "fixture@example.com"), (1, "cliente"))
            with closing(sqlite3.connect(target)) as db:
                self.assertEqual(db.execute("PRAGMA integrity_check").fetchone()[0], "ok")
                self.assertEqual(db.execute("PRAGMA foreign_key_check").fetchall(), [])
                self.assertEqual(db.execute("SELECT COUNT(*) FROM polizas").fetchone()[0], 1)
