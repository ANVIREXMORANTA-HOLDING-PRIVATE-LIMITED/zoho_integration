import requests
import frappe
from frappe import _
from frappe.utils import add_to_date, now_datetime, get_datetime, get_url


class ZohoBooksClient:
    def __init__(self, settings):
        self.s = settings
        self.timeout = 30

    def exchange_code(self, code):
        callback = get_url("/api/method/zoho_integration.oauth.oauth_callback")
        r = requests.post(
            self.s.accounts_domain.rstrip("/") + "/oauth/v2/token",
            data={
                "grant_type": "authorization_code",
                "client_id": self.s.client_id,
                "client_secret": self.s.get_password("client_secret"),
                "redirect_uri": callback,
                "code": code,
            },
            timeout=self.timeout,
        )
        return self._json(r)

    def _refresh(self):
        refresh = self.s.get_password("refresh_token", raise_exception=False)
        if not refresh:
            frappe.throw(_(
                "Zoho refresh token is not stored for this settings record. "
                "Open Zoho Books Settings and reconnect to Zoho."
            ))
        r = requests.post(
            self.s.accounts_domain.rstrip("/") + "/oauth/v2/token",
            data={
                "grant_type": "refresh_token",
                "client_id": self.s.client_id,
                "client_secret": self.s.get_password("client_secret"),
                "refresh_token": refresh,
            },
            timeout=self.timeout,
        )
        self._store_tokens(self._json(r), preserve_refresh=True)

    def _store_tokens(self, data, preserve_refresh=False):
        # A refresh response normally omits refresh_token; retain the existing
        # encrypted refresh token rather than overwriting it with an empty value.
        if preserve_refresh and not data.get("refresh_token"):
            data = dict(data)
        self.s.set_tokens(data)

    def token(self):
        access = self.s.get_password("access_token", raise_exception=False)
        expiry_value = self.s.token_expiry
        # Frappe may return a Datetime field as a string depending on how the
        # document was loaded. Normalize it before comparing with now_datetime().
        expiry = get_datetime(expiry_value) if expiry_value else None

        if not access or not expiry or expiry <= now_datetime():
            self._refresh()
            access = self.s.get_password("access_token", raise_exception=False)

        if not access:
            frappe.throw(_(
                "Zoho access token is not stored after refresh. "
                "Reconnect to Zoho and check the OAuth callback."
            ))
        return access

    def request(self, method, path, params=None, payload=None, retry=True):
        params = dict(params or {})
        if path != "organizations":
            if not self.s.organization_id:
                frappe.throw(_("Set the Zoho Organization ID in settings."))
            params["organization_id"] = self.s.organization_id
        r = requests.request(
            method,
            self.s.api_domain.rstrip("/") + "/books/v3/" + path.lstrip("/"),
            params=params,
            json=payload,
            headers={"Authorization": "Zoho-oauthtoken " + self.token(), "Accept": "application/json"},
            timeout=self.timeout,
        )
        if r.status_code == 401 and retry:
            self._refresh()
            return self.request(method, path, params, payload, retry=False)
        data = self._json(r)
        if isinstance(data, dict) and data.get("code") not in (None, 0):
            frappe.throw(_("Zoho API error: {0}").format(data.get("message", "Unknown error")))
        return data

    def get_organizations(self):
        return self.request("GET", "organizations").get("organizations", [])

    @staticmethod
    def _json(response):
        try:
            data = response.json()
        except ValueError:
            # Some OAuth failures are returned as plain text or HTML. Preserve
            # the HTTP status and a short safe diagnostic instead of allowing
            # requests' JSONDecodeError/HTTPError to become an opaque 500.
            content_type = (response.headers.get("Content-Type") or "").lower()
            body = (response.text or "").strip()
            if "html" in content_type or body.lower().startswith(("<!doctype html", "<html")):
                detail = "Zoho returned an HTML error page; verify the OAuth app configuration and try a fresh authorization code."
            else:
                detail = body[:400] or response.reason or "Empty response from Zoho."
            if not response.ok:
                frappe.throw(_("Zoho HTTP {0}: {1}").format(response.status_code, detail))
            frappe.throw(_("Zoho returned an invalid response (HTTP {0}): {1}").format(response.status_code, detail))

        if not response.ok:
            if isinstance(data, dict):
                detail = data.get("message") or data.get("error") or response.reason
            else:
                detail = str(data)[:400]
            frappe.throw(_("Zoho HTTP {0}: {1}").format(response.status_code, detail))
        return data
