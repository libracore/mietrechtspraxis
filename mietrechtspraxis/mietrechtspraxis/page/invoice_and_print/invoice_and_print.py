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
import math
from mietrechtspraxis.mietrechtspraxis.utils.qrr_reference import get_qrr_reference

@frappe.whitelist()
def get_show_data(sel_type):
    anz_abos = frappe.db.sql("""SELECT COUNT(`name`) AS `qty` FROM `tabmp Abo` WHERE `status` = 'Active' OR `status` = 'Actively terminated'""", as_dict=True)[0].qty
    anz_jahres_abos = frappe.db.sql("""SELECT COUNT(`name`) AS `qty` FROM `tabmp Abo` WHERE `type` = 'Jahres-Abo' AND `status` = 'Active'""", as_dict=True)[0].qty
    anz_jahres_abos_gekuendet = frappe.db.sql("""SELECT COUNT(`name`) AS `qty` FROM `tabmp Abo` WHERE `type` = 'Jahres-Abo' AND `status` = 'Actively terminated'""", as_dict=True)[0].qty
    anz_aktive_probe_abos = frappe.db.sql("""SELECT COUNT(`name`) AS `qty` FROM `tabmp Abo` WHERE `type` = 'Probe-Abo' AND `end_date` >= '{today}'""".format(today=today()), as_dict=True)[0].qty
    anz_gratis_abos = frappe.db.sql("""SELECT COUNT(`name`) AS `qty` FROM `tabmp Abo` WHERE `type` = 'Gratis-Abo' AND `status` = 'Active'""", as_dict=True)[0].qty
    
    return {
        'anz_abos': anz_abos,
        'anz_jahres_abos': anz_jahres_abos,
        'anz_jahres_abos_gekuendet': anz_jahres_abos_gekuendet,
        'anz_aktive_probe_abos': anz_aktive_probe_abos,
        'anz_gratis_abos': anz_gratis_abos
    }

@frappe.whitelist()
def create_invoices(date, year, selected_type, limit=False):
    args = {
        'date': date,
        'year': year,
        'selected_type': selected_type
    }
    enqueue("mietrechtspraxis.mietrechtspraxis.page.invoice_and_print.invoice_and_print._create_invoices", queue='long', job_name='Generierung Sammel-PDF (Rechnungslauf)', timeout=5000, **args)

