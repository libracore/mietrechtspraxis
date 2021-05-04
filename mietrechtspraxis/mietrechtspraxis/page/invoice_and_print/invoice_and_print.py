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

@frappe.whitelist()
def create_invoices(date):
    abos = frappe.db.sql("""SELECT `name` FROM `tabmp Abo` WHERE `type` = 'Jahres-Abo' AND `status` = 'Active'""", as_dict=True)
    for _abo in abos:
        abo = frappe.get_doc("mp Abo", _abo.name)
        sinv = create_invoice(abo.name, date)
        row = abo.append('sales_invoices', {})
        row.sales_invoice = sinv
        abo.save()
        
def create_invoice(abo, date):
    abo = frappe.get_doc("mp Abo", abo)
    
    new_sinv = frappe.get_doc({
        "doctype": "Sales Invoice",
        "set_posting_time": 1,
        "posting_date": date,
        "posting_time": "00:00:00",
        "customer": abo.invoice_recipient,
        "customer_address": abo.recipient_address,
        "contact_person": abo.recipient_contact,
        "items": [
            {
                "item_code": frappe.db.get_single_value('mp Abo Settings', 'jahres_abo'),
                "qty": abo.magazines_qty_total
            }
        ]
    })
    new_sinv.insert()
    new_sinv.submit()
    frappe.db.commit()
    
    return new_sinv.name
