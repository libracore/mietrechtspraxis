# -*- coding: utf-8 -*-
# Copyright (c) 2021, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import pandas as pd


# Header mapping (ERPNext <> MVD)
hm = {
    'first_name': 'vorname', # contact
    'last_name': 'nachname', # contact
    'salutation': 'anrede_string', # contact
    'email_id': 'e_mail', # contact
    'is_primary_phone': 'tel_p', # contact
    'is_primary_mobile_no': 'tel_m', # contact
    'phone': 'tel_g', # contact
    'customer_addition': 'zusatz_firma', # customer
    'company_name': 'firma', # contact, customer
    'sektion': 'sektion_id', # contact, address
    'address_title': 'adress_id', # address
    'address_line1': 'strasse', # address
    'address_line2': 'zusatz_adresse', # address
    'postfach': 'postfach_nummer', # address
    'nummer': 'nummer', # address
    'nummer_zu': 'nummer_zu', # address
    'plz': 'plz', # address
    'city': 'ort', # address
    'address_type': 'adresstyp_c', # identifikation ob Abo Inhaber oder Empfänger
    'mkategorie_id': 'mkategorie_id', # ID der mkategorie_d
    'datum_eintritt': 'datum_eintritt', # start datum
    'datum_austritt': 'datum_austritt', # enddatum
    'zeitung_anzahl': 'zeitung_anzahl', # anz. Zeitungen
    'mitglied_id': 'mitglied_id', # mp abo als import referenz
    'postfach': 'postfach', # checkbox ob Postfach (ja/nein = -1/0)
    'postfach_nummer': 'postfach_nummer', # address
    'preis': 'preis', # abo preis
    'webuser_id': 'webuser_id',
    'password': 'password'
}
    
@frappe.whitelist()
def read_csv(site_name, file_name, limit=False):
    # display all coloumns for error handling
    pd.set_option('display.max_rows', None, 'display.max_columns', None)
    
    # read csv
    df = pd.read_csv('/home/frappe/frappe-bench/sites/{site_name}/private/files/{file_name}'.format(site_name=site_name, file_name=file_name))
    
    # loop through rows
    count = 1
    max_loop = limit
    
    if not limit:
        index = df.index
        max_loop = len(index)
        
    for index, row in df.iterrows():
        if count <= max_loop:
            contact_error = False
            address_error = False
            
            # create contact
            contact_response = create_contact(row)
            if contact_response['success']:
                contact = contact_response['contact']
            else:
                # error handling contact creation
                frappe.log_error('{0}'.format(contact_response['data']), "Kontakt: {0}".format(contact_response['error']))
                contact_error = True
                
            # create address
            address_response = create_address(row)
            if address_response['success']:
                # opt. linking with contact
                if not contact_error:
                    contact = frappe.get_doc("Contact", contact)
                    contact.address = address_response['address']
                    contact.save(ignore_permissions=True)
                    frappe.db.commit()
            else:
                # error handling address creation
                frappe.log_error('{0}'.format(address_response['data']), "Adresse: {0}".format(address_response['error']))
                address_error = True
                
            # create customer
            if not contact_error:
                customer_response = create_customer(data=row, contact=contact_response['contact'])
            else:
                customer_response = create_customer(data=row)
            if customer_response['success']:
                # opt. linking contact with customer
                if not contact_error:
                    contact = frappe.get_doc("Contact", contact_response['contact'])
                    link = contact.append("links", {})
                    link.link_doctype = 'Customer'
                    link.link_name = customer_response['customer']
                    contact.save(ignore_permissions=True)
                    frappe.db.commit()
                # opt. linking address with customer
                if not address_error:
                    address = frappe.get_doc("Address", address_response['address'])
                    link = address.append("links", {})
                    link.link_doctype = 'Customer'
                    link.link_name = customer_response['customer']
                    address.save(ignore_permissions=True)
                    frappe.db.commit()
                # create new Abo or append to existing abo
                if not contact_error and not address_error:
                    if get_value(row, 'address_type') == 'MITGL':
                        # create new Abo (=Inhaber)
                        create_or_append_abo(data=row, new=True, customer=customer_response['customer'], address=address_response['address'], contact=contact_response['contact'])
                    elif get_value(row, 'address_type') == 'ZEITUN':
                        # append to existing abo (=Empfänger)
                        create_or_append_abo(data=row, new=False, customer=customer_response['customer'], address=address_response['address'], contact=contact_response['contact'])
                    else:
                        # error handling unbek. adresstyp_c
                        frappe.log_error('{0}'.format(row), "Unbekannter adresstyp_c: {0}".format(get_value(row, 'address_type')))
            else:
                # error handling customer creation
                frappe.log_error('{0}'.format(customer_response['data']), "Kunde: {0}".format(customer_response['error']))
            print("{count} of {max_loop} --> {percent}".format(count=count, max_loop=max_loop, percent=((100 / max_loop) * count)))
            count += 1
        else:
            break

