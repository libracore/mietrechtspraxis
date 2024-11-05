# -*- coding: utf-8 -*-
# Copyright (c) 2021, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils.data import today, getdate
from mietrechtspraxis.mietrechtspraxis.utils.qrr_reference import get_qrr_reference
from frappe.utils import cint

class mpAbo(Document):
    def onload(self):
        for sinv_row in self.sales_invoices:
            sinv = frappe.get_doc("Sales Invoice", sinv_row.sales_invoice)
            sinv_row.status = sinv.status
        
    def validate(self):
        # calc qty
        total_qty = 0
        total_digital = 0
        for recipient in self.recipient:
            total_qty += recipient.magazines_qty_mr
            if recipient.digital and recipient.magazines_qty_mr == 0:
                total_digital += 1
        self.magazines_qty_total = total_qty
        self.digital_qty = total_digital
        
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
        
        # check receipients
        if self.status != "Inactive":
            if len(self.recipient) < 1:
                frappe.throw("Ein Abo muss mind. ein Empfänger haben.")
        
        #check for not allowed combination
        for recipient in self.recipient:
            if recipient.magazines_qty_mr < 1 and cint(recipient.digital) == 0:
                frappe.throw("Zeile {0}: Ungültige Kombination (Anz. Magazine 0 & Nicht Digital)".format(recipient.idx))
    
    def on_update(self):
        # check valid_mp_web_user_abo
        valid_mp_web_user_abo(abo=self)
    
    def fetch_inhaber(self):
        row = self.append('recipient', {})
        row.abo_type = 'Jahres-Abo'
        row.magazines_qty_mr = 1
        row.magazines_recipient = self.invoice_recipient
        row.recipient_contact = self.recipient_contact
        row.recipient_address = self.recipient_address
        self.save()


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
        
        disabled_customer = False
        if abo.invoice_recipient:
            customer = frappe.get_doc("Customer", abo.invoice_recipient)
            if customer.disabled:
                disabled_customer = True
                customer.disabled = 0
                customer.save()
                
        disabled_address = False
        if abo.recipient_address:
            address = frappe.get_doc("Address", abo.recipient_address)
            if address.disabled:
                disabled_address = True
                address.disabled = 0
                address.save()
        
        abo.save()
        
        if disabled_address:
            address.disabled = 1
            address.save()
        
        # reset mp user login
        if abo.recipient_contact:
            contact = frappe.get_doc("Contact", abo.recipient_contact)
            
            disabled_address = False
            if contact.address:
                address = frappe.get_doc("Address", contact.address)
                if address.disabled:
                    disabled_address = True
                    address.disabled = 0
                    address.save()
            
            contact.mp_username = ''
            contact.mp_password = ''
            contact.save()
            
            if disabled_address:
                address.disabled = 1
                address.save()
        
        if disabled_customer:
            customer.disabled = 1
            customer.save()
        
        for recipient in abo.recipient:
            if recipient.recipient_contact:
                disabled_customer = False
                if recipient.magazines_recipient:
                    customer = frappe.get_doc("Customer", recipient.magazines_recipient)
                    
                    if customer.disabled:
                        disabled_customer = True
                        customer.disabled = 0
                        customer.save()
                
                contact = frappe.get_doc("Contact", recipient.recipient_contact)
                
                disabled_address = False
                if contact.address:
                    address = frappe.get_doc("Address", contact.address)
                    if address.disabled:
                        disabled_address = True
                        address.disabled = 0
                        address.save()
                
                contact.mp_username = ''
                contact.mp_password = ''
                
                contact.save()
                
                if disabled_address:
                    address.disabled = 1
                    address.save()
                
                if disabled_customer:
                    customer.disabled = 1
                    customer.save()

def remove_recipient():
    frappe.db.sql("""SET SQL_SAFE_UPDATES = 0""", as_list=True)
    frappe.db.sql("""DELETE FROM `tabmp Abo Recipient` WHERE `remove_recipient` = '{today}'""".format(today=today()), as_list=True)
    frappe.db.sql("""SET SQL_SAFE_UPDATES = 1""", as_list=True)
    frappe.db.commit()

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
    items = []
    for recipient in abo.recipient:
        abo_type = recipient.abo_type.lower().replace("-", "_") if cint(recipient.digital) == 0 else "{0}_digital".format(recipient.abo_type.lower().replace("-", "_"))
        item_code = frappe.db.get_single_value('mp Abo Settings', abo_type)
        qty = recipient.magazines_qty_mr
        if cint(recipient.digital) == 1:
            if qty == 0:
                qty = 1
        items.append({
            "item_code": item_code,
            "qty": qty,
            "rate": get_price(item_code, abo.invoice_recipient)
        })
    
    new_sinv = frappe.get_doc({
        "doctype": "Sales Invoice",
        "set_posting_time": 1,
        "posting_date": today(),
        "posting_time": "00:00:00",
        "customer": abo.invoice_recipient,
        "customer_address": abo.recipient_address,
        "contact_person": abo.recipient_contact,
        "items": items
    })
    new_sinv.insert()
    new_sinv.esr_reference = get_qrr_reference(sales_invoice=new_sinv.name, customer=abo.invoice_recipient)
    new_sinv.save(ignore_permissions=True)
    new_sinv.submit()
    frappe.db.commit()
    
    return new_sinv.name
    
