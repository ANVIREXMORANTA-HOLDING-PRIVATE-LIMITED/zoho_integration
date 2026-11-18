import json
import frappe
from frappe import _
from frappe.utils import now_datetime
from zoho_integration.zoho_client import ZohoBooksClient

def _link_by_zoho(zoho_id):
    return frappe.db.get_value("Zoho Books Document Link",
        {"zoho_module":"contacts","zoho_id":str(zoho_id),"erpnext_doctype":"Supplier"},"name")

def _save_link(supplier_name, zoho_id):
    link_name = _link_by_zoho(zoho_id)
    doc = frappe.get_doc("Zoho Books Document Link", link_name) if link_name else frappe.new_doc("Zoho Books Document Link")
    doc.erpnext_doctype, doc.erpnext_name = "Supplier", supplier_name
    doc.zoho_module, doc.zoho_id = "contacts", str(zoho_id)
    doc.last_synced_at, doc.sync_status = now_datetime(), "Synced"
    doc.save(ignore_permissions=True)

def _supplier_group():
    group = frappe.db.get_single_value("Buying Settings", "default_supplier_group")
    if group and frappe.db.exists("Supplier Group", group):
        return group
    return frappe.db.get_value("Supplier Group", {"is_group":0}, "name", order_by="lft asc")

def _zoho_to_supplier(row, dry_run):
    if row.get("contact_type") not in ("vendor","both"):
        return "skipped"
    zid = str(row["contact_id"])
    link = _link_by_zoho(zid)
    linked = frappe.db.get_value("Zoho Books Document Link", link, "erpnext_name") if link else None
    name = row.get("contact_name") or row.get("company_name") or "Zoho Vendor " + zid
    existing = linked if linked and frappe.db.exists("Supplier",linked) else frappe.db.get_value("Supplier",{"supplier_name":name},"name")
    if dry_run: return "would_update" if existing else "would_create"
    doc = frappe.get_doc("Supplier",existing) if existing else frappe.new_doc("Supplier")
    if not existing:
        group = _supplier_group()
        if not group: frappe.throw(_("Create a non-group Supplier Group before syncing vendors."))
        doc.supplier_group = group
    doc.supplier_name = name
    doc.supplier_type = "Company" if row.get("company_name") else "Individual"
    doc.email_id = row.get("email") or doc.get("email_id")
    doc.mobile_no = row.get("mobile") or doc.get("mobile_no")
    doc.save(ignore_permissions=True)
    _save_link(doc.name,zid)
    return "updated" if existing else "created"

def _erp_to_zoho(doc, client, dry_run, index):
    link_name = frappe.db.get_value("Zoho Books Document Link",
        {"erpnext_doctype":"Supplier","erpnext_name":doc.name,"zoho_module":"contacts"},"name")
    link = frappe.get_doc("Zoho Books Document Link",link_name) if link_name else None
    zid = link.zoho_id if link else index.get((doc.supplier_name or "").casefold())
    payload = {"contact_name":doc.supplier_name,"contact_type":"vendor"}
    if doc.supplier_type == "Company": payload["company_name"] = doc.supplier_name
    if doc.get("email_id"): payload["email"] = doc.email_id
    if doc.get("mobile_no"): payload["mobile"] = doc.mobile_no
    if dry_run: return "would_update" if zid else "would_create"
    if zid:
        client.request("PUT","contacts/"+str(zid),payload=payload)
        action = "updated"
    else:
        result = client.request("POST","contacts",payload=payload)
        zid = str(result.get("contact",{}).get("contact_id") or "")
        if not zid: frappe.throw(_("Zoho did not return a vendor contact ID."))
        action = "created"
    _save_link(doc.name,zid)
    return action

def sync_suppliers(direction="pull", dry_run=True):
    settings = frappe.get_single("Zoho Books Settings")
    log = frappe.new_doc("Zoho Books Sync Log")
    log.entity,log.direction,log.status,log.dry_run = "vendors",direction,"Running",int(bool(dry_run))
    log.started_by = frappe.session.user or "Administrator"
    log.insert(ignore_permissions=True)
    counts = {"read":0,"created":0,"updated":0,"skipped":0}
    try:
        client = ZohoBooksClient(settings)
        if direction in ("pull","both"):
            page = 1
            while True:
                result = client.request("GET","contacts",params={"page":page,"per_page":200,"filter_by":"Status.Active"})
                rows = result.get("contacts",[])
                counts["read"] += len(rows)
                for row in rows:
                    out = _zoho_to_supplier(row,dry_run)
                    key = "created" if out in ("created","would_create") else "updated" if out in ("updated","would_update") else "skipped"
                    counts[key] += 1
                if not result.get("page_context",{}).get("has_more_page"): break
                page += 1
        if direction in ("push","both"):
            index, page = {}, 1
            while True:
                result = client.request("GET","contacts",params={"page":page,"per_page":200})
                for row in result.get("contacts",[]):
                    if row.get("contact_type") in ("vendor","both"):
                        label = (row.get("contact_name") or row.get("company_name") or "").strip().casefold()
                        if label and row.get("contact_id"): index[label] = str(row["contact_id"])
                if not result.get("page_context",{}).get("has_more_page"): break
                page += 1
            for name in frappe.get_all("Supplier",pluck="name"):
                out = _erp_to_zoho(frappe.get_doc("Supplier",name),client,dry_run,index)
                counts["created" if out in ("created","would_create") else "updated"] += 1
        log.records_read,log.records_created,log.records_updated = counts["read"],counts["created"],counts["updated"]
        log.status,log.message = "Success",json.dumps(counts)
    except Exception:
        log.status,log.message = "Failed",frappe.get_traceback()[-3500:]
        frappe.log_error(log.message,"Zoho Books Vendor Sync")
    finally:
        log.completed_on = now_datetime()
        log.save(ignore_permissions=True)
        frappe.db.commit()
    return counts
