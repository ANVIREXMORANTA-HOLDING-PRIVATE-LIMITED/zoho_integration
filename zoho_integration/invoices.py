import json
import frappe
from frappe import _
from frappe.utils import now_datetime, getdate
from zoho_integration.zoho_client import ZohoBooksClient

def _link(doctype, erp_name=None, zoho_id=None, module="invoices"):
    filters={"zoho_module":module,"erpnext_doctype":doctype}
    if erp_name: filters["erpnext_name"]=erp_name
    if zoho_id: filters["zoho_id"]=str(zoho_id)
    return frappe.db.get_value("Zoho Books Document Link",filters,"name")

def _save_link(doctype,erp_name,zid):
    name=_link(doctype,zoho_id=zid)
    doc=frappe.get_doc("Zoho Books Document Link",name) if name else frappe.new_doc("Zoho Books Document Link")
    doc.erpnext_doctype,doc.erpnext_name=doctype,erp_name
    doc.zoho_module,doc.zoho_id="invoices",str(zid)
    doc.last_synced_at,doc.sync_status=now_datetime(),"Synced"
    doc.save(ignore_permissions=True)

def _reject_if_taxed_or_discounted(data):
    if float(data.get("tax_total") or 0) or data.get("taxes"):
        frappe.throw(_("Invoice has Zoho tax lines. Configure and validate tax mapping before importing."))
    if float(data.get("discount_amount") or 0) or data.get("discount") or float(data.get("shipping_charge") or 0):
        frappe.throw(_("Invoice has discount or shipping adjustments. These require explicit mapping before sync."))
    for row in data.get("line_items",[]):
        if row.get("tax_id") or float(row.get("tax_amount") or 0) or row.get("discount"):
            frappe.throw(_("Invoice line has tax or discount. This invoice is held for mapping review."))

def _company_currency(company):
    return frappe.get_cached_value("Company",company,"default_currency")

def _income_account(item_code,company):
    account=frappe.db.get_value("Item Default",{"parent":item_code,"company":company},"income_account")
    if not account:
        frappe.throw(_("Item {0} has no income account for company {1}.").format(item_code,company))
    return account

def _pull_one(client,summary,settings,dry_run):
    zid=str(summary["invoice_id"])
    link_name=_link("Sales Invoice",zoho_id=zid)
    linked=frappe.db.get_value("Zoho Books Document Link",link_name,"erpnext_name") if link_name else None
    if linked and frappe.db.exists("Sales Invoice",linked): return "skipped"
    detail=client.request("GET","invoices/"+zid).get("invoice",{})
    if not detail: frappe.throw(_("Zoho invoice {0} returned no detail.").format(zid))
    _reject_if_taxed_or_discounted(detail)
    company=settings.company
    currency=detail.get("currency_code") or _company_currency(company)
    if currency != _company_currency(company):
        frappe.throw(_("Invoice currency {0} differs from ERPNext company currency {1}; FX mapping is not enabled.").format(currency,_company_currency(company)))
    contact_id=str(detail.get("customer_id") or "")
    customer_link=_link("Customer",zoho_id=contact_id,module="contacts")
    customer=frappe.db.get_value("Zoho Books Document Link",customer_link,"erpnext_name") if customer_link else None
    if not customer or not frappe.db.exists("Customer",customer):
        frappe.throw(_("Zoho customer {0} is not linked to an ERPNext Customer. Sync customers first.").format(contact_id))
    rows=[]
    for line in detail.get("line_items",[]):
        item_id=str(line.get("item_id") or "")
        item_link=frappe.db.get_value("Zoho Books Document Link",{"zoho_module":"items","zoho_id":item_id,"erpnext_doctype":"Item"},"name")
        item=frappe.db.get_value("Zoho Books Document Link",item_link,"erpnext_name") if item_link else None
        if not item or not frappe.db.exists("Item",item):
            frappe.throw(_("Zoho item {0} is not linked to an ERPNext Item. Sync items first.").format(item_id))
        rows.append({"item_code":item,"qty":float(line.get("quantity") or 0),"rate":float(line.get("rate") or 0),
                     "description":line.get("description") or line.get("name") or item,
                     "income_account":_income_account(item,company)})
    if not rows: frappe.throw(_("Invoice has no line items."))
    if dry_run: return "would_create"
    doc=frappe.new_doc("Sales Invoice")
    doc.company,doc.customer=company,customer
    doc.posting_date=getdate(detail.get("date") or detail.get("invoice_date") or now_datetime())
    if detail.get("due_date"): doc.due_date=getdate(detail["due_date"])
    doc.currency=currency
    doc.debit_to=frappe.get_cached_value("Company",company,"default_receivable_account")
    doc.set("items",rows)
    doc.insert(ignore_permissions=True)
    _save_link("Sales Invoice",doc.name,zid)
    return "created"

