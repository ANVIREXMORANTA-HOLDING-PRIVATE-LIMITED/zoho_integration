frappe.pages["zoho-books-dashboard"].on_page_load = function (wrapper) {
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: __("Zoho Books Dashboard"),
    single_column: true
  });

  const $main = $(`
    <div class="zoho-dashboard">
      <div class="row" style="margin-bottom:16px">
        <div class="col-sm-4"><div class="zoho-stat"><div class="text-muted">Connection</div><h3 data-status>Checking…</h3></div></div>
        <div class="col-sm-4"><div class="zoho-stat"><div class="text-muted">Organization</div><h3 data-org>Not selected</h3></div></div>
        <div class="col-sm-4"><div class="zoho-stat"><div class="text-muted">Last token expiry</div><h3 data-expiry>—</h3></div></div>
      </div>
      <div class="card" style="padding:18px;margin-bottom:16px">
        <h4>Connection & setup</h4>
        <p class="text-muted">Connect your Zoho Books India organization, then verify access before running preview syncs.</p>
        <button class="btn btn-primary" data-connect>Connect to Zoho</button>
        <button class="btn btn-default" data-test>Test connection</button>
        <button class="btn btn-default" data-settings>Open settings</button>
        <div class="text-muted small" data-message style="margin-top:12px"></div>
      </div>
      <div class="card" style="padding:18px;margin-bottom:16px">
        <h4>Inbound dry runs</h4>
        <p class="text-muted">Preview records from Zoho Books without creating or updating ERPNext documents.</p>
        <div class="btn-group" role="group">
          <button class="btn btn-default" data-sync="customers">Customers</button>
          <button class="btn btn-default" data-sync="suppliers">Vendors</button>
          <button class="btn btn-default" data-sync="items">Items</button>
          <button class="btn btn-default" data-sync="invoices">Sales invoices</button>
        </div>
      </div>
      <div class="card" style="padding:18px">
        <h4>Safety</h4>
        <p>Outbound writes remain disabled until explicitly enabled in Zoho Books Settings. Invoice sync currently supports only a restricted subset; tax, discount, shipping, foreign-currency and purchase-bill workflows are not fully implemented.</p>
        <div class="text-muted small">Review Zoho Books Sync Log after each queued job. Do not enable scheduled sync until dry-run results have been checked.</div>
      </div>
    </div>
    <style>
      .zoho-stat{background:var(--card-bg);border:1px solid var(--border-color);border-radius:8px;padding:16px}
      .zoho-stat h3{margin:8px 0 0;font-size:18px}
      .zoho-dashboard .card{background:var(--card-bg);border:1px solid var(--border-color);border-radius:8px}
      .zoho-dashboard .btn{margin:0 6px 6px 0}
    </style>
  `);
  $(page.body).append($main);

  const message = (text, indicator="blue") => {
    $main.find("[data-message]").text(text).css("color", indicator === "red" ? "var(--red-600)" : "var(--text-muted)");
  };
  const call = async (method, args={}) => {
    const r = await frappe.call({method, args, freeze:true});
    return r.message;
  };

  $main.on("click", "[data-connect]", async () => {
    try {
      const url = await call("zoho_integration.api.get_authorization_url");
      if (url) window.location.href = url;
    } catch (e) { message(__("Could not start OAuth. Check the Error Log."), "red"); }
  });
  $main.on("click", "[data-test]", async () => {
    try {
      const orgs = await call("zoho_integration.api.test_connection");
      message(__( "Connection successful. Organizations returned: {0}", [orgs.length]));
      $main.find("[data-status]").text("Connected");
      if (orgs.length) $main.find("[data-org]").text(orgs[0].name || orgs[0].organization_name || "Available");
    } catch (e) {
      message(__("Connection test failed. Open Zoho Books Sync Log / Error Log for details."), "red");
      $main.find("[data-status]").text("Needs attention");
    }
  });
  $main.on("click", "[data-settings]", () => frappe.set_route("Form", "Zoho Books Settings", "Zoho Books Settings"));
  $main.on("click", "[data-sync]", async function () {
    const key = $(this).attr("data-sync");
    const methods = {
      customers:"zoho_integration.api.sync_customers",
      suppliers:"zoho_integration.api.sync_suppliers",
      items:"zoho_integration.api.sync_items",
      invoices:"zoho_integration.api.sync_invoices"
    };
    try {
      await call(methods[key], {direction:"pull", dry_run:1});
      message(__( "{0} dry-run queued. Review Zoho Books Sync Log for the result.", [key]));
    } catch (e) { message(__( "{0} dry-run could not be queued. Check settings and permissions.", [key]), "red"); }
  });

  frappe.call({
    method:"frappe.client.get",
    args:{doctype:"Zoho Books Settings",name:"Zoho Books Settings",fields:["connected","organization_id","token_expiry","enabled"]},
    callback(r) {
      const d=r.message || {};
      $main.find("[data-status]").text(d.connected ? "Connected flag set" : "Not connected");
      $main.find("[data-org]").text(d.organization_id || "Not selected");
      $main.find("[data-expiry]").text(d.token_expiry ? frappe.datetime.str_to_user(d.token_expiry) : "—");
    }
  });
};
