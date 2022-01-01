# -*- coding: utf-8 -*-
# Copyright (c) 2021, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils.pdf import get_pdf
from frappe.utils.file_manager import save_file
from PyPDF2 import PdfFileWriter

def get_qrr_data(sinv):
    sinv = frappe.get_doc("Sales Invoice", sinv)
    
    if sinv.customer_address:
        pay_addr = frappe.get_doc("Address", sinv.customer_address)
        if pay_addr:
            # get values
            if pay_addr.postfach:
                # postfach
                pay_country = frappe.get_doc("Country", pay_addr.country)
                pay_country_code = pay_country.code.upper()
                if pay_addr.postfach_nummer:
                    postfach_nummer = pay_addr.postfach_nummer
                else:
                    postfach_nummer = ' '
                pay_address_line_detail = {
                    'name': sinv.customer,
                    'street': 'Postfach',
                    'number': postfach_nummer,
                    'pin': pay_addr.pincode,
                    'city': pay_addr.city,
                    'country': pay_country_code
                }
            else:
                # street
                pay_address_trimed = pay_addr.address_line1.strip()
                pay_address_array = pay_address_trimed.split(" ")
                pay_address_line_item_count = len(pay_address_array)
                pay_country = frappe.get_doc("Country", pay_addr.country)
                pay_country_code = pay_country.code.upper()
                pay_address_line_detail = {
                    'name': sinv.customer,
                    'street': '',
                    'number': '',
                    'pin': pay_addr.pincode,
                    'city': pay_addr.city,
                    'country': pay_country_code
                }
                for i in range(0, (pay_address_line_item_count - 1)):
                    pay_address_line_detail['street'] = pay_address_line_detail['street'] + " " + pay_address_array[i]
                pay_address_line_detail['number'] = pay_address_array[pay_address_line_item_count - 1]
        
        # set values
        payer_name = sinv.customer_name
        payer_street = pay_address_line_detail['street']
        payer_number = pay_address_line_detail['number']
        payer_pincode = pay_address_line_detail['pin']
        payer_town = pay_address_line_detail['city']
        payer_country = pay_address_line_detail['country']
        
        # check street vs number
        if not payer_street:
            if payer_number:
                payer_street = payer_number
                payer_number = ' '
    else:
        payer_name = False
        payer_street = False
        payer_number = False
        payer_pincode = False
        payer_town = False
        payer_country = False

    # receiver details
    if sinv.company_address:
        cmp_addr = frappe.get_doc("Address", sinv.company_address)
        if cmp_addr:
            # get values
            address_array = cmp_addr.address_line1.split(" ")
            address_line_item_count = len(address_array)
            cmp_country = frappe.get_doc("Country", cmp_addr.country)
            cmp_country_code = cmp_country.code.upper()
            cmp_address_line_detail = {
                'name': sinv.company,
                'street': '',
                'number': '',
                'plz': cmp_addr.plz,
                'city': cmp_addr.city,
                'country': cmp_country_code
            }
            for i in range(0, (address_line_item_count - 1)):
                cmp_address_line_detail['street'] = cmp_address_line_detail['street'] + " " + address_array[i]
            cmp_address_line_detail['number'] = address_array[address_line_item_count - 1]
            
            # set values
            receiver_name = cmp_address_line_detail['name'].replace("|", "I")
            receiver_street = cmp_address_line_detail['street']
            receiver_number = cmp_address_line_detail['number']
            receiver_pincode = cmp_address_line_detail['plz']
            receiver_town = cmp_address_line_detail['city']
            receiver_country = cmp_address_line_detail['country']
    else:
        receiver_name = False
        receiver_street = False
        receiver_number = False
        receiver_pincode = False
        receiver_town = False
        receiver_country = False

    # qrr dict
    qrr = {
        'top_position': '565px',
        'iban': 'CH68 3000 0002 8878 4152 8',
        'reference': sinv.esr_reference,
        'reference_type': 'QRR',
        'currency': sinv.currency,
        'amount': "{:,.2f}".format(sinv.outstanding_amount).replace(",", "'"),
        'message': sinv.name,
        'additional_information': ' ',
        'receiver_name': receiver_name,
        'receiver_street': receiver_street,
        'receiver_number': receiver_number,
        'receiver_country': receiver_country,
        'receiver_pincode': receiver_pincode,
        'receiver_town': receiver_town,
        'payer_name': payer_name,
        'payer_street': payer_street,
        'payer_number': payer_number,
        'payer_country': payer_country,
        'payer_pincode': payer_pincode,
        'payer_town': payer_town
    }
    
    return qrr

def create_qrr_watermark_pdf(sinv):
    qrr = get_qrr_data(sinv)
    html = frappe.render_template('templates/qrr_invoice/qrr_invoice.html', {'qrr': qrr})
    options = {
        "margin-top": "0mm",
        "margin-bottom": "0mm",
        "margin-left": "0mm",
        "margin-right": "0mm",
        "page-size": "A4",
        'background': None
    }
    qrr_pdf = get_pdf(html, options=options)
    file_name = '{sinv}.pdf'.format(sinv=sinv)
    save_file(file_name, qrr_pdf, 'Sales Invoice', sinv, is_private=1)
