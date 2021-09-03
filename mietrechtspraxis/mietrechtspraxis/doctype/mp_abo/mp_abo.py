# -*- coding: utf-8 -*-
# Copyright (c) 2021, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils.data import today, getdate

class mpAbo(Document):
    def onload(self):
        for sinv_row in self.sales_invoices:
            sinv = frappe.get_doc("Sales Invoice", sinv_row.sales_invoice)
            sinv_row.status = sinv.status
        
    def validate(self):
        # calc qty
        total_qty = self.magazines_qty_ir
        for recipient in self.recipient:
            total_qty += recipient.magazines_qty_mr
        self.magazines_qty_total = total_qty
        
        # check status
        if self.end_date:
            if getdate(self.end_date) >= getdate(today()):
                self.status = "Actively terminated"
            else:
                self.status = "Inactive"
        else:
            self.status = "Active"
        
        # set customer link for dashboard
        self.customer = self.invoice_recipient
        
        # check optional receipients
        if self.type == 'Probe-Abo':
            if len(self.recipient) >= 1:
                frappe.throw("Ein Probe-Abo kann nicht mehrere Empfänger haben.")
    pass

@frappe.whitelist()
def get_address_html(customer, contact, address):
    customer = frappe.get_doc("Customer", customer)
    contact = frappe.get_doc("Contact", contact)
    address = frappe.get_doc("Address", address)
    
    data = {
        'customer_type': customer.customer_type,
        'customer_name': customer.customer_name,
        'customer_addition': customer.customer_addition,
        'zusatz': address.zusatz,
        'salutation': contact.salutation,
        'first_name': contact.first_name,
        'last_name': contact.last_name,
        'postfach': address.postfach,
        'strasse': address.strasse,
        'postfach_nummer': address.postfach_nummer,
        'plz': address.plz,
        'city': address.city,
        'email_id': contact.email_id,
        'phone': contact.phone,
        'mobile_no': contact.mobile_no
    }
    
    return frappe.render_template('templates/address_and_contact/address_and_contact.html', data)

@frappe.whitelist()
def get_abo_list(customer):
    data = {}
    data["owner"] = frappe.db.sql("""SELECT * FROM `tabmp Abo` WHERE `invoice_recipient` = '{customer}'""".format(customer=customer), as_dict=True)
    data["recipient"] = frappe.db.sql("""SELECT
                                            *
                                        FROM `tabmp Abo`
                                        INNER JOIN `tabmp Abo Recipient` ON `tabmp Abo`.`name` = `tabmp Abo Recipient`.`parent`
                                        WHERE `tabmp Abo Recipient`.`magazines_recipient` = '{customer}'""".format(customer=customer), as_dict=True)
    return frappe.render_template('templates/customer/abo_table.html', data)

def set_inactive_status():
    abos = frappe.db.sql("""SELECT `name` FROM `tabmp Abo` WHERE `status` = 'Actively terminated' AND `end_date` < '{today}'""".format(today=today()), as_dict=True)
    for _abo in abos:
        # set status
        abo = frappe.get_doc("mp Abo", _abo.name)
        abo.status = "Inactive"
        abo.save()
        # reset mp user login
        if abo.recipient_contact:
            contact = frappe.get_doc("Contact", abo.recipient_contact)
            contact.mp_username = ''
            contact.mp_password = ''
            contact.save()
        for recipient in abo.recipient:
            if recipient.recipient_contact:
                contact = frappe.get_doc("Contact", recipient.recipient_contact)
                contact.mp_username = ''
                contact.mp_password = ''
                contact.save()

@frappe.whitelist()
def create_invoice(abo):
    abo = frappe.get_doc("mp Abo", abo)
    sinv = _create_invoice(abo.name)
    row = abo.append('sales_invoices', {})
    row.sales_invoice = sinv
    row.year = abo.start_date.strftime("%Y")
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

@frappe.whitelist()
def create_batch_pdf(abo):
    abo = frappe.get_doc("mp Abo", abo)
    # tbd

@frappe.whitelist()
def create_user_login(abo):
    abo = frappe.get_doc("mp Abo", abo)
    if abo.recipient_contact:
        contact = frappe.get_doc("Contact", abo.recipient_contact)
        contact.mp_username = abo.name
        contact.mp_password = create_random_pw()
        contact.save()
    for recipient in abo.recipient:
        if recipient.recipient_contact:
            contact = frappe.get_doc("Contact", recipient.recipient_contact)
            contact.mp_username = abo.name
            contact.mp_password = create_random_pw()
            contact.save()
    abo.user_login_createt = 1
    abo.save()
            
def create_random_pw():
    import random
    conso = ['b','c','d','f','g','h','j','k','l','m','n','p','r','s','t','v','w','x','y','z']
    vocal = ['a','e','i','o','u']
    spchars = ['*','-','+','?']
    numbers = ['1','2','3','4','5','6','7','8','9']
    
    def get_covoco_block():
        return ''.join([random.choice(conso).upper(), random.choice(vocal), random.choice(conso)])
        
    password = ''.join([
        get_covoco_block(),
        random.choice(spchars),
        ''.join([random.choice(numbers), random.choice(numbers)]),
        random.choice(spchars),
        get_covoco_block()])
    return password
