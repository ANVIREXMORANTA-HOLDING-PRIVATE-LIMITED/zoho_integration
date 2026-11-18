import hashlib
import json
import frappe
from frappe import _
from frappe.utils import now_datetime
from zoho_integration.zoho_client import ZohoBooksClient

def _hash(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()

def _find_link(zoho_id):
    return frappe.db.get_value("Zoho Books Document Link",
        {"zoho_id": str(zoho_id), "zoho_module": "contacts", "erpnext_doctype": "Customer"}, "name")

def _save_link(doctype, docname, zoho_id, payload_hash):
    link_name = _find_link(zoho_id)
    link = frappe.get_doc("Zoho Books Document Link", link_name) if link_name else frappe.new_doc("Zoho Books Document Link")
    link.erpnext_doctype = doctype
    link.erpnext_name = docname
    link.zoho_module = "contacts"
    link.zoho_id = str(zoho_id)
    link.last_synced_at = now_datetime()
    link.last_synced_hash = payload_hash
    link.sync_status = "Synced"
    link.save(ignore_permissions=True)

def _contact_payload_from_erp(customer):
    payload = {"contact_name": customer.customer_name, "contact_type": "customer"}
    if customer.customer_type == "Company":
        payload["company_name"] = customer.customer_name
    if customer.get("email_id"):
        payload["email"] = customer.email_id
    if customer.get("mobile_no"):
        payload["mobile"] = customer.mobile_no
    return payload

def _contact_payload_from_zoho(contact):
    return {
        "contact_name": contact.get("contact_name") or contact.get("company_name") or "",
        "contact_type": "customer",
        "company_name": contact.get("company_name") or "",
        "email": contact.get("email") or "",
        "mobile": contact.get("mobile") or "",
    }

def _zoho_contact_to_erp(contact, dry_run):
    if contact.get("contact_type", "customer") not in ("customer", "both"):
        return "skipped"
    zoho_id = str(contact["contact_id"])
    link_name = _find_link(zoho_id)
    linked_customer = frappe.db.get_value("Zoho Books Document Link", link_name, "erpnext_name") if link_name else None
    name = contact.get("contact_name") or contact.get("company_name") or ("Zoho " + zoho_id)
    existing = linked_customer if linked_customer and frappe.db.exists("Customer", linked_customer) else frappe.db.get_value("Customer", {"customer_name": name}, "name")
    if dry_run:
        return "would_update" if existing else "would_create"
    if existing:
        doc = frappe.get_doc("Customer", existing)
    else:
        doc = frappe.new_doc("Customer")
        doc.customer_group = frappe.db.get_value("Customer Group", {"is_group": 0}, "name", order_by="lft asc")
        doc.territory = frappe.db.get_value("Territory", {"is_group": 0}, "name", order_by="lft asc")
        if not doc.customer_group or not doc.territory:
            frappe.throw(_("Create at least one non-group Customer Group and Territory before syncing."))
    doc.customer_name = name
    doc.customer_type = "Company" if contact.get("company_name") else "Individual"
    doc.email_id = contact.get("email") or doc.get("email_id")
    doc.mobile_no = contact.get("mobile") or doc.get("mobile_no")
    doc.save(ignore_permissions=True)
    _save_link("Customer", doc.name, zoho_id, _hash(_contact_payload_from_zoho(contact)))
    return "updated" if existing else "created"

def _erp_customer_to_zoho(customer, client, dry_run, contact_index):
    link_name = frappe.db.get_value("Zoho Books Document Link",
        {"erpnext_doctype":"Customer", "erpnext_name":customer.name, "zoho_module":"contacts"}, "name")
    payload = _contact_payload_from_erp(customer)
    link = frappe.get_doc("Zoho Books Document Link", link_name) if link_name else None
    zoho_id = link.zoho_id if link else contact_index.get((customer.customer_name or "").strip().casefold())
    if dry_run:
        return "would_update" if zoho_id else "would_create"
    if zoho_id:
        client.request("PUT", "contacts/" + str(zoho_id), payload=payload)
        outcome = "updated"
    else:
        result = client.request("POST", "contacts", payload=payload)
        zoho_id = str(result.get("contact", {}).get("contact_id") or "")
        if not zoho_id:
            frappe.throw(_("Zoho did not return a contact ID."))
        outcome = "created"
    _save_link("Customer", customer.name, zoho_id, _hash(payload))
    return outcome

def sync_customers(direction="pull", dry_run=True):
    settings = frappe.get_single("Zoho Books Settings")
    log = frappe.new_doc("Zoho Books Sync Log")
    log.entity, log.direction, log.status, log.dry_run = "contacts", direction, "Running", int(bool(dry_run))
    log.started_by = frappe.session.user or "Administrator"
    log.insert(ignore_permissions=True)
    counts = {"read":0, "created":0, "updated":0, "skipped":0}
    try:
        client = ZohoBooksClient(settings)
        if direction in ("pull", "both"):
            page = 1
            while True:
                result = client.request("GET", "contacts", params={"page":page, "per_page":200})
                rows = result.get("contacts", [])
                counts["read"] += len(rows)
                for row in rows:
                    result_key = _zoho_contact_to_erp(row, dry_run)
                    if result_key in ("created", "would_create"): counts["created"] += 1
                    elif result_key in ("updated", "would_update"): counts["updated"] += 1
                    else: counts["skipped"] += 1
                if not result.get("page_context", {}).get("has_more_page"):
                    break
                page += 1
        if direction in ("push", "both"):
            # Build one remote name index before writes; avoids one GET per ERP customer.
            contact_index = {}
            page = 1
            while True:
                result = client.request("GET", "contacts", params={"page":page, "per_page":200})
                for row in result.get("contacts", []):
                    label = (row.get("contact_name") or row.get("company_name") or "").strip().casefold()
                    if label and row.get("contact_id"):
                        contact_index[label] = str(row["contact_id"])
                if not result.get("page_context", {}).get("has_more_page"): break
                page += 1
            for customer_name in frappe.get_all("Customer", pluck="name"):
                result_key = _erp_customer_to_zoho(frappe.get_doc("Customer", customer_name), client, dry_run, contact_index)
                if result_key in ("created", "would_create"): counts["created"] += 1
                else: counts["updated"] += 1
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
