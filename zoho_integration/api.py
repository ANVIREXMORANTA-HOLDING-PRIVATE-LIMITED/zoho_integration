import frappe
from frappe import _

def _queue_sync(method, direction, dry_run):
    settings=frappe.get_single("Zoho Books Settings")
    settings.check_permission("write")
    if not settings.enabled:
        frappe.throw(_("Enable synchronization in Zoho Books Settings first."))
    if direction not in ("pull","push","both"):
        frappe.throw(_("Direction must be pull, push or both."))
    dry_run=bool(int(dry_run))
    if direction in ("push","both") and not dry_run and not settings.allow_outbound_writes:
        frappe.throw(_("Enable outbound writes only after validating mappings in a test organization."))
    frappe.enqueue(method,queue="long",direction=direction,dry_run=dry_run,enqueue_after_commit=True)
    return {"queued":True,"direction":direction,"dry_run":dry_run}

@frappe.whitelist()
def get_authorization_url():
    from zoho_integration.oauth import get_authorization_url
    return get_authorization_url()

@frappe.whitelist()
def test_connection():
    settings=frappe.get_single("Zoho Books Settings")
    settings.check_permission("read")
    from zoho_integration.zoho_client import ZohoBooksClient
    return ZohoBooksClient(settings).get_organizations()

@frappe.whitelist()
def sync_customers(direction="pull",dry_run=1):
    return _queue_sync("zoho_integration.sync.sync_customers",direction,dry_run)

@frappe.whitelist()
def sync_suppliers(direction="pull",dry_run=1):
    return _queue_sync("zoho_integration.suppliers.sync_suppliers",direction,dry_run)

@frappe.whitelist()
def sync_items(direction="pull",dry_run=1):
    return _queue_sync("zoho_integration.items.sync_items",direction,dry_run)

@frappe.whitelist()
def sync_invoices(direction="pull",dry_run=1):
    return _queue_sync("zoho_integration.invoices.sync_invoices",direction,dry_run)
