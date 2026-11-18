import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils.password import update_password


class ZohoBooksSettings(Document):
    def validate(self):
        for field in ("accounts_domain", "api_domain"):
            value = (self.get(field) or "").strip()
            if value and not value.startswith("https://"):
                frappe.throw(_("{0} must use HTTPS.").format(field))

    def set_tokens(self, data):
        # Frappe Documents expose get_password(), but do not implement
        # set_password(). Store Password fields through Frappe's password API.
        for field in ("access_token", "refresh_token"):
            token = data.get(field)
            if token:
                update_password(
                    self.name,
                    token,
                    doctype=self.doctype,
                    fieldname=field,
                )

        if data.get("api_domain"):
            self.api_domain = data["api_domain"].rstrip("/")
        self.token_expiry = frappe.utils.add_to_date(
            frappe.utils.now_datetime(),
            seconds=max(int(data.get("expires_in", 3600)) - 120, 60),
        )
        self.save(ignore_permissions=True)
