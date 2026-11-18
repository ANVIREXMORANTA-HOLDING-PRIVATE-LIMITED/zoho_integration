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

    def set_tokens(self, data, require_refresh_token=False):
        access_token = data.get("access_token")
        if not access_token:
            frappe.throw(_("Zoho did not return an access token. Check the OAuth response and try connecting again."))

        refresh_token = data.get("refresh_token")
        if require_refresh_token and not refresh_token:
            frappe.throw(_(
                "Zoho did not return a refresh token. The connection was not completed. "
                "Revoke this app's existing Zoho authorization and connect again, granting offline access."
            ))

        # Password fields are encrypted in Frappe's __Auth table.
        for field, token in (("access_token", access_token), ("refresh_token", refresh_token)):
            if token:
                set_encrypted_password(
                    self.doctype,
                    self.name,
                    token,
                    fieldname=field,
                )

        # Read back only to verify storage; never log or display token values.
        if not self.get_password("access_token", raise_exception=False):
            frappe.throw(_(
                "Zoho returned an access token, but Frappe could not read it back from encrypted password storage. "
                "Check the site's encryption key and __Auth table."
            ))

        if (require_refresh_token or refresh_token) and not self.get_password("refresh_token", raise_exception=False):
            frappe.throw(_(
                "Zoho refresh token was returned but could not be read back from encrypted password storage."
            ))

        if data.get("api_domain"):
            self.api_domain = data["api_domain"].rstrip("/")
        self.token_expiry = frappe.utils.add_to_date(
            frappe.utils.now_datetime(),
            seconds=max(int(data.get("expires_in", 3600)) - 120, 60),
        )

        # We wrote Password fields directly with set_encrypted_password above.
        # Frappe's normal Document.save() calls _save_passwords(), which treats
        # blank Password fields on this loaded document as deletions from __Auth.
        # Skip that second password pass so it cannot erase the tokens we just stored.
        self.flags.ignore_save_passwords = True
        self.save(ignore_permissions=True)
