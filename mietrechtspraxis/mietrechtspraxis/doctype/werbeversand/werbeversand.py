# -*- coding: utf-8 -*-
# Copyright (c) 2022, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils.background_jobs import enqueue
from frappe.utils.csvutils import to_csv as make_csv
from frappe.utils.data import now

class Werbeversand(Document):
    def before_submit(self):
        self.status = 'In Arbeit'
        args = {
            'werbeversand': self.name
        }
        enqueue("mietrechtspraxis.mietrechtspraxis.doctype.werbeversand.werbeversand.get_create_csv", queue='long', job_name='Werbeversand {0}'.format(self.name), timeout=6000, **args)

def get_create_csv(werbeversand):
    werbeversand_doc = frappe.get_doc("Werbeversand", werbeversand)
    werbeversand_doc.add_comment('Comment', text='Erstelle CSV...')
    frappe.db.commit()
    
    try:
        # preparing csv
        csv_data = get_csv_header()
        
        filters = ''
        
        if werbeversand_doc.mh_tags:
            first = True
            for mh_tag in werbeversand_doc.mh_tags.split("\n"):
                if first:
                    filters += """WHERE (`_user_tags` LIKE '%{0}%'""".format(mh_tag)
                    first = False
                else:
                    filters += """ AND `_user_tags` LIKE '%{0}%'""".format(mh_tag)
            filters += ')'
        
        if werbeversand_doc.no_tags:
            first = True
            for no_tag in werbeversand_doc.no_tags.split("\n"):
                if first:
                    if not werbeversand_doc.mh_tags:
                        filters += """WHERE (`_user_tags` NOT LIKE '%{0}%'""".format(no_tag)
                        first = False
                    else:
                        filters += """ AND (`_user_tags` NOT LIKE '%{0}%'""".format(no_tag)
                        first = False
                else:
                    filters += """ AND `_user_tags` NOT LIKE '%{0}%'""".format(no_tag)
            filters += ')'
                
        contacts = frappe.db.sql("""SELECT `name` FROM `tabContact` {filters}""".format(filters=filters), as_dict=True)
        
        for contact in contacts:
            c = frappe.get_doc("Contact", contact.name)
            csv_data = get_csv_data(csv_data, c)
        
        file_name = create_csv(csv_data, werbeversand)
        
        werbeversand_doc = frappe.get_doc("Werbeversand", werbeversand)
        werbeversand_doc.add_comment('Comment', text='CSV erstellt, siehe Anhang {file_name}'.format(file_name=file_name))
        werbeversand_doc.status = 'Abgeschlossen'
        werbeversand_doc.save()
        frappe.db.commit()
    except Exception as err:
        werbeversand_doc = frappe.get_doc("Werbeversand", werbeversand)
        werbeversand_doc.add_comment('Comment', text=str(err))
        werbeversand_doc.status = 'Fehlgeschlagen'
        werbeversand_doc.save()
        frappe.db.commit()

def get_csv_header():
    data = []
    header = [
        'customer_fullname',
        'customer_addition',
        'customer_type',
        'customer_group',
        'customer_korrespondenz',
        'customer_disabled',
        'contact_salutation',
        'contact_first_name',
        'contact_last_name',
        'contact_email',
        'contact_phone',
        'contact_mobile',
        'contact_eine_zusendung',
        'contact_keine_werbung',
        'contact_tags',
        'strasse',
        'zusatz',
        'plz',
        'ort',
        'land',
        'customer_id',
        'contact_id',
        'address_id'
    ]
    data.append(header)
    return data

def get_csv_data(csv_data, contact):
    data = []
    
    # add customer data
    customer = False
    if len(contact.links) > 0:
        for link in contact.links:
            if link.link_doctype == 'Customer':
                customer = frappe.get_doc("Customer", link.link_name)
    
    if not customer:
        data.append('---')
        data.append('---')
        data.append('---')
        data.append('---')
        data.append('---')
        data.append('---')
    else:
        if customer.customer_type == 'Company':
            if customer.customer_name != contact.first_name:
                data.append('{customer_fullname}'.format(customer_fullname=customer.customer_name or ''))
            else:
                data.append('')
        else:
            data.append('')
        data.append('{customer_addition}'.format(customer_addition=customer.customer_addition or ''))
        data.append('{customer_type}'.format(customer_type=customer.customer_type or ''))
        data.append('{customer_group}'.format(customer_group=customer.customer_group or ''))
        data.append('{customer_korrespondenz}'.format(customer_korrespondenz=customer.korrespondenz or ''))
        data.append('{customer_disabled}'.format(customer_disabled=1 if customer.disabled else 0))
    
    # add contact data
    data.append('{contact_salutation}'.format(contact_salutation=contact.salutation or ''))
    data.append('{contact_firstname}'.format(contact_firstname=contact.first_name or ''))
    data.append('{contact_last_name}'.format(contact_last_name=contact.last_name or ''))
    data.append('{contact_email}'.format(contact_email=contact.email_id or ''))
    data.append('{contact_phone}'.format(contact_phone=contact.phone or ''))
    data.append('{contact_mobile}'.format(contact_mobile=contact.mobile_no or ''))
    data.append('{contact_eine_zusendung}'.format(contact_eine_zusendung=1 if contact.nur_eine_zusendung else 0))
    data.append('{contact_keine_werbung}'.format(contact_keine_werbung=1 if contact.keine_werbung else 0))
    data.append('{contact_tags}'.format(contact_tags=contact._user_tags or ''))
    
    # add address data
    address = frappe.get_doc("Address", contact.address) if contact.address else False
    
    if not address:
        data.append('---')
        data.append('---')
        data.append('---')
        data.append('---')
        data.append('---')
    else:
        data.append('{strasse}'.format(strasse=address.strasse or ''))
        data.append('{zusatz}'.format(zusatz=address.zusatz or ''))
        data.append('{plz}'.format(plz=address.plz if address.plz else address.pincode or ''))
        data.append('{ort}'.format(ort=address.city or ''))
        data.append('{land}'.format(land=address.country or ''))
    
    if not customer:
        data.append('---')
    else:
        data.append('{0}'.format(customer.name))
    data.append('{0}'.format(contact.name))
    if not address:
        data.append('---')
    else:
        data.append('{0}'.format(address.name))
    # concat data and return
    csv_data.append(data)
    return csv_data

def create_csv(csv_data, werbeversand):
    csv_file = make_csv(csv_data)
    file_name = "{titel}_{datetime}.csv".format(titel=werbeversand, datetime=now().replace(" ", "_"))
    
    _file = frappe.get_doc({
        "doctype": "File",
        "file_name": file_name,
        "folder": "Home/Attachments",
        "is_private": 1,
        "content": csv_file,
        "attached_to_doctype": 'Werbeversand',
        "attached_to_name": werbeversand
    })
    
    _file.insert()
    
    return file_name
