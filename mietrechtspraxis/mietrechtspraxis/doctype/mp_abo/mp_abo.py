# -*- coding: utf-8 -*-
# Copyright (c) 2021, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils.data import today

class mpAbo(Document):
    def validate(self):
        # calc qty
        total_qty = self.magazines_qty_ir
        for recipient in self.recipient:
            total_qty += recipient.magazines_qty_mr
        self.magazines_qty_total = total_qty
        
        # check status
        if self.end_date:
            if self.end_date >= today():
                self.status = "Actively terminated"
            else:
                self.status = "Inactive"
        else:
            self.status = "Active"
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
