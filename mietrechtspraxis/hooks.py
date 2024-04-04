# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "mietrechtspraxis"
app_title = "mietrechtspraxis"
app_publisher = "libracore AG"
app_description = "All about mietrechtspraxis"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "info@libracore.com"
app_license = "MIT"

# Includes in <head>
# ------------------
# website_route_rules = [
#     {"from_route": "/login#forgot", "to_route": "/pwd-reset"},
#     {"from_route": "/#forgot", "to_route": "/pwd-reset"}
# ]
website_redirects = [
    # absolute location
    {"source": "/me", "target": "https://www.mietrecht.ch/"}
]


# include js, css files in header of desk.html
# app_include_css = "/assets/mietrechtspraxis/css/mietrechtspraxis.css"
app_include_js = [
    "/assets/js/mietrechtspraxistemplates.min.js"
]

# include js, css files in header of web template
web_include_css = "/assets/mietrechtspraxis/css/mietrechtspraxis.css"
# web_include_js = "/assets/mietrechtspraxis/js/mietrechtspraxis.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}
welcome_email_subject = "www.mietrecht.ch – mietrechtspraxis | mp"
welcome_email_template = "welcome_mail"

# include js in doctype views
doctype_js = {
    "Customer" : "public/js/custom_scripts/customer.js",
    "Address" : "public/js/custom_scripts/address.js",
    "Sales Invoice" : "public/js/custom_scripts/sales_invoice.js",
    "Contact" : "public/js/custom_scripts/contact.js"
}
doctype_list_js = {
    "Payment Reminder" : "/public/js/custom_scripts/mahnungen_list.js",
    "Sales Order" : "/public/js/custom_scripts/sales_order_list.js"
}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "mietrechtspraxis.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "mietrechtspraxis.install.before_install"
# after_install = "mietrechtspraxis.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "mietrechtspraxis.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"mietrechtspraxis.tasks.all"
# 	],
# 	"daily": [
# 		"mietrechtspraxis.tasks.daily"
# 	],
# 	"hourly": [
# 		"mietrechtspraxis.tasks.hourly"
# 	],
# 	"weekly": [
# 		"mietrechtspraxis.tasks.weekly"
# 	]
# 	"monthly": [
# 		"mietrechtspraxis.tasks.monthly"
# 	]
# }
scheduler_events = {
    "daily": [
        "mietrechtspraxis.mietrechtspraxis.doctype.mp_abo.mp_abo.set_inactive_status",
        "mietrechtspraxis.mietrechtspraxis.doctype.mp_abo.mp_abo.remove_recipient",
        "mietrechtspraxis.mietrechtspraxis.utils.daily_jobs.validate_mp_web_user"
    ]
}

# Testing
# -------

# before_tests = "mietrechtspraxis.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "mietrechtspraxis.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "mietrechtspraxis.task.get_dashboard_data"
# }

