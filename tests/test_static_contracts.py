import ast
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "zoho_integration"

class AppContractTests(unittest.TestCase):
    def test_frappe_package_metadata_exists(self):
        self.assertTrue((APP / "hooks.py").is_file())
        self.assertTrue((APP / "patches.txt").is_file())
        self.assertTrue((APP / "__init__.py").is_file())

    def test_python_sources_parse(self):
        for path in APP.rglob("*.py"):
            with self.subTest(path=str(path.relative_to(ROOT))):
                ast.parse(path.read_text(encoding="utf-8"))

    def test_doctype_json_is_valid(self):
        files = list((APP / "zoho_integration" / "doctype").rglob("*.json"))
        self.assertGreaterEqual(len(files), 2)
        for path in files:
            with self.subTest(path=str(path.relative_to(ROOT))):
                data = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(data.get("doctype"), "DocType")
        page_json = APP / "page" / "zoho_books_dashboard" / "zoho_books_dashboard.json"
        page = json.loads(page_json.read_text(encoding="utf-8"))
        self.assertEqual(page.get("doctype"), "Page")

    def test_desk_dashboard_assets_exist(self):
        page = APP / "page" / "zoho_books_dashboard"
        self.assertTrue((page / "zoho_books_dashboard.json").is_file())
        self.assertTrue((page / "zoho_books_dashboard.js").is_file())
        self.assertTrue((APP / "page" / "__init__.py").is_file())

    def test_sync_modules_exist(self):
        for module in ("sync.py", "suppliers.py", "items.py", "invoices.py", "zoho_client.py"):
            self.assertTrue((APP / module).is_file(), module)

    def test_api_exposes_all_sync_jobs(self):
        source = (APP / "api.py").read_text(encoding="utf-8")
        for endpoint in ("sync_customers", "sync_suppliers", "sync_items", "sync_invoices"):
            self.assertIn("def " + endpoint, source)

    def test_safe_token_diagnostics_do_not_expose_secrets(self):
        source = (APP / "api.py").read_text(encoding="utf-8")
        self.assertIn("def token_storage_status", source)
        self.assertIn("access_token_stored", source)
        self.assertNotIn('"access_token": settings.get_password', source)

    def test_oauth_tokens_use_encrypted_password_storage(self):
        settings = (APP / "zoho_integration" / "doctype" / "zoho_books_settings" / "zoho_books_settings.py").read_text(encoding="utf-8")
        client = (APP / "zoho_client.py").read_text(encoding="utf-8")
        self.assertIn("set_encrypted_password", settings)
        self.assertIn("self.s.set_tokens(data)", client)
        self.assertNotIn(".set_password(", settings + client)

    def test_invoice_guardrails_are_present(self):
        source = (APP / "invoices.py").read_text(encoding="utf-8")
        self.assertIn("_reject_if_taxed_or_discounted", source)
        self.assertIn('doc.docstatus != 0', source)
        self.assertIn("foreign currency", source)

if __name__ == "__main__":
    unittest.main()