def _create_invoices(date, year, selected_type, limit=500):
    # berechne batch anzahl auf basis von Limit
    filter_keine_doppel_rechnung = """SELECT `parent` FROM `tabmp Abo Invoice` WHERE `year` = '{year}'""".format(year=year)
    if selected_type == 'invoice_inkl':
        filter_invoice_typ = """`magazines_qty_ir` > 0"""
    else:
        filter_invoice_typ = """`magazines_qty_ir` = 0"""
    filter_ausland_adressen = """ AND `recipient_address` IN (SELECT `name` FROM `tabAddress` WHERE `country` != 'Schweiz')"""
    filter_inland_adressen = """ AND `recipient_address` IN (SELECT `name` FROM `tabAddress` WHERE `country` = 'Schweiz')"""
    
    ausland_abos_qty = frappe.db.sql("""SELECT
                                            COUNT(`name`) AS `qty`
                                        FROM `tabmp Abo`
                                        WHERE `type` = 'Jahres-Abo'
                                        AND `status` = 'Active'
                                        AND {filter_invoice_typ}
                                        AND `name` NOT IN ({filter_keine_doppel_rechnung})
                                        {filter_ausland_adressen} ORDER BY `magazines_qty_ir` ASC""".format(filter_invoice_typ=filter_invoice_typ,
                                                                                                            filter_keine_doppel_rechnung=filter_keine_doppel_rechnung,
                                                                                                            filter_ausland_adressen=filter_ausland_adressen), as_dict=True)[0].qty
    inland_abos_qty = frappe.db.sql("""SELECT
                                        COUNT(`name`) AS `qty`
                                    FROM `tabmp Abo`
                                    WHERE `type` = 'Jahres-Abo'
                                    AND `status` = 'Active'
                                    AND {filter_invoice_typ}
                                    AND `name` NOT IN ({filter_keine_doppel_rechnung})
                                    {filter_inland_adressen} ORDER BY `magazines_qty_ir` ASC""".format(filter_invoice_typ=filter_invoice_typ,
                                                                                                        filter_keine_doppel_rechnung=filter_keine_doppel_rechnung,
                                                                                                        filter_inland_adressen=filter_inland_adressen), as_dict=True)[0].qty
    total_qty = ausland_abos_qty + inland_abos_qty
    batch_anz = math.ceil((total_qty / limit))
    
    # batch verarbeitung
    for batch in range(batch_anz):
        # reset doppel-rechnungs-filter
        filter_keine_doppel_rechnung = """SELECT `parent` FROM `tabmp Abo Invoice` WHERE `year` = '{year}'""".format(year=year)
        qty_one = 0
        qty_multi = 0
        abos = []
        
        if limit:
            limit_filter = ' LIMIT {limit}'.format(limit=limit)
        else:
            limit_filter = ''
        
        ausland_abos = frappe.db.sql("""SELECT
                                            `name`
                                        FROM `tabmp Abo`
                                        WHERE `type` = 'Jahres-Abo'
                                        AND `status` = 'Active'
                                        AND {filter_invoice_typ}
                                        AND `name` NOT IN ({filter_keine_doppel_rechnung}){filter_ausland_adressen} ORDER BY `magazines_qty_ir` ASC{limit_filter}""".format(filter_invoice_typ=filter_invoice_typ, filter_keine_doppel_rechnung=filter_keine_doppel_rechnung, filter_ausland_adressen=filter_ausland_adressen, limit_filter=limit_filter), as_dict=True)
        for ausland_abo in ausland_abos:
            abos.append(ausland_abo)
        
        inland_abos = frappe.db.sql("""SELECT
                                            `name`
                                        FROM `tabmp Abo`
                                        WHERE `type` = 'Jahres-Abo'
                                        AND `status` = 'Active'
                                        AND {filter_invoice_typ}
                                        AND `name` NOT IN ({filter_keine_doppel_rechnung}){filter_inland_adressen} ORDER BY `magazines_qty_ir` ASC{limit_filter}""".format(filter_invoice_typ=filter_invoice_typ, filter_keine_doppel_rechnung=filter_keine_doppel_rechnung, filter_inland_adressen=filter_inland_adressen, limit_filter=limit_filter), as_dict=True)
        for inland_abo in inland_abos:
            abos.append(inland_abo)
        
        # create log file
        rm_log = frappe.get_doc({
            "doctype": "RM Log",
            'start': now(),
            'status': 'Job gestartet',
            'typ': 'Rechnungen (1+ Ex.)' if selected_type == 'invoice_inkl' else 'Rechnungen (0 Ex.)'
        })
        rm_log.insert()
        frappe.db.commit()
        
        for _abo in abos:
            abo = frappe.get_doc("mp Abo", _abo.name)
            sinv = create_invoice(abo.name, date)
            
            if sinv:
                # update abo
                row = abo.append('sales_invoices', {})
                row.sales_invoice = sinv['sinv']
                row.year = year
                abo.save(ignore_permissions=True)
                frappe.db.commit()
                
                # update log file
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
                    if selected_type == 'invoice_inkl':
                        if abo.magazines_qty_ir == 1:
                            qty_one += 1
                        else:
                            qty_multi += 1
           
        # create sammel pdf
        print_pdf(rm_log.name)
        
        # update log file
        rm_log.ende = now()
        rm_log.status = 'PDF erstellt'
        rm_log.qty_one = qty_one
        rm_log.qty_multi = qty_multi
        rm_log.save(ignore_permissions=True)
        frappe.db.commit()
        
def create_invoice(abo, date):
    from mietrechtspraxis.mietrechtspraxis.doctype.mp_abo.mp_abo import get_price
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
                    "qty": abo.qty_next_invoice,
                    "rate": get_price(frappe.db.get_single_value('mp Abo Settings', 'jahres_abo'), abo.invoice_recipient)
                }
            ]
        })
        new_sinv.insert()
        new_sinv.esr_reference = get_qrr_reference(sales_invoice=new_sinv.name, customer=abo.invoice_recipient)
        new_sinv.save(ignore_permissions=True)
        new_sinv.submit()
        frappe.db.commit()
    
        customer = frappe.get_doc("Customer", abo.invoice_recipient)
        if customer.korrespondenz == 'E-Mail':
            contact = frappe.get_doc("Contact", abo.recipient_contact)
            if contact.email_id:
                send_as_mail = True
                mail = contact.email_id
                if abo.magazines_qty_ir > 0:
                    printformat = 'Jahresrechnung inkl'
                else:
                    printformat = 'Jahresrechnung exkl'
                send_invoice_as_mail(new_sinv.name, mail, printformat)
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
    
