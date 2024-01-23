# -*- coding: utf-8 -*-
# Copyright (c) 2024, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import subprocess
import os

class AppDeployment(Document):
    pass

@frappe.whitelist()
def deploy_app(app=None):
    os.system("chmod +x /home/frappe/frappe-bench/apps/mietrechtspraxis/mietrechtspraxis/mietrechtspraxis/doctype/app_deployment/mietrechtspraxis_deployment.sh")
    os.system("chmod +x /home/frappe/frappe-bench/apps/mietrechtspraxis/mietrechtspraxis/mietrechtspraxis/doctype/app_deployment/mietrecht_ch_deployment.sh")
    if not app:
        return
    if app == 'mietrechtspraxis':
        return str(subprocess.run(["/home/frappe/frappe-bench/apps/mietrechtspraxis/mietrechtspraxis/mietrechtspraxis/doctype/app_deployment/mietrechtspraxis_deployment.sh"], shell=True))
    if app == 'mietrecht_ch':
        return str(subprocess.run(["/home/frappe/frappe-bench/apps/mietrechtspraxis/mietrechtspraxis/mietrechtspraxis/doctype/app_deployment/mietrecht_ch_deployment.sh"], shell=True))

