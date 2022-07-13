# -*- coding: utf-8 -*-
# Copyright (c) 2021, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, os
from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice
from mietrechtspraxis.mietrechtspraxis.utils.qrr_reference import get_qrr_reference
from PyPDF2 import PdfFileWriter
from frappe.utils.background_jobs import enqueue
from frappe.utils.data import now

@frappe.whitelist()
def create_invoices(tag):
    sales_orders = frappe.db.sql("""SELECT
                                        `name`
                                    FROM `tabSales Order`
                                    WHERE `docstatus` = 1
                                    AND `_user_tags` LIKE '%{tag}%'
                                    AND `per_billed` < 1""".format(tag=tag), as_dict=True)
    if len(sales_orders) > 0:
        sinvs = []
        return_value = ''
        for so in sales_orders:
            sinv = frappe.get_doc(make_sales_invoice(so.name, target_doc=None, ignore_permissions=False))
            sinv.insert()
            sinv.esr_reference = get_qrr_reference(sales_invoice=sinv.name, customer=sinv.customer)
            sinv.submit()
            sinvs.append(sinv.name)
            return_value = sinv.name
        print_rechnungen(sinvs, return_value)
        return return_value
    else:
        return 'keine'

def print_rechnungen(sinvs, return_value):
    args = {
        'sinvs': sinvs
    }
    enqueue("mietrechtspraxis.mietrechtspraxis.utils.so_to_sinv.blk_print_rechnungen", queue='long', job_name=return_value, timeout=5000, **args)

def blk_print_rechnungen(sinvs):
    save_counter = 1
    
    rm_log = frappe.get_doc({
        "doctype": "RM Log",
        'start': now(),
        'status': 'Job gestartet',
        'typ': 'Rechnungen (Sonstiges)'
    })
    rm_log.insert()
    frappe.db.commit()
    
    bind_source = "/assets/mietrechtspraxis/sinvs_for_print/{date}.pdf".format(date=rm_log.name)
    physical_path = "/home/frappe/frappe-bench/sites" + bind_source
    dest=str(physical_path)
    
    output = PdfFileWriter()
    
    for sinv in sinvs:
        # create rm_log:
        try:
            row = rm_log.append('sinvs', {})
            row.sinv = sinv
            if save_counter == 250:
                rm_log.save(ignore_permissions=True)
                frappe.db.commit()
                save_counter = 1
            else:
                save_counter += 1
        except:
            frappe.log_error(frappe.get_traceback(), 'create rm_log failed: {ref_dok}'.format(ref_dok=mahnung.name))
        
        try:
            output = frappe.get_print("Sales Invoice", sinv, 'Verlagsprodukte', as_pdf = True, output = output, no_letterhead = 1, ignore_zugferd=True)
        except:
            frappe.log_error(frappe.get_traceback(), 'print_pdf failed: {ref_dok}'.format(ref_dok=sinv))
    
    rm_log.save(ignore_permissions=True)
    frappe.db.commit()
    
    try:
        if isinstance(dest, str): # when dest is a file path
            destdir = os.path.dirname(dest)
            if destdir != '' and not os.path.isdir(destdir):
                os.makedirs(destdir)
            with open(dest, "wb") as w:
                output.write(w)
        else: # when dest is io.IOBase
            output.write(dest)
    except:
        frappe.log_error(frappe.get_traceback(), 'save_pdf failed: {ref_dok}'.format(ref_dok=rm_log.name))
    
    rm_log.ende = now()
    rm_log.status = 'PDF erstellt'
    rm_log.save(ignore_permissions=True)
    frappe.db.commit()
