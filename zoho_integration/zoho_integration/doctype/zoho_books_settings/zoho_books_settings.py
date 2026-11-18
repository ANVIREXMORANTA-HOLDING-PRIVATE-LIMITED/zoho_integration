import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils.password import set_encrypted_password


class ZohoBooksSettings(Document):
    def validate(self):
        for field in ("accounts_domain", "api_domain"):
            value = (self.get(field) or "").strip()
            if value and not value.startswith("https://"):
                frappe.throw(_("{0} must use HTTPS.").format(field))

    def set_tokens(self, data):
        # Password fields are stored encrypted in Frappe's __Auth table.
        # update_password() is for user password hashes, not Password fields.
        for field in ("access_token", "refresh_token"):
            token = data.get(field)
            if token:
                set_encrypted_password(
                    self.doctype,
                    self.name,
                    token,
                    fieldname=field,
                )

        if data.get("api_domain"):
            self.api_domain = data["api_domain"].rstrip("/")
        self.token_expiry = frappe.utils.add_to_date(
            frappe.utils.now_datetime(),
            seconds=max(int(data.get("expires_in", 3600)) - 120, 60),
        )
        self.save(ignore_permissions=True)