def send_invoice_as_mail(sinv, address, printformat):
    try:
        frappe.sendmail([address],
            subject=  _("New Invoice: {sinv}").format(sinv=sinv),
            reply_to= 'office@mietrecht.ch',
            message = _("Please find attached Invoice {sinv}").format(sinv=sinv),
            attachments = [frappe.attach_print('Sales Invoice', sinv, file_name=sinv, print_format=printformat)])
    except:
        frappe.log_error(frappe.get_traceback(), 'send_invoice_as_mail failed: {sinv}'.format(sinv=sinv))

def print_pdf(rm_log):
    bind_source = "/assets/mietrechtspraxis/sinvs_for_print/{date}.pdf".format(date=rm_log)
    physical_path = "/home/frappe/frappe-bench/sites" + bind_source
    dest=str(physical_path)
    
    invoices = frappe.db.sql("""SELECT `sinv`, `anz` FROM `tabRM Log Sinv` WHERE `parent` = '{rm_log}' AND `pdf` = 1 AND `e_mail` != 1 ORDER BY `idx` ASC""".format(rm_log=rm_log), as_list=True)
    
    output = PdfFileWriter()
    
    for invoice in invoices:
        try:
            if int(invoice[1]) > 0:
                output = frappe.get_print("Sales Invoice", invoice[0], 'Jahresrechnung inkl', as_pdf = True, output = output, no_letterhead = 1, ignore_zugferd=True)
            else:
                output = frappe.get_print("Sales Invoice", invoice[0], 'Jahresrechnung exkl', as_pdf = True, output = output, no_letterhead = 1, ignore_zugferd=True)
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
def create_begleitschreiben():
    args = {}
    enqueue("mietrechtspraxis.mietrechtspraxis.page.invoice_and_print.invoice_and_print.create_begleitschreiben_kuendigung", queue='long', job_name='Begleitschreiben: Kündigungen', timeout=5000, **args)
    enqueue("mietrechtspraxis.mietrechtspraxis.page.invoice_and_print.invoice_and_print.create_begleitschreiben_gratis_abo", queue='long', job_name='Begleitschreiben: Gratis Abos', timeout=5000, **args)
    enqueue("mietrechtspraxis.mietrechtspraxis.page.invoice_and_print.invoice_and_print.create_begleitschreiben_jahres_abo", queue='long', job_name='Begleitschreiben: Jahres-Abo Empfänger', timeout=5000, **args)