def create_contact(data):
    # check mandatory fields
    first_name = get_value(data, 'first_name')
    last_name = get_value(data, 'last_name')
    company_name = get_value(data, 'company_name')
    
    if not first_name:
        if not last_name:
            if not company_name:
                return {
                    'success': False,
                    'data': data,
                    'error': 'Fehlende Daten'
                }
            else:
                first_name = company_name
        else:
            first_name = last_name
    
    try:
        # base data
        webuser_id = get_value(data, 'webuser_id')
        if len(webuser_id) < 8:
            webuser_id = webuser_id.zfill(8)
        new_contact = frappe.get_doc({
            'doctype': 'Contact',
            'first_name': first_name,
            'last_name': last_name,
            'salutation': get_value(data, 'salutation'),
            'sektion': get_sektion(get_value(data, 'sektion')),
            'company_name': company_name,
            'mp_password': get_value(data, 'password'),
            'mp_abo_old': webuser_id
        })
        
        # email
        email_id = get_value(data, 'email_id')
        if email_id:
            email_row = new_contact.append("email_ids", {})
            email_row.email_id = email_id
            email_row.is_primary = 1
            
        # private phone
        is_primary_phone = get_value(data, 'is_primary_phone')
        if is_primary_phone:
            is_primary_phone_row = new_contact.append("phone_nos", {})
            is_primary_phone_row.phone = is_primary_phone
            is_primary_phone_row.is_primary_phone = 1
            
        # mobile phone
        is_primary_mobile_no = get_value(data, 'is_primary_mobile_no')
        if is_primary_mobile_no:
            is_primary_mobile_no_row = new_contact.append("phone_nos", {})
            is_primary_mobile_no_row.phone = is_primary_mobile_no
            is_primary_mobile_no_row.is_primary_mobile_no = 1
            
        # other (company) phone
        phone = get_value(data, 'phone')
        if phone:
            phone_row = new_contact.append("phone_nos", {})
            phone_row.phone = phone
            
        new_contact.insert()
        frappe.db.commit()
        return {
            'success': True,
            'contact': new_contact.name
        }
        
    except Exception as err:
        return {
            'success': False,
            'data': data,
            'error': err
        }
        
def create_address(data):
    # get datas
    if len(get_value(data, 'address_line1')) > 0:
        address_line1 = strasse = (" ").join((str(get_value(data, 'address_line1')), str(get_value(data, 'nummer')), str(get_value(data, 'nummer_zu'))))
    else:
        address_line1 = strasse = False
    address_line2 = zusatz = get_value(data, 'address_line2')
    pincode = plz = get_value(data, 'plz')
    city = get_value(data, 'city')
    postfach_check = get_value(data, 'postfach')
    postfach = 0
    if postfach_check:
        if int(postfach_check) < 0:
            postfach = 1
    postfach_nummer = get_value(data, 'postfach_nummer')
    if not address_line1 and not postfach and postfach_nummer:
        postfach = 1
    
    # validierung
    if not address_line1 and not postfach and not postfach_nummer:
        return {
            'success': False,
            'data': data,
            'error': 'Weder Strasse noch Postfach hinterlegt'
        }
    if not plz:
        return {
            'success': False,
            'data': data,
            'error': 'Keine PLZ hinterlegt'
        }
    if not city:
        return {
            'success': False,
            'data': data,
            'error': 'Kein Ort hinterlegt'
        }
        
    if not address_line1:
        address_line1 = '-'
      
    # daten anlage
    try:
        new_address = frappe.get_doc({
            'doctype': 'Address',
            'address_title': get_value(data, 'address_title'),
            'address_line1': address_line1,
            'address_line2': address_line2,
            'strasse': strasse,
            'sektion': get_sektion(get_value(data, 'sektion')),
            'pincode': plz,
            'plz': plz,
            'postfach': postfach,
            'postfach_nummer': postfach_nummer,
            'city': city
        })
        new_address.insert()
        frappe.db.commit()
        return {
            'success': True,
            'address': new_address.name
        }
    except Exception as err:
        return {
            'success': False,
            'data': data,
            'error': err
        }
        
