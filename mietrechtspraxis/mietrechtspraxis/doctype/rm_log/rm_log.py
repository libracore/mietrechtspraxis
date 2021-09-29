# -*- coding: utf-8 -*-
# Copyright (c) 2021, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import os

class RMLog(Document):
    pass

@frappe.whitelist()
def sinv_storno(rm_log):
    rm_log = frappe.get_doc("RM Log", rm_log)
    for rm_log_sinv in rm_log.sinvs:
        sinv = frappe.get_doc("Sales Invoice", rm_log_sinv.sinv)
        sinv_in_abo = frappe.db.sql("""SELECT `name` FROM `tabmp Abo Invoice` WHERE `sales_invoice` = '{sinv}'""".format(sinv=sinv.name), as_dict=True)[0].name
        delete_sinv_in_abo = frappe.db.sql("""DELETE FROM `tabmp Abo Invoice` WHERE `name` = '{sinv}'""".format(sinv=sinv_in_abo), as_list=True)
        sinv.cancel()
        frappe.db.commit()
    
    bind_source = "/assets/mietrechtspraxis/sinvs_for_print/{date}.pdf".format(date=rm_log.name)
    physical_path = "/home/frappe/frappe-bench/sites" + bind_source
    dest=str(physical_path)
    if os.path.exists(dest):
        os.remove(dest)
    
    rm_log.status = 'Rechnungen storniert'
    rm_log.save(ignore_permissions=True)
    frappe.db.commit()
    return
