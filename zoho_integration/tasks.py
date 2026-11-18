import frappe

def enqueue_scheduled_sync():
    settings=frappe.get_single("Zoho Books Settings")
    if not (settings.enabled and settings.connected and settings.scheduled_sync):
        return
    for method in (
        "zoho_integration.sync.sync_customers",
        "zoho_integration.suppliers.sync_suppliers",
        "zoho_integration.items.sync_items",
        "zoho_integration.invoices.sync_invoices",
    ):
        frappe.enqueue(method,queue="long",direction="pull",dry_run=False,enqueue_after_commit=True)
