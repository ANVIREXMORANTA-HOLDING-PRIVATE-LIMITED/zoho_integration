frappe.ui.form.on("Zoho Books Settings", {
 refresh(frm) {
  frm.add_custom_button(__("Connect to Zoho"), async () => {
   const r = await frappe.call({method:"zoho_integration.api.get_authorization_url"});
   if (r.message) window.location.href = r.message;
  });
  frm.add_custom_button(__("Test Connection"), () => {
   frappe.call({method:"zoho_integration.api.test_connection",freeze:true,
    callback(r) { if (r.message) frappe.msgprint(__("Zoho connected. Organizations found: {0}",[r.message.length])); }});
  });
  const run = (label, method, direction="pull", dry_run=1) => frm.add_custom_button(__(label), () => {
   frappe.call({method, args:{direction,dry_run},freeze:true,
    callback(r) { if (r.message && r.message.queued) frappe.show_alert({message:__("Sync job queued"),indicator:"green"}); }});
  });
  run("Dry Run: Pull Customers","zoho_integration.api.sync_customers");
  run("Dry Run: Pull Vendors","zoho_integration.api.sync_suppliers");
  run("Dry Run: Pull Items","zoho_integration.api.sync_items");
  run("Dry Run: Pull Sales Invoices","zoho_integration.api.sync_invoices");
  if (frm.doc.allow_outbound_writes) {
   frm.add_custom_button(__("Run Two-Way Sync"), () => frappe.confirm(
    __("This will create or update contacts, items and draft sales invoices in Zoho Books. Taxed, discounted, foreign-currency and unmapped invoices are skipped. Continue?"),
    () => {
     const jobs=[
      ["zoho_integration.api.sync_customers","both"],
      ["zoho_integration.api.sync_suppliers","both"],
      ["zoho_integration.api.sync_items","both"],
      ["zoho_integration.api.sync_invoices","both"]
     ];
     jobs.forEach(([method,direction])=>frappe.call({method,args:{direction,dry_run:0}}));
     frappe.show_alert({message:__("Synchronization jobs queued"),indicator:"green"});
    }));
  }
 }
});
