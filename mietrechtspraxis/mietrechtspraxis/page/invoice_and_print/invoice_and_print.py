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
from mietrechtspraxis.mietrechtspraxis.page.invoice_and_print.utils import get_abos_for_invoicing, get_abos_for_begleitschreiben

@frappe.whitelist()
def get_show_data(sel_type):
    anz_abos_total = frappe.db.sql("""SELECT COUNT(`name`) AS `qty` FROM `tabmp Abo` WHERE `status` != 'Inactive'""", as_dict=True)[0].qty
    anz_abos_gekuendet = frappe.db.sql("""SELECT COUNT(`name`) AS `qty` FROM `tabmp Abo` WHERE `status` = 'Actively terminated'""", as_dict=True)[0].qty
    anz_abos_ungekuended = frappe.db.sql("""SELECT COUNT(`name`) AS `qty` FROM `tabmp Abo` WHERE `status` NOT IN ('Inactive', 'Actively terminated')""", as_dict=True)[0].qty

    empfaenger_physikalisch_jahr = frappe.db.sql("""SELECT COUNT(`name`) AS `qty` FROM `tabmp Abo Recipient` WHERE `abo_type` = 'Jahres-Abo'
                                                    AND `parent` IN (
                                                        SELECT `name`
                                                        FROM `tabmp Abo`
                                                        WHERE `status` != 'Inactive'
                                                    )
                                                    AND IFNULL(`magazines_qty_mr`, 0) > 0 """, as_dict=True)[0].qty
    
    empfaenger_digital_jahr = frappe.db.sql("""SELECT COUNT(`name`) AS `qty` FROM `tabmp Abo Recipient` WHERE `abo_type` = 'Jahres-Abo'
                                                    AND `parent` IN (
                                                        SELECT `name`
                                                        FROM `tabmp Abo`
                                                        WHERE `status` != 'Inactive'
                                                    )
                                                    AND `digital` = 1""", as_dict=True)[0].qty
    
    empfaenger_physikalisch_jahr_legi = frappe.db.sql("""SELECT COUNT(`name`) AS `qty` FROM `tabmp Abo Recipient` WHERE `abo_type` = 'Jahres-Legi-Abo'
                                                    AND `parent` IN (
                                                        SELECT `name`
                                                        FROM `tabmp Abo`
                                                        WHERE `status` != 'Inactive'
                                                    )
                                                    AND IFNULL(`magazines_qty_mr`, 0) > 0 """, as_dict=True)[0].qty
    
    empfaenger_digital_jahr_legi = frappe.db.sql("""SELECT COUNT(`name`) AS `qty` FROM `tabmp Abo Recipient` WHERE `abo_type` = 'Jahres-Legi-Abo'
                                                    AND `parent` IN (
                                                        SELECT `name`
                                                        FROM `tabmp Abo`
                                                        WHERE `status` != 'Inactive'
                                                    )
                                                    AND `digital` = 1""", as_dict=True)[0].qty
    
    empfaenger_physikalisch_probe = frappe.db.sql("""SELECT COUNT(`name`) AS `qty` FROM `tabmp Abo Recipient` WHERE `abo_type` = 'Probe-Abo'
                                                    AND `parent` IN (
                                                        SELECT `name`
                                                        FROM `tabmp Abo`
                                                        WHERE `status` != 'Inactive'
                                                    )
                                                    AND IFNULL(`magazines_qty_mr`, 0) > 0 """, as_dict=True)[0].qty
    
    empfaenger_digital_probe = frappe.db.sql("""SELECT COUNT(`name`) AS `qty` FROM `tabmp Abo Recipient` WHERE `abo_type` = 'Probe-Abo'
                                                    AND `parent` IN (
                                                        SELECT `name`
                                                        FROM `tabmp Abo`
                                                        WHERE `status` != 'Inactive'
                                                    )
                                                    AND `digital` = 1""", as_dict=True)[0].qty
    
    empfaenger_physikalisch_gratis = frappe.db.sql("""SELECT COUNT(`name`) AS `qty` FROM `tabmp Abo Recipient` WHERE `abo_type` = 'Gratis-Abo'
                                                    AND `parent` IN (
                                                        SELECT `name`
                                                        FROM `tabmp Abo`
                                                        WHERE `status` != 'Inactive'
                                                    )
                                                    AND IFNULL(`magazines_qty_mr`, 0) > 0 """, as_dict=True)[0].qty
    
    empfaenger_digital_gratis = frappe.db.sql("""SELECT COUNT(`name`) AS `qty` FROM `tabmp Abo Recipient` WHERE `abo_type` = 'Gratis-Abo'
                                                    AND `parent` IN (
                                                        SELECT `name`
                                                        FROM `tabmp Abo`
                                                        WHERE `status` != 'Inactive'
                                                    )
                                                    AND `digital` = 1""", as_dict=True)[0].qty

    return {
        'abo_uebersicht': {
            'anz_abos_total': anz_abos_total,
            'anz_abos_ungekuended': anz_abos_ungekuended,
            'anz_abos_gekuendet': anz_abos_gekuendet
        },
        'empfaenger': {
            'empfaenger_physikalisch_jahr': empfaenger_physikalisch_jahr,
            'empfaenger_digital_jahr': empfaenger_digital_jahr,
            'empfaenger_physikalisch_jahr_legi': empfaenger_physikalisch_jahr_legi,
            'empfaenger_digital_jahr_legi': empfaenger_digital_jahr_legi,
            'empfaenger_physikalisch_probe': empfaenger_physikalisch_probe,
            'empfaenger_digital_probe': empfaenger_digital_probe,
            'empfaenger_physikalisch_gratis': empfaenger_physikalisch_gratis,
            'empfaenger_digital_gratis': empfaenger_digital_gratis
        }
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
    total_qty = get_abos_for_invoicing(selected_type, year, qty=True)
    batch_anz = math.ceil((total_qty / limit))
    
    # batch verarbeitung
    for batch in range(batch_anz):
        qty_one = 0
        qty_multi = 0
        
        abos = get_abos_for_invoicing(selected_type, year, limit=limit)
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
            sinv = create_invoice(abo.name, date, inhaber_exemplar=_abo.inhaber_exemplar)
            
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
                sinv_row.anz = _abo.inhaber_exemplar
                sinv_row.recipient_name = abo.recipient_name
                rm_log.save(ignore_permissions=True)
                frappe.db.commit()
                
                if not sinv['send_as_mail']:
                    if selected_type == 'invoice_inkl':
                        if _abo.inhaber_exemplar == 1:
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
        
def create_invoice(abo, date, inhaber_exemplar=0):
    from mietrechtspraxis.mietrechtspraxis.doctype.mp_abo.mp_abo import get_price
    abo = frappe.get_doc("mp Abo", abo)
    try:
        items = []
        not_only_free = False
        if abo.magazines_qty_total > 0:
            items.append(
                {
                    "item_code": frappe.db.get_single_value('mp Abo Settings', 'jahres_abo'),
                    "qty": abo.magazines_qty_total,
                    "rate": get_price(frappe.db.get_single_value('mp Abo Settings', 'jahres_abo'), abo.invoice_recipient)
                }
            )
            not_only_free = True
        if abo.digital_qty > 0:
            items.append(
                {
                    "item_code": frappe.db.get_single_value('mp Abo Settings', 'jahres_abo_digital'),
                    "qty": abo.digital_qty,
                    "rate": get_price(frappe.db.get_single_value('mp Abo Settings', 'jahres_abo_digital'), abo.invoice_recipient)
                }
            )
            not_only_free = True
        if abo.gratis_print_qty > 0:
            items.append(
                {
                    "item_code": frappe.db.get_single_value('mp Abo Settings', 'gratis_abo'),
                    "qty": abo.gratis_print_qty,
                    "rate": get_price(frappe.db.get_single_value('mp Abo Settings', 'gratis_abo'), abo.invoice_recipient)
                }
            )
        if abo.gratis_digital_qty > 0:
            items.append(
                {
                    "item_code": frappe.db.get_single_value('mp Abo Settings', 'gratis_abo_digital'),
                    "qty": abo.gratis_digital_qty,
                    "rate": get_price(frappe.db.get_single_value('mp Abo Settings', 'gratis_abo_digital'), abo.invoice_recipient)
                }
            )
        if abo.legi_print_qty > 0:
            items.append(
                {
                    "item_code": frappe.db.get_single_value('mp Abo Settings', 'jahres_legi_abo'),
                    "qty": abo.legi_print_qty,
                    "rate": get_price(frappe.db.get_single_value('mp Abo Settings', 'jahres_legi_abo'), abo.invoice_recipient)
                }
            )
            not_only_free = True
        if abo.legi_digital_qty > 0:
            items.append(
                {
                    "item_code": frappe.db.get_single_value('mp Abo Settings', 'jahres_legi_abo_digital'),
                    "qty": abo.legi_digital_qty,
                    "rate": get_price(frappe.db.get_single_value('mp Abo Settings', 'jahres_legi_abo_digital'), abo.invoice_recipient)
                }
            )
            not_only_free = True
        if not_only_free:
            new_sinv = frappe.get_doc({
                "doctype": "Sales Invoice",
                "set_posting_time": 1,
                "posting_date": date,
                "posting_time": "00:00:00",
                "customer": abo.invoice_recipient,
                "customer_address": abo.recipient_address,
                "contact_person": abo.recipient_contact,
                "items": items,
                "inhaber_exemplar": inhaber_exemplar
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
        else:
            return False
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
    qty_one = 0
    qty_multi = 0
    rm_log = frappe.get_doc({
        "doctype": "RM Log",
        'start': now(),
        'status': 'Job gestartet',
        'typ': 'Begleitschreiben: Kündigungen Ausland'
    })
    rm_log.insert()
    frappe.db.commit()

    ausland_datas = get_abos_for_begleitschreiben('Kündigung', ausland=True)

    for ausland_data in ausland_datas:
        if ausland_data.anz == 1:
            qty_one += 1
        elif ausland_data.anz > 1:
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
    rm_log.qty_one = qty_one
    rm_log.qty_multi = qty_multi
    rm_log.status = 'PDF erstellt'
    rm_log.save(ignore_permissions=True)
    frappe.db.commit()
    
    qty_one = 0
    qty_multi = 0
    rm_log = frappe.get_doc({
        "doctype": "RM Log",
        'start': now(),
        'status': 'Job gestartet',
        'typ': 'Begleitschreiben: Kündigungen Inland'
    })
    rm_log.insert()
    frappe.db.commit()

    inland_datas = ausland_datas = get_abos_for_begleitschreiben('Kündigung')

    for inland_data in inland_datas:
        if inland_data.anz == 1:
            qty_one += 1
        elif inland_data.anz > 1:
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
    rm_log.qty_one = qty_one
    rm_log.qty_multi = qty_multi
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

    ausland_datas = ausland_datas = get_abos_for_begleitschreiben('Gratis-Abo', ausland=True)

    for ausland_data in ausland_datas:
        if ausland_data.anz == 1:
            qty_one += 1
        elif ausland_data.anz > 1:
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

    inland_datas = ausland_datas = get_abos_for_begleitschreiben('Gratis-Abo')

    for inland_data in inland_datas:
        if inland_data.anz == 1:
            qty_one += 1
        elif inland_data.anz > 1:
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

    ausland_datas = ausland_datas = get_abos_for_begleitschreiben('Jahres-Abo', ausland=True)

    for ausland_data in ausland_datas:
        if ausland_data.anz == 1:
            qty_one += 1
        elif ausland_data.anz > 1:
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

    inland_datas = ausland_datas = get_abos_for_begleitschreiben('Jahres-Abo')
    for inland_data in inland_datas:
        if inland_data.anz == 1:
            qty_one += 1
        elif inland_data.anz > 1:
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
def start_get_versandkarten_empfaenger(date, txt, printformat=None):
    args = {
        'date': date,
        'txt': txt,
        'printformat': printformat
    }
    enqueue("mietrechtspraxis.mietrechtspraxis.page.invoice_and_print.invoice_and_print.get_versandkarten_empfaenger", queue='long', job_name='Generierung Sammel-PDF (Versandkarten)', timeout=5000, **args)

def get_versandkarten_empfaenger(date, txt, printformat=None):
    abo_query = """
        SELECT `name`
        FROM `tabmp Abo`
        WHERE (
            `status` = 'Active'
            OR (
                `status` = 'Actively terminated'
                AND `end_date` > '{0}'
            )
        )
    """.format(date)

    inland_query = """
        SELECT `name`
        FROM `tabAddress`
        WHERE `country` = 'Schweiz'
    """

    ausland_query = """
        SELECT `name`
        FROM `tabAddress`
        WHERE `country` != 'Schweiz'
    """

    empfaenger_ausland = frappe.db.sql("""
                                SELECT
                                    `magazines_recipient` AS `customer`,
                                    `recipient_contact` AS `contact`,
                                    `recipient_address` AS `address`,
                                    `magazines_qty_mr` AS `qty`,
                                    `parent` AS `abo`
                                FROM `tabmp Abo Recipient`
                                WHERE `parent` IN (
                                    {abo_query}
                                )
                                AND `recipient_address` IN (
                                    {ausland_query}
                                )
                                AND `magazines_qty_mr` > 0
                                AND (
                                    `remove_recipient` > '{date}'
                                    OR
                                    `remove_recipient` IS NULL
                                )
                                ORDER BY `magazines_qty_mr` DESC
                               """.format(abo_query=abo_query, ausland_query=ausland_query, date=date), as_dict=True)

    empfaenger_inland = frappe.db.sql("""
                                SELECT
                                    `magazines_recipient` AS `customer`,
                                    `recipient_contact` AS `contact`,
                                    `recipient_address` AS `address`,
                                    `magazines_qty_mr` AS `qty`,
                                    `parent` AS `abo`
                                FROM `tabmp Abo Recipient`
                                WHERE `parent` IN (
                                    {abo_query}
                                )
                                AND `recipient_address` IN (
                                    {inland_query}
                                )
                                AND `magazines_qty_mr` > 0
                                AND (
                                    `remove_recipient` > '{date}'
                                    OR
                                    `remove_recipient` IS NULL
                                )
                                ORDER BY `magazines_qty_mr` DESC
                               """.format(abo_query=abo_query, inland_query=inland_query, date=date), as_dict=True)

    qty_one = 0
    qty_multi = 0
    save_counter = 1
    batch_counter = 1

    rm_log = create_rm_log_batch('Versandkarten', txt)

    for empfaenger in empfaenger_ausland:
        # create ggf. new rm_log:
        if batch_counter > 500:
            save_and_print_rm_log(rm_log, qty_one, qty_multi, printformat)
            rm_log = create_rm_log_batch('Versandkarten', txt)
            qty_one = 0
            qty_multi = 0
            save_counter = 1
            batch_counter = 1
        try:
            customer = frappe.get_doc("Customer", empfaenger.customer)
            versand_row = rm_log.append('versandkarten', {})
            versand_row.recipient_name = customer.customer_name
            versand_row.abo = empfaenger.abo
            versand_row.anz = empfaenger.qty
            versand_row.recipient_contact = empfaenger.contact
            versand_row.recipient_address = empfaenger.address
            if save_counter == 250:
                rm_log.save(ignore_permissions=True)
                frappe.db.commit()
                save_counter = 1
            else:
                save_counter += 1
            if empfaenger.qty > 1:
                qty_multi += 1
            else:
                qty_one += 1
            batch_counter += 1
        except:
            frappe.log_error(frappe.get_traceback(), 'create rm_log failed: {ref_dok}'.format(ref_dok=empfaenger.abo))
    
    for empfaenger in empfaenger_inland:
        # create ggf. new rm_log:
        if batch_counter > 500:
            save_and_print_rm_log(rm_log, qty_one, qty_multi, printformat)
            rm_log = create_rm_log_batch('Versandkarten', txt)
            qty_one = 0
            qty_multi = 0
            save_counter = 1
            batch_counter = 1
        try:
            customer = frappe.get_doc("Customer", empfaenger.customer)
            versand_row = rm_log.append('versandkarten', {})
            versand_row.recipient_name = customer.customer_name
            versand_row.abo = empfaenger.abo
            versand_row.anz = empfaenger.qty
            versand_row.recipient_contact = empfaenger.contact
            versand_row.recipient_address = empfaenger.address
            if save_counter == 250:
                rm_log.save(ignore_permissions=True)
                frappe.db.commit()
                save_counter = 1
            else:
                save_counter += 1
            if empfaenger.qty > 1:
                qty_multi += 1
            else:
                qty_one += 1
            batch_counter += 1
        except:
            frappe.log_error(frappe.get_traceback(), 'create rm_log failed: {ref_dok}'.format(ref_dok=empfaenger.abo))
    
    if batch_counter > 1:
        save_and_print_rm_log(rm_log, qty_one, qty_multi, printformat)

def create_rm_log_batch(typ, txt):
    rm_log = frappe.get_doc({
        "doctype": "RM Log",
        'start': now(),
        'status': 'Job gestartet',
        'typ': typ,
        'versandkartentext': txt
    })
    rm_log.insert()
    frappe.db.commit()
    return rm_log

def save_and_print_rm_log(rm_log, qty_one, qty_multi, printformat=None):
    rm_log.save(ignore_permissions=True)
    frappe.db.commit()

    bind_source = "/assets/mietrechtspraxis/sinvs_for_print/{date}.pdf".format(date=rm_log.name)
    physical_path = "/home/frappe/frappe-bench/sites" + bind_source
    dest=str(physical_path)
    
    output = PdfFileWriter()

    try:
        if printformat:
            durckformat = printformat
        else:
            durckformat = 'RM Log Versandkarten'
        output = frappe.get_print("RM Log", rm_log.name, durckformat, as_pdf = True, output = output, no_letterhead = 1, ignore_zugferd=True)
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