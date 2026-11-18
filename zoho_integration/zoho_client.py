import requests
import frappe
from frappe import _
from frappe.utils import add_to_date, now_datetime, get_url

class ZohoBooksClient:
    def __init__(self, settings):
        self.s = settings
        self.timeout = 30

    def exchange_code(self, code):
        callback = get_url("/api/method/zoho_integration.oauth_callback")
        r = requests.post(self.s.accounts_domain.rstrip("/") + "/oauth/v2/token",
            data={"grant_type":"authorization_code","client_id":self.s.client_id,
                  "client_secret":self.s.get_password("client_secret"),"redirect_uri":callback,"code":code},
            timeout=self.timeout)
        return self._json(r)

    def _refresh(self):
        refresh = self.s.get_password("refresh_token")
        if not refresh:
            frappe.throw(_("Zoho refresh token missing. Reconnect the account."))
        r = requests.post(self.s.accounts_domain.rstrip("/") + "/oauth/v2/token",
            data={"grant_type":"refresh_token","client_id":self.s.client_id,
                  "client_secret":self.s.get_password("client_secret"),"refresh_token":refresh},
            timeout=self.timeout)
        self._store_tokens(self._json(r), preserve_refresh=True)

    def _store_tokens(self, data, preserve_refresh=False):
        if data.get("access_token"):
            self.s.set_password("access_token", data["access_token"])
        if data.get("refresh_token") and not preserve_refresh:
            self.s.set_password("refresh_token", data["refresh_token"])
        if data.get("api_domain"):
            self.s.api_domain = data["api_domain"].rstrip("/")
        self.s.token_expiry = add_to_date(now_datetime(), seconds=max(int(data.get("expires_in",3600))-120,60))
        self.s.save(ignore_permissions=True)

    def token(self):
        if not self.s.get_password("access_token") or not self.s.token_expiry or self.s.token_expiry <= now_datetime():
            self._refresh()
        return self.s.get_password("access_token")

    def request(self, method, path, params=None, payload=None, retry=True):
        params = dict(params or {})
        if path != "organizations":
            if not self.s.organization_id:
                frappe.throw(_("Set the Zoho Organization ID in settings."))
            params["organization_id"] = self.s.organization_id
        r = requests.request(method, self.s.api_domain.rstrip("/") + "/books/v3/" + path.lstrip("/"),
            params=params, json=payload,
            headers={"Authorization":"Zoho-oauthtoken " + self.token(),"Accept":"application/json"},
            timeout=self.timeout)
        if r.status_code == 401 and retry:
            self._refresh()
            return self.request(method, path, params, payload, retry=False)
        data = self._json(r)
        if isinstance(data, dict) and data.get("code") not in (None, 0):
            frappe.throw(_("Zoho API error: {0}").format(data.get("message","Unknown error")))
        return data

    def get_organizations(self):
        return self.request("GET", "organizations").get("organizations", [])

    @staticmethod
    def _json(response):
        try:
            data = response.json()
        except ValueError:
            response.raise_for_status()
            frappe.throw(_("Zoho returned invalid JSON."))
        if not response.ok:
            msg = data.get("message", response.reason) if isinstance(data,dict) else response.reason
            frappe.throw(_("Zoho HTTP {0}: {1}").format(response.status_code,msg))
        return data