def _push_one(doc,client,dry_run):
    if doc.docstatus != 0:
        return "skipped"
    if doc.taxes or float(doc.get("discount_amount") or 0) or float(doc.get("write_off_amount") or 0):
        frappe.throw(_("Sales Invoice {0} has taxes, discount or write-off. Outbound mapping is required.").format(doc.name))
    if doc.currency != _company_currency(doc.company):
        frappe.throw(_("Sales Invoice {0} uses foreign currency; FX mapping is not enabled.").format(doc.name))
    customer_link=_link("Customer",erp_name=doc.customer,module="contacts")
    customer_id=frappe.db.get_value("Zoho Books Document Link",customer_link,"zoho_id") if customer_link else None
    if not customer_id: frappe.throw(_("Customer {0} is not linked to Zoho Books.").format(doc.customer))
    lines=[]
    for row in doc.items:
        item_link=frappe.db.get_value("Zoho Books Document Link",{"zoho_module":"items","erpnext_doctype":"Item","erpnext_name":row.item_code},"name")
        item_id=frappe.db.get_value("Zoho Books Document Link",item_link,"zoho_id") if item_link else None
        if not item_id: frappe.throw(_("Item {0} is not linked to Zoho Books.").format(row.item_code))
        lines.append({"item_id":item_id,"quantity":float(row.qty),"rate":float(row.rate),
                      "description":row.description or row.item_name or row.item_code})
    payload={"customer_id":customer_id,"date":str(doc.posting_date),"line_items":lines}
    if doc.due_date: payload["due_date"]=str(doc.due_date)
    if doc.po_no: payload["reference_number"]=doc.po_no
    link_name=_link("Sales Invoice",erp_name=doc.name)
    link=frappe.get_doc("Zoho Books Document Link",link_name) if link_name else None
    if dry_run: return "would_update" if link else "would_create"
    if link:
        client.request("PUT","invoices/"+str(link.zoho_id),payload=payload)
        action="updated"
        zid=link.zoho_id
    else:
        result=client.request("POST","invoices",payload=payload)
        zid=str(result.get("invoice",{}).get("invoice_id") or "")
        if not zid: frappe.throw(_("Zoho did not return an invoice ID."))
        action="created"
    _save_link("Sales Invoice",doc.name,zid)
    return action

def sync_invoices(direction="pull",dry_run=True):
    settings=frappe.get_single("Zoho Books Settings")
    log=frappe.new_doc("Zoho Books Sync Log")
    log.entity,log.direction,log.status,log.dry_run="sales_invoices",direction,"Running",int(bool(dry_run))
    log.started_by=frappe.session.user or "Administrator"
    log.insert(ignore_permissions=True)
    counts={"read":0,"created":0,"updated":0,"skipped":0}
    try:
        client=ZohoBooksClient(settings)
        if direction in ("pull","both"):
            page=1
            while True:
                result=client.request("GET","invoices",params={"page":page,"per_page":100})
                rows=result.get("invoices",[])
                counts["read"]+=len(rows)
                for row in rows:
                    try:
                        out=_pull_one(client,row,settings,dry_run)
                    except Exception as exc:
                        frappe.log_error(str(exc),"Zoho invoice import "+str(row.get("invoice_number") or row.get("invoice_id")))
                        counts["skipped"]+=1
                        continue
                    counts["created" if out in ("created","would_create") else "skipped"]+=1
                if not result.get("page_context",{}).get("has_more_page"): break
                page+=1
        if direction in ("push","both"):
            for name in frappe.get_all("Sales Invoice",filters={"company":settings.company,"docstatus":0},pluck="name"):
                try:
                    out=_push_one(frappe.get_doc("Sales Invoice",name),client,dry_run)
                except Exception as exc:
                    frappe.log_error(str(exc),"ERPNext invoice export "+name)
                    counts["skipped"]+=1
                    continue
                counts["created" if out in ("created","would_create") else "updated" if out in ("updated","would_update") else "skipped"]+=1
        log.records_read,log.records_created,log.records_updated=counts["read"],counts["created"],counts["updated"]
        log.status,log.message="Success",json.dumps(counts)
    except Exception:
        log.status,log.message="Failed",frappe.get_traceback()[-3500:]
        frappe.log_error(log.message,"Zoho Books Invoice Sync")
    finally:
        log.completed_on=now_datetime()
        log.save(ignore_permissions=True)
        frappe.db.commit()
    return counts
