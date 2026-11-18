# Zoho Books Integration for ERPNext

**Development version:** 0.4.0  
**Target:** Frappe / ERPNext v16 and Zoho Books India  
**App name:** `zoho_integration`

A controlled integration app for connecting one ERPNext site to a Zoho Books organization. The app includes OAuth connection management, background synchronization, dry-run previews, external document links and sync logs. It is an evolving integration—not a complete accounting or inventory connector yet.

> **Production warning:** Do not treat a successful OAuth connection or dashboard load as proof that accounting synchronization is production-ready. Validate every workflow in a separate ERPNext test site and Zoho Books test organization, back up production, and reconcile sample documents before enabling live jobs.

## 1. Current feature status

| Area | Current implementation | Important limitation |
|---|---|---|
| OAuth 2.0 | India accounts domain, authorization callback, encrypted access/refresh token storage, refresh support | Re-authorize after changing scopes |
| Organization | Organization discovery and API connection test | Select the correct legal entity manually |
| Customers | Pull and push contact records; external ID links; dry run | Field mapping is basic; duplicate matching needs business review |
| Suppliers | Vendor contact synchronization | Not a full supplier accounting workflow |
| Items | Item synchronization | Imported items are deliberately non-stock; no warehouse/quantity ledger sync |
| Sales invoices | Restricted pull to ERPNext draft and push of eligible ERPNext draft to Zoho draft | Tax, discount, shipping, foreign currency and complex accounting cases are skipped; no automatic submission |
| Sync operations | Background queue, dry-run flag, sync log and link records | Review every failed/skipped record |
| Dashboard | Connection status, token-storage indicator, settings, API test, log shortcut, four inbound preview actions, operational flags and feature coverage | It does not replace the settings form or accounting review |

### Not implemented (do not assume these features exist)

- Purchase bills / vendor bills and purchase invoice posting
- Customer receipts, supplier payments, payment allocations or bank reconciliation
- Credit notes, refunds and debit notes
- Complete Indian GST treatment: intra/inter-state logic, CGST, SGST, IGST, cess, HSN/SAC, place of supply, reverse charge, TDS/TCS
- Stock quantities, warehouses, stock entries, batches, serial numbers or inventory valuation
- Multi-currency conversion, exchange-rate handling and realized/unrealized gain/loss
- Webhooks, conflict-resolution UI, full retry/dead-letter management or end-to-end reconciliation
- Automatic submit/approve/post workflows

These require additional implementation and test coverage before they can be safely used for accounting.

## 2. Dashboard

After installation, open Desk and navigate to:

```
/app/zoho-books-dashboard
```

The **Zoho Books Control Center** contains:

- Connection and encrypted token-storage status
- Selected organization and token expiry
- Connect / re-authorize and live connection test
- Shortcut to Zoho Books Settings
- Shortcut to Zoho Books Sync Log
- Dry-run preview actions for customers, suppliers, items and sales invoices
- Visibility of synchronization, scheduled-pull and outbound-write flags
- Clear distinction between implemented, limited and not-yet-implemented workflows

The dashboard preview buttons always request `direction="pull"` and `dry_run=1`. They do not enable outbound writes.

## 3. Frappe Cloud installation

1. Open the target bench group in Frappe Cloud.
2. Confirm that the bench supports custom apps.
3. Add this GitHub repository to the bench group:
   `ANVIREXMORANTA-HOLDING-PRIVATE-LIMITED/zoho_integration`.
4. Select the intended branch (normally `main`) and add the app.
5. Deploy the bench-group update.
6. Open the target site and install the app `zoho_integration`.
7. Run the site migration/update task if Frappe Cloud does not run it automatically.
8. Confirm the app is listed under Installed Apps.
9. Reload Desk and open `/app/zoho-books-dashboard`.

Frappe Cloud documentation: https://docs.frappe.io/cloud/benches/custom-app

## 4. Zoho Books India OAuth setup

### 4.1 Create the OAuth client

Create a Server-based application in the Zoho API Console for the **India data center**.

Register the exact callback URL for your site:

```
https://YOUR-SITE/api/method/zoho_integration.oauth.oauth_callback
```

Do not use the callback for a different app or a different site.

### 4.2 Configure Zoho Books Settings

Open **Zoho Books Settings** in ERPNext and configure:

| Setting | Value / instruction |
|---|---|
| ERPNext Company | Select the company that owns the accounting data |
| Client ID | From Zoho API Console |
| Client Secret | From Zoho API Console; store only in the Password field |
| Accounts Domain | `https://accounts.zoho.in` |
| API Domain | `https://www.zohoapis.in` |
| OAuth Scopes | Use the scopes required by the implemented contacts, items and invoices operations |
| Organization ID | Select the correct Zoho Books legal entity after organization discovery |
| Enable Synchronization | Keep disabled until setup and connection verification are complete |
| Scheduled Pull Sync | Keep disabled during validation |
| Allow ERPNext to Zoho Writes | Keep disabled until outbound mapping tests are signed off |

Never paste Client Secret, access token, refresh token or OAuth authorization code into chat, issue trackers or logs.

### 4.3 Connect and verify

1. Save the settings.
2. Click **Connect / Re-authorize** from the dashboard (or the connection action in Settings).
3. Sign in to Zoho India and approve the requested scopes.
4. Return to ERPNext.
5. Click **Test connection**.
6. Confirm that the expected organizations are returned.
7. Select the correct Zoho Organization ID in Settings and save.
8. Confirm the dashboard reports token storage and API connection correctly.

If scopes are changed later, re-authorize the application so Zoho grants the updated permissions.

## 5. ERPNext prerequisites

