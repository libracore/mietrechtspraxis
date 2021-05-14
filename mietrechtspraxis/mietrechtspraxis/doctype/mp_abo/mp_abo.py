# -*- coding: utf-8 -*-
# Copyright (c) 2021, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils.data import today, getdate

class mpAbo(Document):
    def validate(self):
        # calc qty
        total_qty = self.magazines_qty_ir
        for recipient in self.recipient:
            total_qty += recipient.magazines_qty_mr
        self.magazines_qty_total = total_qty
        
        # check status
        if self.end_date:
            if self.end_date >= getdate(today()):
                self.status = "Actively terminated"
            else:
                self.status = "Inactive"
        else:
            self.status = "Active"
        
        # set customer link for dashboard
        self.customer = self.invoice_recipient
    pass

@frappe.whitelist()
def get_address_html(customer, contact, address):
    customer = frappe.get_doc("Customer", customer)
    contact = frappe.get_doc("Contact", contact)
    address = frappe.get_doc("Address", address)
    
    html = ''
    
    if customer.customer_type == 'Individual':
        # contact
        salutation = contact.salutation + "<br>" if contact.salutation else ''
        first_name = contact.first_name + ' ' if contact.first_name != '-' else ''
        last_name = contact.last_name if contact.last_name != '-' else ''
        html += salutation + first_name + last_name + "<br>"
        
        # address
        address_line2 = address.address_line2 + "<br>" if address.address_line2 else ''
        html += str(address.address_line1) + "<br>" + address_line2 + str(address.pincode) + " " + str(address.city) + "<br>" + str(address.country)
    else:
        #tbd"
        html = 'tbd'
    
    return html

@frappe.whitelist()
def get_abo_list(customer):
    data = {}
    data["owner"] = frappe.db.sql("""SELECT * FROM `tabmp Abo` WHERE `invoice_recipient` = '{customer}'""".format(customer=customer), as_dict=True)
    data["recipient"] = frappe.db.sql("""SELECT
                                            *
                                        FROM `tabmp Abo`
                                        INNER JOIN `tabmp Abo Recipient` ON `tabmp Abo`.`name` = `tabmp Abo Recipient`.`parent`
                                        WHERE `tabmp Abo Recipient`.`magazines_recipient` = '{customer}'""".format(customer=customer), as_dict=True)
    return data

def set_inactive_status():
    abos = frappe.db.sql("""SELECT `name` FROM `tabmp Abo` WHERE `status` = 'Actively terminated' AND `end_date` < '{today}'""".format(today=today()), as_dict=True)
    for _abo in abos:
        abo = frappe.get_doc("mp Abo", _abo.name)
        abo.status = "Inactive"
        abo.save()

@frappe.whitelist()
def create_invoice(abo):
    abo = frappe.get_doc("mp Abo", abo)
    sinv = _create_invoice(abo.name)
    row = abo.append('sales_invoices', {})
    row.sales_invoice = sinv
    abo.save()
    return sinv
        
def _create_invoice(abo):
    abo = frappe.get_doc("mp Abo", abo)
    
    new_sinv = frappe.get_doc({
        "doctype": "Sales Invoice",
        "set_posting_time": 1,
        "posting_date": today(),
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
