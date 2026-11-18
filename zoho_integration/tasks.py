import frappe

def enqueue_scheduled_sync():
    settings = frappe.get_single("Zoho Books Settings")
    if settings.enabled and settings.connected and settings.scheduled_sync:
        frappe.enqueue("zoho_integration.sync.sync_customers", queue="long", direction="pull", dry_run=False)
