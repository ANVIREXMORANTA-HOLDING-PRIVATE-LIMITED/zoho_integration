# Zoho Books Integration for ERPNext

A Frappe app for controlled, two-way synchronization between Zoho Books (India data center) and ERPNext v16.

## Implemented modules (development release 0.3.0)
- OAuth 2.0 authorization-code connection and token refresh.
- Zoho Books India endpoints and organization discovery.
- Customers: Zoho contacts (customer/both) ↔ ERPNext Customer.
- Vendors: Zoho contacts (vendor/both) ↔ ERPNext Supplier.
- Items: Zoho Books items ↔ ERPNext Item. Imported items are deliberately marked non-stock until inventory and warehouse mapping is configured.
- Sales invoices: imports eligible Zoho invoices as ERPNext draft Sales Invoices and exports eligible ERPNext draft Sales Invoices as Zoho drafts.
- External ID link records, pagination, background jobs, dry-run actions and sync logs.

## Accounting safety limits
This is an early integration build, not yet a production-ready accounting connector. Invoice synchronization intentionally skips records with taxes, discounts, shipping adjustments, foreign currency, missing customer/item links or missing ERPNext income/receivable accounts. It never submits ERPNext invoices or marks Zoho invoices as sent. Purchase bills, payments, inventory quantities, tax/GST mapping, multi-currency, webhooks, conflict resolution and automated regression tests against a live Zoho sandbox remain future work.

Run a dry run first, use a separate Zoho test organization and ERPNext test site, back up your data, and review all created drafts before production use.

## Frappe Cloud installation
1. In Frappe Cloud, open the target site's bench group.
2. Confirm the bench is a **private bench group** that supports custom apps.
3. Open **Apps → Add App → Add from GitHub**.
4. Connect GitHub and grant Frappe Cloud access to this repository.
5. Select this repository and the tested release branch, then click **Validate App** and **Add App**.
6. Deploy the bench-group update.
7. Open the target site, choose **Install App**, and install `zoho_integration`.
8. Run the site migration/update task from Frappe Cloud if prompted; confirm the app appears in Installed Apps.

Frappe Cloud custom-app guide: https://docs.frappe.io/cloud/benches/custom-app

## Configure Zoho Books India
1. Create a Zoho Books server-based OAuth client in the India data center.
2. Register this exact callback URL: `https://YOUR-SITE/api/method/zoho_integration.oauth.oauth_callback`
3. In **Zoho Books Settings**, enter the Client ID and Client Secret. Keep the India domains:
   - Accounts: `https://accounts.zoho.in`
   - API: `https://www.zohoapis.in`
4. Save settings and click **Connect to Zoho**. Approve the requested contact, item and invoice scopes.
5. Click **Test Connection**, then copy the correct Organization ID into settings.
6. Enable synchronization only after verifying company, customer group, supplier group, item group, UOM, receivable and income account setup.

The default OAuth scope list is expanded in this release. If the app was previously authorized, reconnect Zoho to grant the new scopes.

## Recommended validation sequence
1. Test on a staging site and a Zoho Books test organization.
2. Run dry-run pulls for customers, vendors and items.
3. Review mappings and sync logs; create missing ERPNext groups and UOMs.
4. Run actual pulls for customers, vendors and items.
5. Run dry-run invoice import/export. Resolve all skipped invoices before enabling outbound writes.
6. Enable outbound writes and test with one non-taxed draft customer, vendor, item and sales invoice.
7. Verify Zoho IDs and ERPNext document links, totals, dates and duplicate behavior.
8. Only then schedule recurring pull sync.

## Development checks
```bash
python -m compileall -q zoho_integration
python -m unittest discover -s tests -v
```

## Marketplace
Marketplace submission requires a public GitHub repository, compatible open-source license, a valid Frappe app, passing CI, publisher setup, complete listing details and Frappe Cloud review. Keep secrets, access tokens and refresh tokens out of Git.

## Support and security
Replace the placeholder support email in `hooks.py` before publishing. Never commit OAuth credentials, customer data or production exports.
