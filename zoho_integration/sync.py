import hashlib, json
import frappe
from frappe import _
from frappe.utils import now_datetime
from zoho_integration.zoho_client import ZohoBooksClient

def _hash(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()

def _find_link(zoho_id):
    return frappe.db.get_value("Zoho Books Document Link", {"zoho_id": str(zoho_id), "zoho_module":"contacts"}, "name")

def _save_link(doctype, docname, zoho_id, payload_hash):
    link = _find_link(zoho_id)
    if not link:
        link = frappe.new_doc("Zoho Books Document Link")
        link.zoho_module = "contacts"
        link.zoho_id = str(zoho_id)
    link.erpnext_doctype = doctype
    link.erpnext_name = docname
    link.last_synced_at = now_datetime()
    link.last_synced_hash = payload_hash
    link.sync_status = "Synced"
    link.save(ignore_permissions=True)

def _zoho_contact_to_erp(contact, dry_run):
    # Zoho contact types include customer/vendor/both. ERPNext Customer is created
    # for customer-capable contacts; vendor-only contacts are handled in the vendor phase.
    ctype = contact.get("contact_type", "customer")
    if ctype not in ("customer", "both"):
        return "skipped"
    zoho_id = str(contact["contact_id"])
    link = _find_link(zoho_id)
    customer_name = frappe.db.get_value("Zoho Books Document Link", link, "erpnext_name") if link else None
    name = contact.get("contact_name") or contact.get("company_name") or ("Zoho " + zoho_id)
    if dry_run:
        return "would_update" if customer_name else "would_create"
    if customer_name and frappe.db.exists("Customer", customer_name):
        doc = frappe.get_doc("Customer", customer_name)
    else:
        existing = frappe.db.get_value("Customer", {"customer_name": name}, "name")
        doc = frappe.get_doc("Customer", existing) if existing else frappe.new_doc("Customer")
        if not existing:
            doc.customer_name = name
            doc.customer_type = "Company" if contact.get("company_name") else "Individual"
            doc.customer_group = frappe.db.get_single_value("Selling Settings", "customer_group") or "All Customer Groups"
            doc.territory = frappe.db.get_single_value("Selling Settings", "territory") or "All Territories"
    doc.customer_name = name
    doc.customer_type = "Company" if contact.get("company_name") else "Individual"
    doc.save(ignore_permissions=True)
    _save_link("Customer", doc.name, zoho_id, _hash(contact))
    return "updated" if customer_name else "created"

def _erp_customer_to_zoho(customer, client, dry_run):
    link_name = frappe.db.get_value("Zoho Books Document Link",
        {"erpnext_doctype":"Customer","erpnext_name":customer.name,"zoho_module":"contacts"},"name")
    payload = {"contact_name": customer.customer_name, "contact_type":"customer"}
    if customer.customer_type == "Company":
        payload["company_name"] = customer.customer_name
    if customer.get("email_id"):
        payload["email"] = customer.email_id
    if customer.get("mobile_no"):
        payload["mobile"] = customer.mobile_no
    if dry_run:
        return "would_update" if link_name else "would_create"
    if link_name:
        link = frappe.get_doc("Zoho Books Document Link", link_name)
        result = client.request("PUT", "contacts/" + link.zoho_id, payload=payload)
        zoho_id = link.zoho_id
    else:
        result = client.request("POST", "contacts", payload=payload)
        zoho_id = str(result.get("contact",{}).get("contact_id") or "")
        if not zoho_id:
            frappe.throw(_("Zoho did not return a contact ID."))
    _save_link("Customer", customer.name, zoho_id, _hash(payload))
    return "updated" if link_name else "created"

def sync_customers(direction="pull", dry_run=True):
    s = frappe.get_single("Zoho Books Settings")
    log = frappe.new_doc("Zoho Books Sync Log")
    log.entity, log.direction, log.status, log.dry_run = "contacts", direction, "Running", int(bool(dry_run))
    log.started_by = frappe.session.user if frappe.session.user else "Administrator"
    log.insert(ignore_permissions=True)
    counts = {"read":0,"created":0,"updated":0,"skipped":0}
    try:
        client = ZohoBooksClient(s)
        if direction in ("pull","both"):
            page = 1
            while True:
                result = client.request("GET","contacts",params={"page":page,"per_page":200})
                rows = result.get("contacts",[])
                counts["read"] += len(rows)
                for row in rows:
                    outcome = _zoho_contact_to_erp(row,dry_run)
                    counts["created" if outcome in ("created","would_create") else "updated" if outcome in ("updated","would_update") else "skipped"] += 1
                if not result.get("page_context",{}).get("has_more_page"):
                    break
                page += 1
        if direction in ("push","both"):
            for name in frappe.get_all("Customer", pluck="name"):
                outcome = _erp_customer_to_zoho(frappe.get_doc("Customer",name),client,dry_run)
                counts["created" if outcome in ("created","would_create") else "updated"] += 1
        log.records_read = counts["read"]
        log.records_created = counts["created"]
        log.records_updated = counts["updated"]
        log.status = "Success"
        log.message = json.dumps(counts)
    except Exception:
        log.status = "Failed"
        log.message = frappe.get_traceback()[-3500:]
        frappe.log_error(log.message, "Zoho Books Contact Sync")
    finally:
        log.completed_on = now_datetime()
        log.save(ignore_permissions=True)
        frappe.db.commit()
    return counts