def create_begleitschreiben_kuendigung():
    rm_log = frappe.get_doc({
        "doctype": "RM Log",
        'start': now(),
        'status': 'Job gestartet',
        'typ': 'Begleitschreiben: Kündigungen Ausland'
    })
    rm_log.insert()
    frappe.db.commit()
    
    ausland_datas = frappe.db.sql("""
                            SELECT
                                `view`.`abo` AS `abo`,
                                `view`.`anz` AS `anz`,
                                `view`.`recipient_name` AS `recipient_name`,
                                `view`.`recipient_contact` AS `recipient_contact`,
                                `view`.`recipient_address` AS `recipient_address`
                            FROM (
                                SELECT
                                    `name` AS `abo`,
                                    `magazines_qty_ir` AS `anz`,
                                    `invoice_recipient` AS `recipient_name`,
                                    `recipient_contact` AS `recipient_contact`,
                                    `recipient_address` AS `recipient_address`
                                FROM `tabmp Abo`
                                WHERE `status` = 'Actively terminated'
                                AND `type` = 'Jahres-Abo'
                                AND `magazines_qty_ir` > 0
                                AND `recipient_address` IN (SELECT `name` FROM `tabAddress` WHERE `country` != 'Schweiz')
                                UNION
                                SELECT
                                    `parent` AS `abo`,
                                    `magazines_qty_mr` AS `anz`,
                                    `magazines_recipient` AS `recipient_name`,
                                    `recipient_contact` AS `recipient_contact`,
                                    `recipient_address` AS `recipient_address`
                                FROM `tabmp Abo Recipient`
                                WHERE `parent` IN (
                                    SELECT
                                        `name`
                                    FROM `tabmp Abo`
                                    WHERE `status` = 'Actively terminated'
                                    AND `type` = 'Jahres-Abo'
                                )
                                AND `recipient_address` IN (SELECT `name` FROM `tabAddress` WHERE `country` != 'Schweiz')
                                UNION
                                SELECT
                                    `parent` AS `abo`,
                                    `magazines_qty_mr` AS `anz`,
                                    `magazines_recipient` AS `recipient_name`,
                                    `recipient_contact` AS `recipient_contact`,
                                    `recipient_address` AS `recipient_address`
                                FROM `tabmp Abo Recipient`
                                WHERE `parent` IN (
                                    SELECT
                                        `name`
                                    FROM `tabmp Abo`
                                    WHERE `status` = 'Active'
                                    AND `type` = 'Jahres-Abo'
                                )
                                AND `recipient_address` IN (SELECT `name` FROM `tabAddress` WHERE `country` != 'Schweiz')
                                AND `remove_recipient` IS NOT NULL
                            ) AS `view`
                            ORDER BY `view`.`anz` ASC
                            """, as_dict=True)
    for ausland_data in ausland_datas:
        begleit_row = rm_log.append('begleitungen', {})
        customer_name = frappe.get_doc("Customer", ausland_data.recipient_name).customer_name
        begleit_row.recipient_name = customer_name
        begleit_row.recipient_customer = ausland_data.recipient_name
        # tbd!
        begleit_row.pdf = 1
        #---------------------
        begleit_row.drucken = 1
        begleit_row.abo = ausland_data.abo
        begleit_row.anz = ausland_data.anz
        begleit_row.recipient_contact = ausland_data.recipient_contact
        begleit_row.recipient_address = ausland_data.recipient_address
        rm_log.save(ignore_permissions=True)
        frappe.db.commit()
    
    rm_log.ende = now()
    rm_log.status = 'PDF erstellt'
    rm_log.save(ignore_permissions=True)
    frappe.db.commit()
    
    rm_log = frappe.get_doc({
        "doctype": "RM Log",
        'start': now(),
        'status': 'Job gestartet',
        'typ': 'Begleitschreiben: Kündigungen Inland'
    })
    rm_log.insert()
    frappe.db.commit()
    
    inland_datas = frappe.db.sql("""
                            SELECT
                                `view`.`abo` AS `abo`,
                                `view`.`anz` AS `anz`,
                                `view`.`recipient_name` AS `recipient_name`,
                                `view`.`recipient_contact` AS `recipient_contact`,
                                `view`.`recipient_address` AS `recipient_address`
                            FROM (
                                SELECT
                                    `name` AS `abo`,
                                    `magazines_qty_ir` AS `anz`,
                                    `invoice_recipient` AS `recipient_name`,
                                    `recipient_contact` AS `recipient_contact`,
                                    `recipient_address` AS `recipient_address`
                                FROM `tabmp Abo`
                                WHERE `status` = 'Actively terminated'
                                AND `type` = 'Jahres-Abo'
                                AND `magazines_qty_ir` > 0
                                AND `recipient_address` IN (SELECT `name` FROM `tabAddress` WHERE `country` = 'Schweiz')
                                UNION
                                SELECT
                                    `parent` AS `abo`,
                                    `magazines_qty_mr` AS `anz`,
                                    `magazines_recipient` AS `recipient_name`,
                                    `recipient_contact` AS `recipient_contact`,
                                    `recipient_address` AS `recipient_address`
                                FROM `tabmp Abo Recipient`
                                WHERE `parent` IN (
                                    SELECT
                                        `name`
                                    FROM `tabmp Abo`
                                    WHERE `status` = 'Actively terminated'
                                    AND `type` = 'Jahres-Abo'
                                )
                                AND `recipient_address` IN (SELECT `name` FROM `tabAddress` WHERE `country` = 'Schweiz')
                                UNION
                                SELECT
                                    `parent` AS `abo`,
                                    `magazines_qty_mr` AS `anz`,
                                    `magazines_recipient` AS `recipient_name`,
                                    `recipient_contact` AS `recipient_contact`,
                                    `recipient_address` AS `recipient_address`
                                FROM `tabmp Abo Recipient`
                                WHERE `parent` IN (
                                    SELECT
                                        `name`
                                    FROM `tabmp Abo`
                                    WHERE `status` = 'Active'
                                    AND `type` = 'Jahres-Abo'
                                )
                                AND `recipient_address` IN (SELECT `name` FROM `tabAddress` WHERE `country` = 'Schweiz')
                                AND `remove_recipient` IS NOT NULL
                            ) AS `view`
                            ORDER BY `view`.`anz` ASC
                            """, as_dict=True)
    for inland_data in inland_datas:
        begleit_row = rm_log.append('begleitungen', {})
        customer_name = frappe.get_doc("Customer", inland_data.recipient_name).customer_name
        begleit_row.recipient_name = customer_name
        begleit_row.recipient_customer = inland_data.recipient_name
        # tbd!
        begleit_row.pdf = 1
        #---------------------
        begleit_row.drucken = 1
        begleit_row.abo = inland_data.abo
        begleit_row.anz = inland_data.anz
        begleit_row.recipient_contact = inland_data.recipient_contact
        begleit_row.recipient_address = inland_data.recipient_address
        rm_log.save(ignore_permissions=True)
        frappe.db.commit()
    
    rm_log.ende = now()
    rm_log.status = 'PDF erstellt'
    rm_log.save(ignore_permissions=True)
    frappe.db.commit()

