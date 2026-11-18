# Zoho Books Integration for ERPNext

Frappe app for controlled two-way synchronization between Zoho Books (India data center) and ERPNext v16.

## Implemented in this branch
- Server-side OAuth 2.0 authorization-code flow and refresh-token storage.
- Zoho Books India API client and organization discovery.
- Two-way customer/contact synchronization (Zoho customer contacts ↔ ERPNext Customer).
- External-ID document links, pagination, background jobs, sync logs and dry-run mode.
- Exact-name matching when importing contacts and prefetch matching before outbound creation to reduce duplicates.

## Not yet implemented
Supplier/vendor records, items, invoices, bills, payments, tax/account mappings, webhook delivery, field-level conflict resolution and multi-organization support. Do not treat this release as a complete accounting connector until those modules and integration tests are complete.

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
2. Register callback URL: `https://YOUR-SITE/api/method/zoho_integration.oauth.oauth_callback`
3. In **Zoho Books Settings**, set Client ID and Client Secret.
4. Click **Connect to Zoho**, approve the scopes, then select the Zoho Organization ID from the organization list.
5. Keep **Enable Synchronization** off until setup is complete.
6. Run a dry-run pull first. Test outbound writes in a sandbox before enabling them.

India endpoints: `https://accounts.zoho.in` and `https://www.zohoapis.in`.

## Safety
No automatic deletion, invoice submission, payment allocation or accounting posting is performed. Back up ERPNext and use a separate Zoho test organization before enabling live writes. Never commit OAuth secrets or tokens.
