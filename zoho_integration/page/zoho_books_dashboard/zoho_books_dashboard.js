frappe.pages["zoho-books-dashboard"].on_page_load = function (wrapper) {
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: __("Zoho Books Control Center"),
    single_column: true
  });

  const $root = $(`
    <div class="zb-shell">
      <section class="zb-hero">
        <div>
          <div class="zb-eyebrow">ERPNext × ZOHO BOOKS INDIA</div>
          <h2>Integration Control Center</h2>
          <p>Monitor your connection, validate mappings and run controlled synchronization jobs.</p>
        </div>
        <div class="zb-hero-actions">
          <button class="btn btn-default" data-refresh><i class="fa fa-refresh"></i> Refresh</button>
          <button class="btn btn-primary" data-settings><i class="fa fa-sliders"></i> Setup & Settings</button>
        </div>
      </section>

      <section class="zb-grid zb-grid-3">
        <article class="zb-metric"><span>Zoho connection</span><strong data-status>Checking…</strong><small data-token>Checking encrypted token storage</small></article>
        <article class="zb-metric"><span>Selected organization</span><strong class="zb-org" data-org>Not selected</strong><small>Zoho Books India</small></article>
        <article class="zb-metric"><span>Access token expiry</span><strong data-expiry>—</strong><small>Token values are never displayed</small></article>
      </section>

      <section class="zb-panel">
        <div class="zb-panel-head"><div><h3>Connection & setup</h3><p>Complete the connection test before starting any sync job.</p></div><span class="zb-pill" data-connection-pill>Checking</span></div>
        <div class="zb-actions">
          <button class="btn btn-primary" data-connect><i class="fa fa-link"></i> Connect / Re-authorize</button>
          <button class="btn btn-default" data-test><i class="fa fa-check-circle"></i> Test connection</button>
          <button class="btn btn-default" data-settings><i class="fa fa-cog"></i> Open settings</button>
          <button class="btn btn-default" data-logs><i class="fa fa-list-alt"></i> View sync logs</button>
        </div>
        <div class="zb-notice" data-message role="status">Loading integration status…</div>
      </section>

      <section class="zb-panel">
        <div class="zb-panel-head"><div><h3>Synchronization center</h3><p>Preview inbound Zoho data. These buttons always queue dry-run jobs.</p></div><span class="zb-pill zb-pill-safe">DRY RUN ONLY</span></div>
        <div class="zb-sync-grid">
          <article class="zb-sync-card"><div class="zb-icon"><i class="fa fa-address-book"></i></div><h4>Customers</h4><p>Zoho contacts to ERPNext Customers.</p><button class="btn btn-default" data-sync="customers">Preview customers</button></article>
          <article class="zb-sync-card"><div class="zb-icon"><i class="fa fa-truck"></i></div><h4>Suppliers</h4><p>Zoho vendor contacts to ERPNext Suppliers.</p><button class="btn btn-default" data-sync="suppliers">Preview suppliers</button></article>
          <article class="zb-sync-card"><div class="zb-icon"><i class="fa fa-cubes"></i></div><h4>Items</h4><p>Zoho items and ERPNext item mapping.</p><button class="btn btn-default" data-sync="items">Preview items</button></article>
          <article class="zb-sync-card"><div class="zb-icon"><i class="fa fa-file-text-o"></i></div><h4>Sales invoices</h4><p>Check eligible invoice imports without creating documents.</p><button class="btn btn-default" data-sync="invoices">Preview invoices</button></article>
        </div>
      </section>

      <section class="zb-grid zb-grid-2">
        <article class="zb-panel">
          <div class="zb-panel-head"><div><h3>Operational controls</h3><p>Production safeguards read from Zoho Books Settings.</p></div></div>
          <div class="zb-control-row"><span>Synchronization enabled</span><strong data-enabled>—</strong></div>
          <div class="zb-control-row"><span>Scheduled pull sync</span><strong data-scheduled>—</strong></div>
          <div class="zb-control-row"><span>ERPNext → Zoho writes</span><strong data-outbound>—</strong></div>
          <p class="zb-footnote">Keep scheduled sync and outbound writes disabled until mappings, dry-run results and accounting totals have been independently verified.</p>
        </article>
        <article class="zb-panel">
          <div class="zb-panel-head"><div><h3>Feature coverage</h3><p>Current code capabilities, not roadmap promises.</p></div></div>
          <div class="zb-feature"><span>Customers & suppliers</span><b class="zb-tag zb-tag-live">Implemented</b></div>
          <div class="zb-feature"><span>Items (non-stock import)</span><b class="zb-tag zb-tag-live">Implemented</b></div>
          <div class="zb-feature"><span>Sales invoices (restricted drafts)</span><b class="zb-tag zb-tag-limited">Limited</b></div>
          <div class="zb-feature"><span>Purchase bills & payments</span><b class="zb-tag zb-tag-roadmap">Not implemented</b></div>
          <div class="zb-feature"><span>GST / tax / inventory movements</span><b class="zb-tag zb-tag-roadmap">Not implemented</b></div>
          <div class="zb-feature"><span>Auto-submit / reconciliation</span><b class="zb-tag zb-tag-roadmap">Not implemented</b></div>
        </article>
      </section>
      <footer class="zb-footer">Security first · Encrypted OAuth credentials · Background jobs · Audit trail in Zoho Books Sync Log</footer>
    </div>
    <style>
      .zb-shell{max-width:1440px;margin:0 auto;padding:8px 2px 28px;color:var(--text-color)}
      .zb-hero{display:flex;justify-content:space-between;align-items:center;gap:20px;padding:28px 30px;margin-bottom:18px;border-radius:16px;background:linear-gradient(120deg,var(--subtle-accent),var(--card-bg));border:1px solid var(--border-color)}
      .zb-eyebrow{font-size:10px;letter-spacing:1.5px;font-weight:700;color:var(--primary);margin-bottom:8px}
      .zb-hero h2{font-size:26px;font-weight:700;margin:0 0 7px}.zb-hero p,.zb-panel-head p{color:var(--text-muted);margin:0}
      .zb-hero-actions,.zb-actions{display:flex;gap:8px;flex-wrap:wrap}.zb-grid{display:grid;gap:14px;margin-bottom:16px}.zb-grid-3{grid-template-columns:repeat(3,minmax(0,1fr))}.zb-grid-2{grid-template-columns:repeat(2,minmax(0,1fr))}
      .zb-metric,.zb-panel{background:var(--card-bg);border:1px solid var(--border-color);border-radius:13px;padding:19px}
      .zb-metric span{display:block;color:var(--text-muted);font-size:12px}.zb-metric strong{display:block;font-size:20px;margin:7px 0;overflow-wrap:anywhere}.zb-metric small{color:var(--text-muted)}
      .zb-org{font-size:17px!important}.zb-panel{margin-bottom:16px}.zb-panel-head{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;margin-bottom:16px}.zb-panel-head h3{font-size:16px;font-weight:700;margin:0 0 5px}
      .zb-pill{font-size:10px;font-weight:700;border-radius:30px;padding:6px 10px;background:var(--subtle-fg);white-space:nowrap}.zb-pill-safe{background:var(--bg-green);color:var(--green-700)}
      .zb-notice{margin-top:14px;padding:10px 12px;background:var(--control-bg);border-radius:8px;color:var(--text-muted);font-size:12px}
      .zb-sync-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}.zb-sync-card{border:1px solid var(--border-color);border-radius:11px;padding:16px}.zb-icon{width:34px;height:34px;border-radius:9px;background:var(--subtle-accent);display:grid;place-items:center;color:var(--primary);font-size:15px}
      .zb-sync-card h4{font-weight:700;margin:12px 0 5px}.zb-sync-card p{font-size:12px;color:var(--text-muted);min-height:34px}.zb-sync-card .btn{width:100%}
      .zb-control-row,.zb-feature{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:10px 0;border-bottom:1px solid var(--border-color);font-size:12px}.zb-control-row strong{font-size:12px}.zb-footnote,.zb-footer{font-size:11px;color:var(--text-muted);line-height:1.6;margin:14px 0 0}.zb-tag{font-size:10px;padding:4px 7px;border-radius:5px;white-space:nowrap}.zb-tag-live{background:var(--bg-green);color:var(--green-700)}.zb-tag-limited{background:var(--bg-yellow);color:var(--yellow-700)}.zb-tag-roadmap{background:var(--control-bg);color:var(--text-muted)}
      @media(max-width:900px){.zb-sync-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.zb-hero{align-items:flex-start;flex-direction:column}}
      @media(max-width:650px){.zb-grid-3,.zb-grid-2,.zb-sync-grid{grid-template-columns:1fr}.zb-hero{padding:20px}.zb-hero h2{font-size:22px}}
    </style>
  `);
  $(page.body).append($root);

  const say = (value, error) => {
    $root.find("[data-message]").text(value).toggleClass("text-danger", !!error);
  };
  const call = async (method, args = {}) => {
    const response = await frappe.call({method, args, freeze: true});
    return response.message;
  };
  const setFlag = (selector, value) => {
    $root.find(selector).text(value ? "Enabled" : "Disabled");
  };

  async function refreshStatus() {
    try {
      const [settings, tokens] = await Promise.all([
        call("frappe.client.get", {doctype:"Zoho Books Settings", name:"Zoho Books Settings"}),
        call("zoho_integration.api.token_storage_status")
      ]);
      const stored = !!(tokens.access_token_stored && tokens.refresh_token_stored);
      const connected = !!(tokens.connected_flag && stored);
      $root.find("[data-status]").text(connected ? "Connected" : "Needs attention");
      $root.find("[data-token]").text(stored ? "Access and refresh tokens securely stored" : "Encrypted token storage incomplete");
      $root.find("[data-org]").text(settings.organization_id || "Not selected");
      $root.find("[data-expiry]").text(settings.token_expiry ? frappe.datetime.str_to_user(settings.token_expiry) : "Not available");
      $root.find("[data-connection-pill]").text(connected ? "CONNECTED" : "NOT VERIFIED");
      setFlag("[data-enabled]", settings.enabled);
      setFlag("[data-scheduled]", settings.scheduled_sync);
      setFlag("[data-outbound]", settings.allow_outbound_writes);
      if (!connected) say("Connection is not fully verified. Open settings and complete OAuth + Test Connection.", true);
      else say("Credentials are stored. Run Test connection to verify live Zoho API access.");
    } catch (e) {
      $root.find("[data-status]").text("Unavailable");
      $root.find("[data-connection-pill]").text("CHECK ERROR");
      say("Could not load settings. Confirm System Manager permissions and inspect Error Log.", true);
    }
  }

  $root.on("click", "[data-refresh]", refreshStatus);
  $root.on("click", "[data-settings]", () => frappe.set_route("Form","Zoho Books Settings","Zoho Books Settings"));
  $root.on("click", "[data-logs]", () => frappe.set_route("List","Zoho Books Sync Log"));
  $root.on("click", "[data-connect]", async () => {
    try {
      const url = await call("zoho_integration.api.get_authorization_url");
      if (url) window.location.href = url;
      else say("Zoho did not return an authorization URL.", true);
    } catch (e) { say("Could not start OAuth. Check Client ID, Client Secret and Error Log.", true); }
  });
  $root.on("click", "[data-test]", async () => {
    try {
      const orgs = await call("zoho_integration.api.test_connection");
      say("Live connection successful. Zoho organizations available: " + (orgs || []).length + ". Confirm the correct organization in Settings.");
      $root.find("[data-status]").text("API verified");
      $root.find("[data-connection-pill]").text("API VERIFIED");
    } catch (e) { say("Connection test failed. Check organization selection, OAuth scopes and Error Log.", true); }
  });
  $root.on("click", "[data-sync]", async function () {
    const key = $(this).attr("data-sync");
    const methods = {
      customers:"zoho_integration.api.sync_customers",
      suppliers:"zoho_integration.api.sync_suppliers",
      items:"zoho_integration.api.sync_items",
      invoices:"zoho_integration.api.sync_invoices"
    };
    try {
      await call(methods[key], {direction:"pull", dry_run:1});
      say(key + " preview queued. Open Sync Logs and wait for the background job to finish.");
    } catch (e) { say("Could not queue " + key + " preview. Confirm sync is enabled and inspect Error Log.", true); }
  });

  refreshStatus();
};