def get_price(item_code, customer):
    customer_group = frappe.get_doc("Customer", customer).customer_group
    prices = frappe.db.sql("""SELECT
                                    `rate`
                                FROM `tabPricing Rule`
                                WHERE `applicable_for` = 'Customer Group'
                                AND `selling` = 1
                                AND customer_group = '{customer_group}'
                                AND `rate_or_discount` = 'Rate'
                                AND `valid_from` <= CURDATE()
                                AND (`valid_upto` >= CURDATE() OR `valid_upto` IS NULL)
                                AND `name` IN (SELECT `parent` FROM `tabPricing Rule Item Code` WHERE `item_code` = '{item_code}')""".format(customer_group=customer_group, item_code=item_code), as_dict=True)
    if prices:
        return prices[0].rate
    else:
        return None

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

def valid_mp_web_user_abo(abo=None, user=None):
    if not abo and not user:
        return
    
    if abo:
        user = get_user_from_contact(abo.recipient_contact)
        if user:
            contacts = get_contacts_from_user(user)
            check_mp_web_user_based_on_contacts(contacts, user)

        for recipient_contact in abo.recipient:
            user = get_user_from_contact(recipient_contact.recipient_contact)
            if user:
                contacts = get_contacts_from_user(user)
                check_mp_web_user_based_on_contacts(contacts, user)
        return
    
    if user:
        contacts = get_contacts_from_user(user)
        check_mp_web_user_based_on_contacts(contacts, user)
        return


def check_mp_web_user_based_on_contacts(contacts, username):
    has_activ_abo = False
    for contact in contacts:
        c = frappe.get_doc("Contact", contact[0])
        if c.mp_web_user:
            activ_recipient = frappe.db.sql("""
                                            SELECT COUNT(`mar`.`name`) AS `qty`
                                            FROM `tabmp Abo Recipient` AS `mar`
                                            LEFT JOIN `tabmp Abo` AS `ma` ON `mar`.`parent` = `ma`.`name`
                                            WHERE `ma`.`status` != 'Inactive'
                                            AND `mar`.`recipient_contact` = '{0}'
                                            AND `mar`.`digital` = 1
                                            """.format(contact[0]), as_dict=True)
            
            if activ_recipient[0].qty > 0:
                has_activ_abo = True
    user = frappe.get_doc("User", username)
    if has_activ_abo:
        if cint(user.enabled) != 1:
            enable_disable_user(user, 1)
    else:
        if cint(user.enabled) == 1:
            enable_disable_user(user, 0)
        
    return

def get_contacts_from_user(user):
    if not user:
        return []
    
    contacts = frappe.db.sql("""
                             SELECT `name`
                             FROM `tabContact`
                             WHERE `mp_web_user` = '{0}'
                             """.format(user), as_list=True)
    return contacts

def get_user_from_contact(contact):
    c = frappe.get_doc("Contact", contact)
    if c.mp_web_user:
        return c.mp_web_user
    else:
        return False

def enable_disable_user(user, status):
    user.enabled = status
    user.save(ignore_permissions=True)
    return

# Diese Funktion wird anstelle eines Patches dafür verwendet, die bestehenden Abos in die neue Struktur zu migrieren.
# Execute with bench --site [site_name] execute mietrechtspraxis.mietrechtspraxis.doctype.mp_abo.mp_abo.migrate_old_abos
def migrate_old_abos():
    # Abos bei denen Inhaber = Empfänger
    abos = frappe.db.sql("""
                            SELECT `name`
                            FROM `tabmp Abo`
                            WHERE `status` != "Inactive"
                            AND `magazines_qty_ir` > 0
                        """, as_dict=True)
    total = len(abos)
    loop = 1
    for abo in abos:
        print("Round 1: {0} von {1}".format(loop, total))
        a = frappe.get_doc("mp Abo", abo.name)
        found_inhaber = False
        for recipient in a.recipient:
            recipient.abo_type = a.type
            recipient.digital = 1
            if recipient.magazines_recipient == a.invoice_recipient:
                if recipient.recipient_contact == a.recipient_contact:
                    if recipient.recipient_address == a.recipient_address:
                        found_inhaber = True
        if not found_inhaber:
            row = a.append('recipient', {})
            row.abo_type = a.type
            row.digital = 1
            row.magazines_qty_mr = a.magazines_qty_ir
            row.magazines_recipient = a.invoice_recipient
            row.recipient_contact = a.recipient_contact
            row.recipient_address = a.recipient_address
        a.save()
        loop += 1
    
    # Abos bei denen Inhaber != Empfänger
    abos = frappe.db.sql("""
                            SELECT `name`
                            FROM `tabmp Abo`
                            WHERE `status` != "Inactive"
                            AND (
                                `magazines_qty_ir` < 1
                                OR
                                `magazines_qty_ir` IS NULL
                            )
                        """, as_dict=True)
    total = len(abos)
    loop = 1
    for abo in abos:
        print("Round 2: {0} von {1}".format(loop, total))
        a = frappe.get_doc("mp Abo", abo.name)
        for recipient in a.recipient:
            recipient.abo_type = a.type
            recipient.digital = 1
        a.save()
        loop += 1
    print("Done")

