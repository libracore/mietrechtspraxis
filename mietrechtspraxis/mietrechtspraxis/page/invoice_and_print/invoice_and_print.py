# -*- coding: utf-8 -*-
# Copyright (c) 2021, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils.data import today

@frappe.whitelist()
def get_show_data(sel_type):
    # invoice and magazine
    if sel_type == 'inv_incl':
        abo_qty = frappe.db.sql("""SELECT COUNT(`name`) AS `qty` FROM `tabmp Abo` WHERE `type` = 'Jahres-Abo' AND `status` = 'Active'""", as_dict=True)[0].qty
        magazine_qty = frappe.db.sql("""SELECT SUM(`magazines_qty_total`) AS `qty` FROM `tabmp Abo` WHERE `type` = 'Jahres-Abo' AND `status` = 'Active'""", as_dict=True)[0].qty
        return {
            'abo_qty': abo_qty,
            'magazine_qty': magazine_qty
        }
        
    # invoice without magazine
    elif sel_type == 'inv_excl':
        abo_qty = frappe.db.sql("""SELECT COUNT(`name`) AS `qty` FROM `tabmp Abo` WHERE `type` = 'Jahres-Abo' AND `status` = 'Active' AND `magazines_qty_ir` = '0'""", as_dict=True)[0].qty
        magazine_qty = frappe.db.sql("""SELECT SUM(`magazines_qty_total`) AS `qty` FROM `tabmp Abo` WHERE `type` = 'Jahres-Abo' AND `status` = 'Active' AND `magazines_qty_ir` = '0'""", as_dict=True)[0].qty
        return {
            'abo_qty': abo_qty,
            'magazine_qty': magazine_qty
        }
    # magazine without invoice
    elif sel_type == 'only_mag':
        abo_qty = frappe.db.sql("""SELECT COUNT(`name`) AS `qty` FROM `tabmp Abo` WHERE `type` = 'Jahres-Abo' AND `status` = 'Active' AND `magazines_qty_ir` = '0'""", as_dict=True)[0].qty
        magazine_qty = frappe.db.sql("""SELECT (SUM(`magazines_qty_total`) - SUM(`magazines_qty_ir`)) AS `qty` FROM `tabmp Abo` WHERE `type` = 'Jahres-Abo' AND `status` = 'Active'""", as_dict=True)[0].qty
        return {
            'abo_qty': abo_qty,
            'magazine_qty': magazine_qty
        }
    # all
    else:
        gratis_qty = frappe.db.sql("""SELECT SUM(`magazines_qty_ir`) AS `qty` FROM `tabmp Abo` WHERE `type` = 'Gratis-Abo' AND `status` = 'Active'""", as_dict=True)[0].qty
        jahres_qty = frappe.db.sql("""SELECT SUM(`magazines_qty_ir`) AS `qty` FROM `tabmp Abo` WHERE `type` = 'Jahres-Abo' AND `status` = 'Active'""", as_dict=True)[0].qty
        probe_qty = frappe.db.sql("""SELECT SUM(`magazines_qty_ir`) AS `qty` FROM `tabmp Abo` WHERE `type` = 'Probe-Abo' AND `end_date` >= '{today}'""".format(today=today()), as_dict=True)[0].qty
        return {
            'gratis_qty': gratis_qty,
            'jahres_qty': jahres_qty,
            'probe_qty': probe_qty
        }
