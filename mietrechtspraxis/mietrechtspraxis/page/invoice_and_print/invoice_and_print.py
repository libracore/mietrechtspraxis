# -*- coding: utf-8 -*-
# Copyright (c) 2021, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, os
from frappe.utils.data import today, now
from frappe import publish_progress
from frappe import _
from PyPDF2 import PdfFileWriter
from frappe.utils.background_jobs import enqueue

@frappe.whitelist()
def get_show_data(sel_type):
    gratis_qty = frappe.db.sql("""SELECT SUM(`magazines_qty_total`) AS `qty` FROM `tabmp Abo` WHERE `type` = 'Gratis-Abo' AND `status` = 'Active'""", as_dict=True)[0].qty
    jahres_qty = frappe.db.sql("""SELECT SUM(`magazines_qty_total`) AS `qty` FROM `tabmp Abo` WHERE `type` = 'Jahres-Abo' AND `status` = 'Active'""", as_dict=True)[0].qty
    probe_qty = frappe.db.sql("""SELECT SUM(`magazines_qty_total`) AS `qty` FROM `tabmp Abo` WHERE `type` = 'Probe-Abo' AND `end_date` >= '{today}'""".format(today=today()), as_dict=True)[0].qty
    
    return {
        'gratis_qty': gratis_qty,
        'jahres_qty': jahres_qty,
        'probe_qty': probe_qty
    }

@frappe.whitelist()
def create_invoices(date, year, selected_type, limit=False):
    args = {
        'date': date,
        'year': year,
        'selected_type': selected_type,
        'limit': limit
    }
    enqueue("mietrechtspraxis.mietrechtspraxis.page.invoice_and_print.invoice_and_print._create_invoices", queue='long', job_name='Generierung Sammel-PDF (Rechnungslauf)', timeout=5000, **args)

def _create_invoices(date, year, selected_type, limit=False):
    # data = []
    qty_one = 0
    qty_multi = 0
    abos = []
    
    if limit:
        limit_filter = ' LIMIT {limit}'.format(limit=limit)
    else:
        limit_filter = ''
        
    filter_keine_doppel_rechnung = """SELECT `parent` FROM `tabmp Abo Invoice` WHERE `year` = '{year}'""".format(year=year)
    
    if selected_type == 'invoice_inkl':
        filter_invoice_typ = """`magazines_qty_ir` > 0"""
    else:
        filter_invoice_typ = """`magazines_qty_ir` = 0"""
    
    filter_ausland_adressen = """ AND `recipient_address` IN (SELECT `name` FROM `tabAddress` WHERE `country` != 'Switzerland')"""
    ausland_abos = frappe.db.sql("""SELECT
                                        `name`
                                    FROM `tabmp Abo`
                                    WHERE `type` = 'Jahres-Abo'
                                    AND `status` = 'Active'
                                    AND {filter_invoice_typ}
                                    AND `name` NOT IN ({filter_keine_doppel_rechnung}){filter_ausland_adressen} ORDER BY `magazines_qty_ir` ASC{limit_filter}""".format(filter_invoice_typ=filter_invoice_typ, filter_keine_doppel_rechnung=filter_keine_doppel_rechnung, filter_ausland_adressen=filter_ausland_adressen, limit_filter=limit_filter), as_dict=True)
    for ausland_abo in ausland_abos:
        abos.append(ausland_abo)
    
    filter_inland_adressen = """ AND `recipient_address` IN (SELECT `name` FROM `tabAddress` WHERE `country` = 'Switzerland')"""
    inland_abos = frappe.db.sql("""SELECT
                                        `name`
                                    FROM `tabmp Abo`
                                    WHERE `type` = 'Jahres-Abo'
                                    AND `status` = 'Active'
                                    AND {filter_invoice_typ}
                                    AND `name` NOT IN ({filter_keine_doppel_rechnung}){filter_inland_adressen} ORDER BY `magazines_qty_ir` ASC{limit_filter}""".format(filter_invoice_typ=filter_invoice_typ, filter_keine_doppel_rechnung=filter_keine_doppel_rechnung, filter_inland_adressen=filter_inland_adressen, limit_filter=limit_filter), as_dict=True)
    for inland_abo in inland_abos:
        abos.append(inland_abo)
    
    count = 0
    
    rm_log = frappe.get_doc({
        "doctype": "RM Log",
        'start': now(),
        'status': 'Job gestartet'
    })
    rm_log.insert()
    frappe.db.commit()
    
    for _abo in abos:
        abo = frappe.get_doc("mp Abo", _abo.name)
        sinv = create_invoice(abo.name, date)
        
        if sinv:
            row = abo.append('sales_invoices', {})
            row.sales_invoice = sinv['sinv']
            row.year = year
            abo.save(ignore_permissions=True)
            frappe.db.commit()
            
            sinv_row = rm_log.append('sinvs', {})
            sinv_row.sinv = sinv['sinv']
            if not sinv['send_as_mail']:
                sinv_row.pdf = 1
            else:
                sinv_row.e_mail = 1
            sinv_row.abo = abo.name
            sinv_row.anz = abo.magazines_qty_ir
            sinv_row.recipient_name = abo.recipient_name
            rm_log.save(ignore_permissions=True)
            frappe.db.commit()
            
            if not sinv['send_as_mail']:
                if abo.magazines_qty_total == 1:
                    qty_one += 1
                else:
                    qty_multi += 1
        
    print_pdf(rm_log.name)
    
    rm_log.ende = now()
    rm_log.status = 'PDF erstellt'
    rm_log.qty_one = qty_one
    rm_log.qty_multi = qty_multi
    rm_log.save(ignore_permissions=True)
    frappe.db.commit()
        
