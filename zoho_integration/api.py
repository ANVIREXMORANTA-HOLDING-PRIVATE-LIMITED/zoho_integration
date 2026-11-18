import frappe
from frappe import _

@frappe.whitelist()
def get_authorization_url():
    from zoho_integration.oauth import get_authorization_url
    return get_authorization_url()

@frappe.whitelist()
def test_connection():
    settings = frappe.get_single("Zoho Books Settings")
    settings.check_permission("read")
    from zoho_integration.zoho_client import ZohoBooksClient
    return ZohoBooksClient(settings).get_organizations()

@frappe.whitelist()
def sync_customers(direction="pull", dry_run=1):
    settings = frappe.get_single("Zoho Books Settings")
    settings.check_permission("write")
    if not settings.enabled:
        frappe.throw(_("Enable synchronization in Zoho Books Settings first."))
    if direction not in ("pull", "push", "both"):
        frappe.throw(_("Direction must be pull, push or both."))
    if direction in ("push", "both") and not settings.allow_outbound_writes:
        frappe.throw(_("Enable outbound writes only after validating the sandbox mappings."))
    frappe.enqueue("zoho_integration.sync.sync_customers", queue="long",
                   direction=direction, dry_run=bool(int(dry_run)), enqueue_after_commit=True)
    return {"queued": True, "direction": direction, "dry_run": bool(int(dry_run))}