def create_begleitschreiben_gratis_abo():
    qty_one = 0
    qty_multi = 0
    
    rm_log = frappe.get_doc({
        "doctype": "RM Log",
        'start': now(),
        'status': 'Job gestartet',
        'typ': 'Begleitschreiben: Gratis Abos Ausland'
    })
    rm_log.insert()
    frappe.db.commit()
    
    ausland_datas = frappe.db.sql("""
                            SELECT
                                `view`.`abo` AS `abo`,
                                `view`.`anz` AS `anz`,
                                `view`.`recipient_name` AS `recipient_name`,
                                `view`.`recipient_contact` AS `recipient_contact`,
                                `view`.`recipient_address` AS `recipient_address`
                            FROM (
                                SELECT
                                    `name` AS `abo`,
                                    `magazines_qty_ir` AS `anz`,
                                    `invoice_recipient` AS `recipient_name`,
                                    `recipient_contact` AS `recipient_contact`,
                                    `recipient_address` AS `recipient_address`
                                FROM `tabmp Abo`
                                WHERE `status` = 'Active'
                                AND `type` = 'Gratis-Abo'
                                AND `magazines_qty_ir` > 0
                                AND `recipient_address` IN (SELECT `name` FROM `tabAddress` WHERE `country` != 'Schweiz')
                            ) AS `view`
                            ORDER BY `view`.`anz` ASC
                            """, as_dict=True)
    for ausland_data in ausland_datas:
        if ausland_data.anz == 1:
            qty_one += 1
        else:
            qty_multi += 1
        begleit_row = rm_log.append('begleitungen', {})
        customer_name = frappe.get_doc("Customer", ausland_data.recipient_name).customer_name
        begleit_row.recipient_name = customer_name
        begleit_row.recipient_customer = ausland_data.recipient_name
        # tbd!
        begleit_row.pdf = 1
        #---------------------
        begleit_row.drucken = 1
        begleit_row.abo = ausland_data.abo
        begleit_row.anz = ausland_data.anz
        begleit_row.recipient_contact = ausland_data.recipient_contact
        begleit_row.recipient_address = ausland_data.recipient_address
        rm_log.save(ignore_permissions=True)
        frappe.db.commit()
    
    rm_log.ende = now()
    rm_log.status = 'PDF erstellt'
    rm_log.qty_one = qty_one
    rm_log.qty_multi = qty_multi
    rm_log.save(ignore_permissions=True)
    frappe.db.commit()
    
    qty_one = 0
    qty_multi = 0
    
    rm_log = frappe.get_doc({
        "doctype": "RM Log",
        'start': now(),
        'status': 'Job gestartet',
        'typ': 'Begleitschreiben: Gratis Abos Inland'
    })
    rm_log.insert()
    frappe.db.commit()
    
    inland_datas = frappe.db.sql("""
                            SELECT
                                `view`.`abo` AS `abo`,
                                `view`.`anz` AS `anz`,
                                `view`.`recipient_name` AS `recipient_name`,
                                `view`.`recipient_contact` AS `recipient_contact`,
                                `view`.`recipient_address` AS `recipient_address`
                            FROM (
                                SELECT
                                    `name` AS `abo`,
                                    `magazines_qty_ir` AS `anz`,
                                    `invoice_recipient` AS `recipient_name`,
                                    `recipient_contact` AS `recipient_contact`,
                                    `recipient_address` AS `recipient_address`
                                FROM `tabmp Abo`
                                WHERE `status` = 'Active'
                                AND `type` = 'Gratis-Abo'
                                AND `magazines_qty_ir` > 0
                                AND `recipient_address` IN (SELECT `name` FROM `tabAddress` WHERE `country` = 'Schweiz')
                            ) AS `view`
                            ORDER BY `view`.`anz` ASC
                            """, as_dict=True)
    for inland_data in inland_datas:
        if inland_data.anz == 1:
            qty_one += 1
        else:
            qty_multi += 1
        begleit_row = rm_log.append('begleitungen', {})
        customer_name = frappe.get_doc("Customer", inland_data.recipient_name).customer_name
        begleit_row.recipient_name = customer_name
        begleit_row.recipient_customer = inland_data.recipient_name
        # tbd!
        begleit_row.pdf = 1
        #---------------------
        begleit_row.drucken = 1
        begleit_row.abo = inland_data.abo
        begleit_row.anz = inland_data.anz
        begleit_row.recipient_contact = inland_data.recipient_contact
        begleit_row.recipient_address = inland_data.recipient_address
        rm_log.save(ignore_permissions=True)
        frappe.db.commit()
    
    rm_log.ende = now()
    rm_log.status = 'PDF erstellt'
    rm_log.qty_one = qty_one
    rm_log.qty_multi = qty_multi
    rm_log.save(ignore_permissions=True)
    frappe.db.commit()

