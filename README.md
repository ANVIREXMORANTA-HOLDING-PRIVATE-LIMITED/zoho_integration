# Zoho Books Integration for ERPNext

Frappe app for controlled two-way synchronization between Zoho Books (India data center) and ERPNext v16.

## Current implementation scope
- Server-side OAuth 2.0 authorization-code flow with offline refresh token.
- Zoho Books India API client and organization selection.
- Two-way customer/contact synchronization with external-ID link records.
- Dry-run support, pagination, sync logs, duplicate protection and background jobs.
- Supplier/vendor, item, invoice, bill and payment synchronization are planned modules, not enabled yet.

## Install
```bash
cd ~/frappe-bench
bench get-app https://github.com/ANVIREXMORANTA-HOLDING-PRIVATE-LIMITED/zoho_integration
bench --site your-site install-app zoho_integration
bench --site your-site migrate
bench restart
```

## Configure
1. Create a Zoho Books server-based OAuth client.
2. Add callback URL: `https://YOUR-SITE/api/method/zoho_integration.api.oauth_callback`
3. Set Client ID and Client Secret in **Zoho Books Settings**.
4. Connect, select/enter the Zoho Organization ID, and test the connection.
5. Start with dry-run sync. Enable writes only after verifying field mappings and backups.

India endpoints: `https://accounts.zoho.in` and `https://www.zohoapis.in`.

## Safety
No automatic deletion, invoice posting, payment allocation or accounting submission is performed by this release. Test against a Zoho sandbox and ERPNext test site before production use. Never commit credentials or tokens.