def create_invoice(abo, date):
    abo = frappe.get_doc("mp Abo", abo)
    try:
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
    except:
        frappe.log_error(frappe.get_traceback(), 'create_invoice failed: {abo}'.format(abo=abo.name))
        return False
    
def send_invoice_as_mail(sinv, address):
    try:
        frappe.sendmail([address],
            subject=  _("New Invoice: {sinv}").format(sinv=sinv),
            reply_to= 'office@mietrecht.ch',
            message = _("Please find attached Invoice {sinv}").format(sinv=sinv),
            attachments = [frappe.attach_print('Sales Invoice', sinv, file_name=sinv, print_format=frappe.db.get_single_value('mp Abo Settings', 'druckformat'))])
    except:
        frappe.log_error(frappe.get_traceback(), 'send_invoice_as_mail failed: {sinv}'.format(sinv=sinv))

@frappe.whitelist()
def print_pdf(rm_log):
    bind_source = "/assets/mietrechtspraxis/sinvs_for_print/{date}.pdf".format(date=rm_log)
    physical_path = "/home/frappe/frappe-bench/sites" + bind_source
    dest=str(physical_path)
    
    invoices = frappe.db.sql("""SELECT `sinv` FROM `tabRM Log Sinv` WHERE `parent` = '{rm_log}' AND `pdf` = 1 AND `e_mail` != 1 ORDER BY `idx` ASC""".format(rm_log=rm_log), as_list=True)
    
    output = PdfFileWriter()
    
    for invoice in invoices:
        try:
            output = frappe.get_print("Sales Invoice", invoice[0], frappe.db.get_single_value('mp Abo Settings', 'druckformat'), as_pdf = True, output = output, ignore_zugferd=True)
        except:
            frappe.log_error(frappe.get_traceback(), 'print_pdf failed: {sinv}'.format(sinv=invoice[0]))
        
    if isinstance(dest, str): # when dest is a file path
        destdir = os.path.dirname(dest)
        if destdir != '' and not os.path.isdir(destdir):
            os.makedirs(destdir)
        with open(dest, "wb") as w:
            output.write(w)
    else: # when dest is io.IOBase
        output.write(dest)
        
    return bind_source

@frappe.whitelist()
def create_begleitschreiben(limit=False):
    args = {
        'limit': limit
    }
    enqueue("mietrechtspraxis.mietrechtspraxis.page.invoice_and_print.invoice_and_print._create_begleitschreiben", queue='long', job_name='Generierung Sammel-PDF (Begleitschreiben)', timeout=5000, **args)