def create_begleitschreiben_jahres_abo():
    qty_one = 0
    qty_multi = 0
    rm_log = frappe.get_doc({
        "doctype": "RM Log",
        'start': now(),
        'status': 'Job gestartet',
        'typ': 'Begleitschreiben: Jahres-Abo Empfänger Ausland'
    })
    rm_log.insert()
    frappe.db.commit()
    
    ausland_datas = frappe.db.sql("""
                            SELECT
                                `view`.`abo` AS `abo`,
                                `view`.`anz` AS `anz`,
                                `view`.`recipient_name` AS `recipient_name`,
                                `view`.`recipient_contact` AS `recipient_contact`,
                                `view`.`recipient_address` AS `recipient_address`
                            FROM (
                                SELECT
                                    `parent` AS `abo`,
                                    `magazines_qty_mr` AS `anz`,
                                    `magazines_recipient` AS `recipient_name`,
                                    `recipient_contact` AS `recipient_contact`,
                                    `recipient_address` AS `recipient_address`
                                FROM `tabmp Abo Recipient`
                                WHERE `parent` IN (
                                    SELECT
                                        `name`
                                    FROM `tabmp Abo`
                                    WHERE `status` = 'Active'
                                    AND `type` = 'Jahres-Abo'
                                )
                                AND `recipient_address` IN (SELECT `name` FROM `tabAddress` WHERE `country` != 'Schweiz')
                                AND `remove_recipient` IS NULL
                            ) AS `view`
                            ORDER BY `view`.`anz` ASC
                            """, as_dict=True)
    for ausland_data in ausland_datas:
        if ausland_data.anz == 1:
            qty_one += 1
        else:
            qty_multi += 1
        begleit_row = rm_log.append('begleitungen', {})
        customer_name = frappe.get_doc("Customer", ausland_data.recipient_name).customer_name
        begleit_row.recipient_name = customer_name
        begleit_row.recipient_customer = ausland_data.recipient_name
        # tbd!
        begleit_row.pdf = 1
        #---------------------
        begleit_row.drucken = 1
        begleit_row.abo = ausland_data.abo
        begleit_row.anz = ausland_data.anz
        begleit_row.recipient_contact = ausland_data.recipient_contact
        begleit_row.recipient_address = ausland_data.recipient_address
        rm_log.save(ignore_permissions=True)
        frappe.db.commit()
    
    rm_log.ende = now()
    rm_log.status = 'PDF erstellt'
    rm_log.qty_one = qty_one
    rm_log.qty_multi = qty_multi
    rm_log.save(ignore_permissions=True)
    frappe.db.commit()
    
    qty_one = 0
    qty_multi = 0
    rm_log = frappe.get_doc({
        "doctype": "RM Log",
        'start': now(),
        'status': 'Job gestartet',
        'typ': 'Begleitschreiben: Jahres-Abo Empfänger Inland'
    })
    rm_log.insert()
    frappe.db.commit()
    
    inland_datas = frappe.db.sql("""
                            SELECT
                                `view`.`abo` AS `abo`,
                                `view`.`anz` AS `anz`,
                                `view`.`recipient_name` AS `recipient_name`,
                                `view`.`recipient_contact` AS `recipient_contact`,
                                `view`.`recipient_address` AS `recipient_address`
                            FROM (
                                SELECT
                                    `parent` AS `abo`,
                                    `magazines_qty_mr` AS `anz`,
                                    `magazines_recipient` AS `recipient_name`,
                                    `recipient_contact` AS `recipient_contact`,
                                    `recipient_address` AS `recipient_address`
                                FROM `tabmp Abo Recipient`
                                WHERE `parent` IN (
                                    SELECT
                                        `name`
                                    FROM `tabmp Abo`
                                    WHERE `status` = 'Active'
                                    AND `type` = 'Jahres-Abo'
                                )
                                AND `recipient_address` IN (SELECT `name` FROM `tabAddress` WHERE `country` = 'Schweiz')
                                AND `remove_recipient` IS NULL
                            ) AS `view`
                            ORDER BY `view`.`anz` ASC
                            """, as_dict=True)
    for inland_data in inland_datas:
        if inland_data.anz == 1:
            qty_one += 1
        else:
            qty_multi += 1
        begleit_row = rm_log.append('begleitungen', {})
        customer_name = frappe.get_doc("Customer", inland_data.recipient_name).customer_name
        begleit_row.recipient_name = customer_name
        begleit_row.recipient_customer = inland_data.recipient_name
        # tbd!
        begleit_row.pdf = 1
        #---------------------
        begleit_row.drucken = 1
        begleit_row.abo = inland_data.abo
        begleit_row.anz = inland_data.anz
        begleit_row.recipient_contact = inland_data.recipient_contact
        begleit_row.recipient_address = inland_data.recipient_address
        rm_log.save(ignore_permissions=True)
        frappe.db.commit()
    
    rm_log.ende = now()
    rm_log.status = 'PDF erstellt'
    rm_log.qty_one = qty_one
    rm_log.qty_multi = qty_multi
    rm_log.save(ignore_permissions=True)
    frappe.db.commit()