Before any real inbound sync, verify:

- The target Company and its default currency
- At least one non-group Customer Group and Territory
- At least one non-group Supplier Group
- Item Group and stock UOM defaults
- Item Defaults and income accounts for invoice items
- Company default receivable account
- Customer and supplier naming/duplicate policy
- User permissions for System Manager and the integration settings/log DocTypes

Do not create arbitrary accounts or tax templates just to make an import pass. Map them to the approved chart of accounts and tax policy for the legal entity.

## 6. Safe validation sequence

### Phase A — connection only

1. Complete OAuth and Test Connection.
2. Verify the organization ID and company.
3. Keep scheduled sync disabled.
4. Keep outbound writes disabled.
5. Do not run a live sync yet.

### Phase B — dry-run previews

1. Open the dashboard.
2. Run **Preview customers**.
3. Open **Zoho Books Sync Log** and wait for the background job.
4. Review status, records read, create/update counts and error text.
5. Repeat for suppliers, items and sales invoices.
6. Resolve missing groups, territories, UOMs, account defaults and duplicate matches.
7. Confirm that every preview log has `dry_run = 1`.

Dry runs should not create or update ERPNext business documents. They may create a sync-log record for audit purposes.

### Phase C — controlled inbound test

Only after dry-run review:

1. Take a database and files backup.
2. Use a non-production test site and Zoho test organization whenever possible.
3. Enable synchronization only when ready to run a real inbound job.
4. Start with one low-risk entity and a small data set.
5. Review the created/updated ERPNext documents and their external link records.
6. Reconcile counts and sample field values in both systems.
7. Repeat for other entity types only after the first test passes.

A non-dry-run pull can create or update ERPNext records. It is not a preview.

### Phase D — outbound test

Outbound writes are blocked unless **Allow ERPNext to Zoho Writes** is enabled. Do not enable it in production just to test the button.

Use a test organization and test company. Validate contact, item and draft invoice payloads, duplicate behavior, currency, dates, tax handling and link records. The current invoice exporter is restricted to eligible drafts and does not submit them.

### Phase E — scheduling

The hourly scheduler checks the settings flags. When synchronization is enabled and **Scheduled Pull Sync** is selected, it queues non-dry-run inbound pulls for customers, suppliers, items and sales invoices. That can create/update ERPNext records automatically.

Therefore, leave **Scheduled Pull Sync** disabled until the exact inbound behavior has been tested, approved and monitored. Scheduling is not a substitute for a reconciliation process.

## 7. Sync logs and troubleshooting

Open **Zoho Books Sync Log** from the dashboard or the Desk list.

Review:

- Entity and direction
- Dry Run flag
- Status
- Records read, created and updated
- Started/completed timestamps
- Error message / traceback

Common causes:

| Symptom | Checks |
|---|---|
| OAuth callback error | Callback URL, India data center, Client ID and client secret |
| 401 / unauthorized | Re-authorize and confirm scopes; do not share tokens |
| No organization selected | Run Test Connection and save the intended organization ID |
| Token not stored | Check site encryption key and Frappe Password field storage |
| Missing Customer Group / Territory | Create valid non-group defaults before a real customer pull |
| Invoice skipped | Check customer/item links, currency, taxes, discounts, shipping and account defaults |
| Job queued but no result | Check RQ workers, background job queue and Error Log |
| Select option validation error | Confirm DocType Select options contain newline-separated choices and run migration |

Do not retry a failed live job blindly. First inspect the log and confirm whether any records were already written.

## 8. Security and operational safeguards

- OAuth tokens are stored using Frappe encrypted Password fields.
- Never log or display token values.
- Keep outbound writes disabled until a test organization proves the mappings.
- Keep scheduled sync disabled until inbound writes are approved.
- Do not auto-submit invoices or bills.
- Back up the site before real synchronization.
- Limit settings and sync-log access to authorized ERPNext administrators.
- Review the sync log after each job.
- Do not assume a successful connection means the accounting data is reconciled.
- Preserve unrelated integrations and site configuration when deploying updates.

## 9. Development and tests

Run these checks in a development environment with the app installed:

```bash
python -m compileall -q zoho_integration
python -m unittest discover -s tests -v
```

These checks validate Python syntax and the repository's unit tests only. They do **not** prove live Zoho API behavior, production accounting correctness, GST compliance or safe end-to-end synchronization.

## 10. Roadmap for a complete accounting connector

The following are separate development milestones, not currently available features:

1. Configuration and mapping center for company, branches, warehouses, tax templates, accounts, UOM and item groups.
2. Purchase bills with vendor, line, tax, currency and duplicate validation.
3. Customer receipts and supplier payments with allocation and bank/account mapping.
4. Credit/debit notes, refunds and payment reversals.
5. Indian GST engine and validation for CGST/SGST/IGST, HSN/SAC, place of supply and reverse charge.
6. Inventory ledger integration with warehouse, stock entry, batch/serial and valuation safeguards.
7. Reconciliation center, conflict review, retry queue and idempotency controls.
8. Webhooks and incremental sync with replay protection.
9. Automated tests using isolated Zoho test organizations and ERPNext test sites.
10. Controlled submit/post workflows with explicit approval and audit history.

Each milestone must include mapping design, test coverage, migration review and reconciliation before it is enabled on a live company.

## 11. Marketplace readiness

Marketplace publication requires a compatible public repository, valid license, publisher details, complete documentation, automated tests and Frappe Cloud review. This repository is not declared marketplace-ready or production-certified.

## Support

Replace the placeholder support email in `hooks.py` before public distribution. Never commit credentials, customer records, database backups or production exports.