def create_customer(data=None, contact=None):
    customer_addition = get_value(data, 'customer_addition')
    if not contact:
        company = get_value(data, 'company_name')
        if not company:
            return {
                'success': False,
                'data': data,
                'error': 'Weder Kontaktdaten noch Firma hinterlegt'
            }
        else:
            customer_name = company
            customer_type = 'Company'
    else:
        contact = frappe.get_doc('Contact', contact)
        if not contact.company_name:
            customer_name = (" ").join((contact.first_name, contact.last_name))
            customer_type = 'Individual'
        else:
            customer_name = contact.company_name
            customer_type = 'Company'
        
    try:
        new_customer = frappe.get_doc({
            'doctype': 'Customer',
            'customer_name': customer_name,
            'customer_addition': customer_addition,
            'customer_type': customer_type
        })
        new_customer.insert()
        frappe.db.commit()
        return {
            'success': True,
            'customer': new_customer.name
        }
    except Exception as err:
        return {
            'success': False,
            'data': data,
            'error': err
        }
        
def create_or_append_abo(data, new, customer=False, address=False, contact=False):
    if new:
        # create new Abo
        abo_type = 'Jahres-Abo'
        abo_status = 'Inactive'
        preis = 0
        if get_value(data, 'preis'):
            preis = get_value(data, 'preis')
        if not preis > 0:
            abo_type = 'Gratis-Abo'
        start_datum_raw = get_value(data, 'datum_eintritt').split(" ")[0]
        if not start_datum_raw:
            start_datum_raw = '1900-01-01'
        end_datum_raw = get_value(data, 'datum_austritt').split(" ")[0]
        if not start_datum_raw:
            end_datum_raw = ''
            abo_status = 'Active'
        
        try:
            new_abo = frappe.get_doc({
                'doctype': 'mp Abo',
                'type': abo_type,
                'start_date': start_datum_raw.replace("/", "-"),
                'end_date': end_datum_raw,
                'status': abo_status,
                'invoice_recipient': customer,
                'customer': customer,
                'recipient_contact': contact,
                'recipient_address': address,
                'magazines_qty_ir': get_value(data, 'zeitung_anzahl'),
                'mitglied_id': get_value(data, 'mitglied_id')
            })
            new_abo.insert()
            frappe.db.commit()
            add_new_abo_nr_to_contact(contact, new_abo.name)
            return {
                'success': True,
                'customer': new_abo.name
            }
        except Exception as err:
            return {
                'success': False,
                'data': data,
                'error': err
            }
        
    else:
        # append to existing Abo
        mitglied_id = get_value(data, 'mitglied_id')
        existing_abo = frappe.db.sql("""SELECT `name` FROM `tabmp Abo` WHERE `mitglied_id` = '{mitglied_id}' LIMIT 1""".format(mitglied_id=mitglied_id), as_dict=True)
        if len(existing_abo) > 0:
            existing_abo = frappe.get_doc("mp Abo", existing_abo[0].name)
            row = existing_abo.append('recipient', {})
            row.magazines_recipient = customer
            row.recipient_contact = contact
            row.recipient_address = address
            row.magazines_qty_mr = get_value(data, 'zeitung_anzahl')
            existing_abo.save(ignore_permissions=True)
            frappe.db.commit()
            add_new_abo_nr_to_contact(contact, existing_abo.name)
        else:
            # error handling no existing Abo
            frappe.log_error('{0}'.format(data), "Kein 'Eltern'-Abo gefunden")
        
        
def add_new_abo_nr_to_contact(contact, abo):
    contact = frappe.get_doc("Contact", contact)
    contact.mp_username = abo
    contact.save(ignore_permissions=True)
    frappe.db.commit()
    
    
def get_sektion(id):
    if id == 25:
        return 'MP'
        
def get_value(row, value):
    value = row[hm[value]]
    if not pd.isnull(value):
        if isinstance(value, str):
            return value.strip()
        else:
            return value
    else:
        return ''
