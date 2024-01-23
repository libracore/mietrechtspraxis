# -*- coding: utf-8 -*-
# Copyright (c) 2024, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import subprocess

class AppDeployment(Document):
    pass

@frappe.whitelist()
def deploy_app(app=None):
    if not app:
        return
    if app == 'mietrechtspraxis':
        return str(subprocess.run(["/home/frappe/frappe-bench/apps/mietrechtspraxis/mietrechtspraxis/mietrechtspraxis/doctype/app_deployment/mietrechtspraxis_deployment.sh"], shell=True))

