import frappe
from frappe.model.document import Document
from frappe import _

class ZohoBooksSettings(Document):
    def validate(self):
        for field in ("accounts_domain", "api_domain"):
            value = (self.get(field) or "").strip()
            if value and not value.startswith("https://"):
                frappe.throw(_("{0} must use HTTPS.").format(field))

    def set_tokens(self, data):
        if data.get("access_token"):
            self.set_password("access_token", data["access_token"])
        if data.get("refresh_token"):
            self.set_password("refresh_token", data["refresh_token"])
        if data.get("api_domain"):
            self.api_domain = data["api_domain"].rstrip("/")
        self.token_expiry = frappe.utils.add_to_date(
            frappe.utils.now_datetime(), seconds=max(int(data.get("expires_in", 3600))-120, 60))
        self.save(ignore_permissions=True)