@frappe.whitelist()
def create_versandkarten(date):
    args = {
        'date': date
    }
    enqueue("mietrechtspraxis.mietrechtspraxis.page.invoice_and_print.invoice_and_print._create_versandkarten", queue='long', job_name='Generierung Sammel-PDF (Versandkarten)', timeout=5000, **args)

def _create_versandkarten(date):
    data = []
    qty_one = 0
    qty_multi = 0
    save_counter = 1
    
    rm_log = frappe.get_doc({
        "doctype": "RM Log",
        'start': now(),
        'status': 'Job gestartet',
        'typ': 'Versandkarten'
    })
    rm_log.insert()
    frappe.db.commit()
    
    bind_source = "/assets/mietrechtspraxis/sinvs_for_print/{date}.pdf".format(date=rm_log.name)
    physical_path = "/home/frappe/frappe-bench/sites" + bind_source
    dest=str(physical_path)
    
    output = PdfFileWriter()
    
    ausland_empfaenger = frappe.db.sql("""
                        SELECT
                            `view`.`recipient`,
                            `view`.`abo`,
                            `view`.`anz`,
                            `view`.`recipient_contact`,
                            `view`.`recipient_address`
                        FROM (
                            SELECT
                                `tabmp Abo`.`invoice_recipient` AS `recipient`,
                                `tabmp Abo`.`name` AS `abo`,
                                `tabmp Abo`.`magazines_qty_ir` AS `anz`,
                                `tabmp Abo`.`recipient_contact`,
                                `tabmp Abo`.`recipient_address`
                            FROM `tabmp Abo`
                            WHERE
                            (`tabmp Abo`.`status` = 'Active' OR (`tabmp Abo`.`status` = 'Actively terminated' AND `tabmp Abo`.`end_date` <= '{date}'))
                            AND `tabmp Abo`.`recipient_address` IN (SELECT `name` FROM `tabAddress` WHERE `country` != 'Schweiz')
                            AND `tabmp Abo`.`magazines_qty_ir` > 0
                            UNION
                            SELECT
                                `tabmp Abo Recipient`.`magazines_recipient` AS `recipient`,
                                `tabmp Abo Recipient`.`parent` AS `abo`,
                                `tabmp Abo Recipient`.`magazines_qty_mr` AS `anz`,
                                `tabmp Abo Recipient`.`recipient_contact`,
                                `tabmp Abo Recipient`.`recipient_address`
                            FROM `tabmp Abo Recipient`
                            WHERE `tabmp Abo Recipient`.`recipient_address` IN (SELECT `name` FROM `tabAddress` WHERE `country` != 'Schweiz')
                            AND `tabmp Abo Recipient`.`parent` IN (
                                SELECT
                                    `name`
                                FROM `tabmp Abo`
                                WHERE `tabmp Abo`.`status` = 'Active' OR (`tabmp Abo`.`status` = 'Actively terminated' AND `tabmp Abo`.`end_date` <= '{date}')
                            )
                            AND `tabmp Abo Recipient`.`magazines_qty_mr` > 0
                        ) AS `view`
                        ORDER BY `view`.`anz` ASC
                    """.format(date=date), as_dict=True)
    for empfaenger in ausland_empfaenger:
        # create rm_log:
        try:
            customer = frappe.get_doc("Customer", empfaenger.recipient)
            versand_row = rm_log.append('versandkarten', {})
            versand_row.recipient_name = customer.customer_name
            versand_row.abo = empfaenger.abo
            versand_row.anz = empfaenger.anz
            versand_row.recipient_contact = empfaenger.recipient_contact
            versand_row.recipient_address = empfaenger.recipient_address
            if save_counter == 250:
                rm_log.save(ignore_permissions=True)
                frappe.db.commit()
                save_counter = 1
            else:
                save_counter += 1
            if empfaenger.anz > 1:
                qty_multi += 1
            else:
                qty_one += 1
        except:
            frappe.log_error(frappe.get_traceback(), 'create rm_log failed: {ref_dok}'.format(ref_dok=ausland_abo.name))
    
    rm_log.save(ignore_permissions=True)
    frappe.db.commit()
    
    inland_empfaenger = frappe.db.sql("""
                        SELECT
                            `view`.`recipient`,
                            `view`.`abo`,
                            `view`.`anz`,
                            `view`.`recipient_contact`,
                            `view`.`recipient_address`
                        FROM (
                            SELECT
                                `tabmp Abo`.`invoice_recipient` AS `recipient`,
                                `tabmp Abo`.`name` AS `abo`,
                                `tabmp Abo`.`magazines_qty_ir` AS `anz`,
                                `tabmp Abo`.`recipient_contact`,
                                `tabmp Abo`.`recipient_address`
                            FROM `tabmp Abo`
                            WHERE
                            (`tabmp Abo`.`status` = 'Active' OR (`tabmp Abo`.`status` = 'Actively terminated' AND `tabmp Abo`.`end_date` <= '{date}'))
                            AND `tabmp Abo`.`recipient_address` IN (SELECT `name` FROM `tabAddress` WHERE `country` = 'Schweiz')
                            UNION
                            SELECT
                                `tabmp Abo Recipient`.`magazines_recipient` AS `recipient`,
                                `tabmp Abo Recipient`.`parent` AS `abo`,
                                `tabmp Abo Recipient`.`magazines_qty_mr` AS `anz`,
                                `tabmp Abo Recipient`.`recipient_contact`,
                                `tabmp Abo Recipient`.`recipient_address`
                            FROM `tabmp Abo Recipient`
                            WHERE `tabmp Abo Recipient`.`recipient_address` IN (SELECT `name` FROM `tabAddress` WHERE `country` = 'Schweiz')
                            AND `tabmp Abo Recipient`.`parent` IN (
                                SELECT
                                    `name`
                                FROM `tabmp Abo`
                                WHERE `tabmp Abo`.`status` = 'Active' OR (`tabmp Abo`.`status` = 'Actively terminated' AND `tabmp Abo`.`end_date` <= '{date}')
                            )
                        ) AS `view`
                        ORDER BY `view`.`anz` ASC
                    """.format(date=date), as_dict=True)
    for empfaenger in inland_empfaenger:
        # create rm_log:
        try:
            customer = frappe.get_doc("Customer", empfaenger.recipient)
            versand_row = rm_log.append('versandkarten', {})
            versand_row.recipient_name = customer.customer_name
            versand_row.abo = empfaenger.abo
            versand_row.anz = empfaenger.anz
            versand_row.recipient_contact = empfaenger.recipient_contact
            versand_row.recipient_address = empfaenger.recipient_address
            if save_counter == 250:
                rm_log.save(ignore_permissions=True)
                frappe.db.commit()
                save_counter = 1
            else:
                save_counter += 1
            if empfaenger.anz > 1:
                qty_multi += 1
            else:
                qty_one += 1
        except:
            frappe.log_error(frappe.get_traceback(), 'create rm_log failed: {ref_dok}'.format(ref_dok=ausland_abo.name))
    
    rm_log.save(ignore_permissions=True)
    frappe.db.commit()
    
        
    try:
        output = frappe.get_print("RM Log", rm_log.name, 'RM Log Versandkarten', as_pdf = True, output = output, no_letterhead = 1, ignore_zugferd=True)
    except:
        frappe.log_error(frappe.get_traceback(), 'print_pdf failed: {ref_dok}'.format(ref_dok=rm_log.name))
    
    
    
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
    rm_log.qty_one = qty_one
    rm_log.qty_multi = qty_multi
    rm_log.status = 'PDF erstellt'
    rm_log.save(ignore_permissions=True)
    frappe.db.commit()
