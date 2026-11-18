import json
import frappe
from frappe import _
from frappe.utils import now_datetime
from zoho_integration.zoho_client import ZohoBooksClient

def _link(zoho_id=None, erp_name=None):
    filters={"zoho_module":"items"}
    if zoho_id: filters["zoho_id"]=str(zoho_id)
    if erp_name: filters.update({"erpnext_doctype":"Item","erpnext_name":erp_name})
    return frappe.db.get_value("Zoho Books Document Link",filters,"name")

def _save_link(item_name,zid):
    name=_link(zoho_id=zid)
    doc=frappe.get_doc("Zoho Books Document Link",name) if name else frappe.new_doc("Zoho Books Document Link")
    doc.erpnext_doctype,doc.erpnext_name="Item",item_name
    doc.zoho_module,doc.zoho_id="items",str(zid)
    doc.last_synced_at,doc.sync_status=now_datetime(),"Synced"
    doc.save(ignore_permissions=True)

def _default_item_group():
    return frappe.db.get_value("Item Group",{"is_group":0},"name",order_by="lft asc")

def _zoho_to_item(row,dry_run):
    zid=str(row["item_id"])
    link=_link(zoho_id=zid)
    linked=frappe.db.get_value("Zoho Books Document Link",link,"erpnext_name") if link else None
    sku=(row.get("sku") or "").strip()
    existing=linked if linked and frappe.db.exists("Item",linked) else (sku if sku and frappe.db.exists("Item",sku) else None)
    if dry_run: return "would_update" if existing else "would_create"
    doc=frappe.get_doc("Item",existing) if existing else frappe.new_doc("Item")
    if not existing:
        group=_default_item_group()
        uom=row.get("unit") or frappe.db.get_single_value("Stock Settings","stock_uom") or "Nos"
        if not group: frappe.throw(_("Create a non-group Item Group before syncing items."))
        if not frappe.db.exists("UOM",uom): uom="Nos" if frappe.db.exists("UOM","Nos") else frappe.db.get_single_value("Stock Settings","stock_uom")
        if not uom or not frappe.db.exists("UOM",uom): frappe.throw(_("Create the Zoho unit as an ERPNext UOM before syncing this item."))
        doc.item_group,doc.stock_uom=group,uom
        doc.is_stock_item=0
    doc.item_code=sku or doc.get("item_code") or "ZB-"+zid
    doc.item_name=row.get("name") or row.get("item_name") or doc.item_code
    doc.description=row.get("description") or doc.get("description")
    doc.is_stock_item=0
    # Preserve an existing ERPNext stock/non-stock classification. New imports
    # remain non-stock until the administrator configures inventory mapping.
    doc.save(ignore_permissions=True)
    _save_link(doc.name,zid)
    return "updated" if existing else "created"

def _erp_to_zoho(doc,client,dry_run,index):
    link_name=_link(erp_name=doc.name)
    link=frappe.get_doc("Zoho Books Document Link",link_name) if link_name else None
    zid=link.zoho_id if link else index.get((doc.item_code or "").casefold())
    payload={"name":doc.item_name or doc.item_code,"sku":doc.item_code,"description":doc.description or "",
             "rate":float(doc.get("standard_rate") or 0),
             "product_type":"goods" if doc.is_stock_item else "service"}
    if dry_run: return "would_update" if zid else "would_create"
    if zid:
        client.request("PUT","items/"+str(zid),payload=payload)
        action="updated"
    else:
        result=client.request("POST","items",payload=payload)
        zid=str(result.get("item",{}).get("item_id") or "")
        if not zid: frappe.throw(_("Zoho did not return an item ID."))
        action="created"
    _save_link(doc.name,zid)
    return action

def sync_items(direction="pull",dry_run=True):
    settings=frappe.get_single("Zoho Books Settings")
    log=frappe.new_doc("Zoho Books Sync Log")
    log.entity,log.direction,log.status,log.dry_run="items",direction,"Running",int(bool(dry_run))
    log.started_by=frappe.session.user or "Administrator"
    log.insert(ignore_permissions=True)
    counts={"read":0,"created":0,"updated":0,"skipped":0}
    try:
        client=ZohoBooksClient(settings)
        if direction in ("pull","both"):
            page=1
            while True:
                result=client.request("GET","items",params={"page":page,"per_page":200})
                rows=result.get("items",[])
                counts["read"]+=len(rows)
                for row in rows:
                    out=_zoho_to_item(row,dry_run)
                    counts["created" if out in ("created","would_create") else "updated" if out in ("updated","would_update") else "skipped"]+=1
                if not result.get("page_context",{}).get("has_more_page"): break
                page+=1
        if direction in ("push","both"):
            index,page={},1
            while True:
                result=client.request("GET","items",params={"page":page,"per_page":200})
                for row in result.get("items",[]):
                    sku=(row.get("sku") or "").casefold()
                    if sku and row.get("item_id"): index[sku]=str(row["item_id"])
                if not result.get("page_context",{}).get("has_more_page"): break
                page+=1
            for name in frappe.get_all("Item",filters={"disabled":0},pluck="name"):
                out=_erp_to_zoho(frappe.get_doc("Item",name),client,dry_run,index)
                counts["created" if out in ("created","would_create") else "updated"]+=1
        log.records_read,log.records_created,log.records_updated=counts["read"],counts["created"],counts["updated"]
        log.status,log.message="Success",json.dumps(counts)
    except Exception:
        log.status,log.message="Failed",frappe.get_traceback()[-3500:]
        frappe.log_error(log.message,"Zoho Books Item Sync")
    finally:
        log.completed_on=now_datetime()
        log.save(ignore_permissions=True)
        frappe.db.commit()
    return counts
