frappe.ui.form.on("Zoho Books Settings", {
 refresh(frm) {
  frm.add_custom_button(__("Connect to Zoho"), async () => {
   const r = await frappe.call({method:"zoho_integration.oauth.get_authorization_url"});
   if (r.message) window.location.href = r.message;
  });
  frm.add_custom_button(__("Test Connection"), () => {
   frappe.call({method:"zoho_integration.api.test_connection", freeze:true,
    callback(r) { if (r.message) frappe.msgprint(__("Zoho connected. Organizations found: {0}", [r.message.length])); }});
  });
  frm.add_custom_button(__("Dry Run: Pull Customers"), () => {
   frappe.call({method:"zoho_integration.api.sync_customers",args:{direction:"pull",dry_run:1},freeze:true});
  });
  frm.add_custom_button(__("Sync Customers Both Ways"), () => {
   frappe.confirm(__("This can create/update contacts in both systems. Confirm outbound writes are enabled and mappings are verified."),
    () => frappe.call({method:"zoho_integration.api.sync_customers",args:{direction:"both",dry_run:0},freeze:true}));
  });
 }
});
