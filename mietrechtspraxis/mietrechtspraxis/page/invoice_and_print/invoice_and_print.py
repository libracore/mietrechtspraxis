# -*- coding: utf-8 -*-
# Copyright (c) 2021, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, os
from frappe.utils.data import today
from frappe import publish_progress
from frappe import _
from PyPDF2 import PdfFileWriter

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
        gratis_qty = frappe.db.sql("""SELECT SUM(`magazines_qty_total`) AS `qty` FROM `tabmp Abo` WHERE `type` = 'Gratis-Abo' AND `status` = 'Active'""", as_dict=True)[0].qty
        jahres_qty = frappe.db.sql("""SELECT SUM(`magazines_qty_total`) AS `qty` FROM `tabmp Abo` WHERE `type` = 'Jahres-Abo' AND `status` = 'Active'""", as_dict=True)[0].qty
        probe_qty = frappe.db.sql("""SELECT SUM(`magazines_qty_total`) AS `qty` FROM `tabmp Abo` WHERE `type` = 'Probe-Abo' AND `end_date` >= '{today}'""".format(today=today()), as_dict=True)[0].qty
        return {
            'gratis_qty': gratis_qty,
            'jahres_qty': jahres_qty,
            'probe_qty': probe_qty
        }

@frappe.whitelist()
def create_invoices(date, year):
    data = []
    qty_one = 0
    qty_multi = 0
    abos = frappe.db.sql("""SELECT `name` FROM `tabmp Abo` WHERE `type` = 'Jahres-Abo' AND `status` = 'Active' AND `name` NOT IN (SELECT `parent` FROM `tabmp Abo Invoice` WHERE `year` = '{year}')""".format(year=year), as_dict=True)
    count = 0
    for _abo in abos:
        count += 1
        abo = frappe.get_doc("mp Abo", _abo.name)
        sinv = create_invoice(abo.name, date)
        row = abo.append('sales_invoices', {})
        row.sales_invoice = sinv['sinv']
        row.year = year
        abo.save()
        _data = {}
        _data['abo'] = abo.name
        _data['recipient'] = abo.recipient_name
        _data['invoice_recipient'] = abo.invoice_recipient
        _data['magazines_qty_total'] = abo.magazines_qty_total
        _data['sinv'] = sinv['sinv']
        _data['send_as_mail'] = sinv['send_as_mail']
        _data['mail'] = sinv['mail']
        data.append(_data)
        
        if not sinv['send_as_mail']:
            if abo.magazines_qty_total == 1:
                qty_one += 1
            else:
                qty_multi += 1
        progress = (100 / len(abos)) * count
        publish_progress(percent=progress, title="Creating Invoices...")
    return {
        'abos': data,
        'qty_one': qty_one,
        'qty_multi': qty_multi
    }
        
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
    
    customer = frappe.get_doc("Customer", abo.invoice_recipient)
    if customer.korrespondenz == 'E-Mail':
        contact = frappe.get_doc("Contact", abo.recipient_contact)
        if contact.email_id:
            send_as_mail = True
            mail = contact.email_id
            send_invoice_as_mail(new_sinv.name, mail)
            new_sinv.sended_as_mail = 1
            new_sinv.save()
            frappe.db.commit()
        else:
            send_as_mail = False
            mail = ''
    else:
        send_as_mail = False
        mail = ''
    
    return {
        'sinv': new_sinv.name,
        'send_as_mail': send_as_mail,
        'mail': mail
    }
    
def send_invoice_as_mail(sinv, address):
	frappe.sendmail([address],
		subject=  _("New Invoice: {sinv}").format(sinv=sinv),
        reply_to= 'office@mietrecht.ch',
		message = _("Please find attached Invoice {sinv}").format(sinv=sinv),
		attachments = [frappe.attach_print('Sales Invoice', sinv, file_name=sinv, print_format=frappe.db.get_single_value('mp Abo Settings', 'druckformat'))])

@frappe.whitelist()
def print_pdf(date):
    bind_source = "/assets/mietrechtspraxis/sinvs_for_print/{date}.pdf".format(date=date)
    physical_path = "/home/frappe/frappe-bench/sites" + bind_source
    dest=str(physical_path)
    
    invoices = frappe.db.sql("""SELECT `name` FROM `tabSales Invoice` WHERE `posting_date` = '{date}' AND `docstatus` = 1 AND `sended_as_mail` != 1""".format(date=date), as_list=True)
    
    output = PdfFileWriter()
    
    for invoice in invoices:
        output = frappe.get_print("Sales Invoice", invoice[0], frappe.db.get_single_value('mp Abo Settings', 'druckformat'), as_pdf = True, output = output, ignore_zugferd=True)
        
    if isinstance(dest, str): # when dest is a file path
        destdir = os.path.dirname(dest)
        if destdir != '' and not os.path.isdir(destdir):
            os.makedirs(destdir)
        with open(dest, "wb") as w:
            output.write(w)
    else: # when dest is io.IOBase
        output.write(dest)
        
    return bind_source
