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
        files = list(APP.rglob("*.json"))
        self.assertGreaterEqual(len(files), 3)
        for path in files:
            with self.subTest(path=str(path.relative_to(ROOT))):
                data = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(data.get("doctype"), "DocType")

    def test_sync_modules_exist(self):
        for module in ("sync.py", "suppliers.py", "items.py", "invoices.py", "zoho_client.py"):
            self.assertTrue((APP / module).is_file(), module)

    def test_api_exposes_all_sync_jobs(self):
        source = (APP / "api.py").read_text(encoding="utf-8")
        for endpoint in ("sync_customers", "sync_suppliers", "sync_items", "sync_invoices"):
            self.assertIn("def " + endpoint, source)

    def test_invoice_guardrails_are_present(self):
        source = (APP / "invoices.py").read_text(encoding="utf-8")
        self.assertIn("_reject_if_taxed_or_discounted", source)
        self.assertIn('doc.docstatus != 0', source)
        self.assertIn("foreign currency", source)

if __name__ == "__main__":
    unittest.main()