def _create_begleitschreiben(limit=False):
    data = []
    qty_one = 0
    qty_multi = 0
    gratis_abos = []
    gekuendete_abos = []
    
    rm_log = frappe.get_doc({
        "doctype": "RM Log",
        'start': now(),
        'status': 'Job gestartet'
    })
    rm_log.insert()
    frappe.db.commit()
    
    bind_source = "/assets/mietrechtspraxis/sinvs_for_print/{date}.pdf".format(date=rm_log.name)
    physical_path = "/home/frappe/frappe-bench/sites" + bind_source
    dest=str(physical_path)
    
    output = PdfFileWriter()
    
    if limit:
        limit_filter = ' LIMIT {limit}'.format(limit=limit)
    else:
        limit_filter = ''
    
    # Gratis Abos
    filter_ausland_adressen = """ AND `recipient_address` IN (SELECT `name` FROM `tabAddress` WHERE `country` != 'Switzerland')"""
    gratis_ausland_abos = frappe.db.sql("""SELECT
                                            `name`
                                        FROM `tabmp Abo`
                                        WHERE `type` = 'Gratis-Abo'
                                        AND `status` = 'Active'
                                        {filter_ausland_adressen} ORDER BY `magazines_qty_ir` ASC{limit_filter}""".format(filter_ausland_adressen=filter_ausland_adressen, limit_filter=limit_filter), as_dict=True)
    for ausland_abo in gratis_ausland_abos:
        try:
            output = frappe.get_print("mp Abo", ausland_abo.name, 'Weiterführung Gratis Abo', as_pdf = True, output = output, ignore_zugferd=True)
        except:
            frappe.log_error(frappe.get_traceback(), 'print_pdf failed: {ref_dok}'.format(ref_dok=ausland_abo.name))
    
    filter_inland_adressen = """ AND `recipient_address` IN (SELECT `name` FROM `tabAddress` WHERE `country` = 'Switzerland')"""
    gratis_inland_abos = frappe.db.sql("""SELECT
                                            `name`
                                        FROM `tabmp Abo`
                                        WHERE `type` = 'Gratis-Abo'
                                        AND `status` = 'Active'
                                        {filter_inland_adressen} ORDER BY `magazines_qty_ir` ASC{limit_filter}""".format(filter_inland_adressen=filter_inland_adressen, limit_filter=limit_filter), as_dict=True)
    for inland_abo in gratis_inland_abos:
        try:
            output = frappe.get_print("mp Abo", inland_abo.name, 'Weiterführung Gratis Abo', as_pdf = True, output = output, ignore_zugferd=True)
        except:
            frappe.log_error(frappe.get_traceback(), 'print_pdf failed: {ref_dok}'.format(ref_dok=inland_abo.name))
    
    # Gekündete Abos
    filter_ausland_adressen = """ AND `recipient_address` IN (SELECT `name` FROM `tabAddress` WHERE `country` != 'Switzerland')"""
    gekuendete_ausland_abos = frappe.db.sql("""SELECT
                                                `name`
                                            FROM `tabmp Abo`
                                            WHERE `status` = 'Actively terminated'
                                            {filter_ausland_adressen} ORDER BY `magazines_qty_ir` ASC{limit_filter}""".format(filter_ausland_adressen=filter_ausland_adressen, limit_filter=limit_filter), as_dict=True)
    for ausland_abo in gekuendete_ausland_abos:
        try:
            output = frappe.get_print("mp Abo", ausland_abo.name, 'Ablauf Jahres Abo', as_pdf = True, output = output, ignore_zugferd=True)
        except:
            frappe.log_error(frappe.get_traceback(), 'print_pdf failed: {ref_dok}'.format(ref_dok=ausland_abo.name))
    
    filter_inland_adressen = """ AND `recipient_address` IN (SELECT `name` FROM `tabAddress` WHERE `country` = 'Switzerland')"""
    gekuendete_inland_abos = frappe.db.sql("""SELECT
                                                `name`
                                            FROM `tabmp Abo`
                                            WHERE `status` = 'Actively terminated'
                                            {filter_inland_adressen} ORDER BY `magazines_qty_ir` ASC{limit_filter}""".format(filter_inland_adressen=filter_inland_adressen, limit_filter=limit_filter), as_dict=True)
    for inland_abo in gekuendete_inland_abos:
        try:
            output = frappe.get_print("mp Abo", inland_abo.name, 'Ablauf Jahres Abo', as_pdf = True, output = output, ignore_zugferd=True)
        except:
            frappe.log_error(frappe.get_traceback(), 'print_pdf failed: {ref_dok}'.format(ref_dok=inland_abo.name))
        
    # nur Empfänger
    nur_empfaenger = frappe.db.sql("""SELECT
                                        `name`
                                    FROM `tabmp Abo`
                                    WHERE `status` != 'Inactive'
                                    AND `name` IN (SELECT `parent` FROM `tabmp Abo Recipient`){limit_filter}""".format(limit_filter=limit_filter), as_dict=True)
    for _nur_empfaenger in nur_empfaenger:
        try:
            output = frappe.get_print("mp Abo", _nur_empfaenger.name, 'Begleitschreiben Empfänger', as_pdf = True, output = output, ignore_zugferd=True)
        except:
            frappe.log_error(frappe.get_traceback(), 'print_pdf failed: {ref_dok}'.format(ref_dok=_nur_empfaenger.name))
    
    
    
    
    if isinstance(dest, str): # when dest is a file path
        destdir = os.path.dirname(dest)
        if destdir != '' and not os.path.isdir(destdir):
            os.makedirs(destdir)
        with open(dest, "wb") as w:
            output.write(w)
    else: # when dest is io.IOBase
        output.write(dest)
    
    rm_log.ende = now()
    rm_log.status = 'PDF erstellt'
    rm_log.save(ignore_permissions=True)
    frappe.db.commit()
