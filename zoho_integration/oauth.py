import secrets
from urllib.parse import urlencode
import frappe
from frappe import _
from frappe.utils import get_url


def get_authorization_url():
    s = frappe.get_single("Zoho Books Settings")
    s.check_permission("write")
    state = secrets.token_urlsafe(32)
    frappe.cache().set_value("zoho_oauth_state:" + frappe.session.user, state, expires_in_sec=600)
    callback = get_url("/api/method/zoho_integration.oauth.oauth_callback")
    params = {
        "scope": s.scopes,
        "client_id": s.client_id,
        "state": state,
        "response_type": "code",
        "redirect_uri": callback,
        "access_type": "offline",
        "prompt": "consent",
    }
    return s.accounts_domain.rstrip("/") + "/oauth/v2/auth?" + urlencode(params)


@frappe.whitelist()
def oauth_callback(code=None, state=None, **kwargs):
    expected = frappe.cache().get_value("zoho_oauth_state:" + frappe.session.user)
    if not expected or not state or not secrets.compare_digest(str(expected), str(state)):
        frappe.throw(_("Invalid or expired OAuth state."), frappe.PermissionError)
    frappe.cache().delete_value("zoho_oauth_state:" + frappe.session.user)
    if not code:
        frappe.throw(_("Zoho authorization code missing."))

    s = frappe.get_single("Zoho Books Settings")
    from zoho_integration.zoho_client import ZohoBooksClient

    # Clear stale status first. On success, set connected before set_tokens()
    # performs the one final document save. Avoid a second save after writing
    # encrypted credentials to __Auth.
    s.connected = 0
    s.save(ignore_permissions=True)
    frappe.db.commit()

    token_data = ZohoBooksClient(s).exchange_code(code)
    s.connected = 1
    s.set_tokens(token_data, require_refresh_token=True)
    frappe.db.commit()

    frappe.local.response["type"] = "redirect"
    frappe.local.response["location"] = "/app/zoho-books-settings/Zoho%20Books%20Settings"
