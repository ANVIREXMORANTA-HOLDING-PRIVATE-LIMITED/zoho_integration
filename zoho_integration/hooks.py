app_name = "zoho_integration"
app_title = "Zoho Books Integration"
app_publisher = "ANVIREXMORANTA HOLDING PRIVATE LIMITED"
app_description = "Two-way Zoho Books integration for ERPNext"
app_email = "support@example.com"
app_license = "MIT"
app_version = "0.2.0"
required_apps = ["erpnext"]

scheduler_events = {
    "hourly": ["zoho_integration.tasks.enqueue_scheduled_sync"]
}

doctype_js = {
    "Zoho Books Settings": "public/js/zoho_books_settings.js"
}
