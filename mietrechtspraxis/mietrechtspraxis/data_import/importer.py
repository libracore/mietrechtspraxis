# -*- coding: utf-8 -*-
# Copyright (c) 2021, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import pandas as pd
from frappe.desk.tags import add_tag


# ----------------------------------------------
# Import Abo Inhaber/Empfänger
# ----------------------------------------------

# Header mapping (ERPNext <> MVD)
hm = {
    'first_name': 'first_name', # contact
    'last_name': 'last_name', # contact
    'salutation': 'anrede_string', # contact
    'email_id': 'e_mail', # contact
    'is_primary_phone': 'tel_p', # contact
    'is_primary_mobile_no': 'tel_m', # contact
    'phone': 'tel_g', # contact
    'customer_addition': 'zusatz_firma', # customer
    'company_name': 'firma', # contact, customer
    'sektion': 'sektion_id', # contact, address
    'address_title': 'adress_id', # address,
    'adress_id': 'adress_identifier', # address
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
    'password': 'password',
    'backup_mail': 'email',
    'zeitung_anzahl_adresse': 'zeitung_anzahl_adresse',
    'leistung_id': 'leistung_id',
    'datum_kuend_per': 'datum_kuend_per',
    'id': 'id',
    'gender': 'gender',
    'street': 'street',
    'postcode': 'postcode',
    'location': 'location',
    'phone_number': 'phone_number',
    'email': 'email',
    'company': 'company',
    'data_1': 'data_1'
}
    

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
    
    # check and/or create customer_groups
    check_customer_group()
    
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
    first_name = str(get_value(data, 'first_name'))
    last_name = str(get_value(data, 'last_name'))
    company_name = str(get_value(data, 'company_name'))
    
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
        existing = check_if_update(str(get_value(data, 'adress_id')), "Contact")
        if not existing:
            # base data
            webuser_id = str(get_value(data, 'webuser_id'))
            if len(webuser_id) < 8:
                webuser_id = webuser_id.zfill(8)
            new_contact = frappe.get_doc({
                'doctype': 'Contact',
                'first_name': first_name,
                'last_name': last_name,
                'salutation': str(get_value(data, 'salutation')),
                'sektion': str(get_sektion(get_value(data, 'sektion'))),
                'company_name': company_name,
                'mp_password': str(get_value(data, 'password')),
                'mp_abo_old': webuser_id,
                'address_id': str(get_value(data, 'adress_id'))
            })
        else:
            webuser_id = str(get_value(data, 'webuser_id'))
            if len(webuser_id) < 8:
                webuser_id = webuser_id.zfill(8)
            new_contact = frappe.get_doc("Contact", existing)
            new_contact.first_name = first_name
            new_contact.last_name = last_name
            new_contact.salutation = str(get_value(data, 'salutation'))
            new_contact.sektion = str(get_sektion(get_value(data, 'sektion')))
            new_contact.company_name = company_name
            new_contact.mp_password = str(get_value(data, 'password'))
            new_contact.mp_abo_old = webuser_id
            new_contact.email_ids = []
            new_contact.phone_nos = []
            
        
        # email
        email_id = get_value(data, 'email_id')
        if email_id:
            email_row = new_contact.append("email_ids", {})
            email_row.email_id = email_id
            email_row.is_primary = 1
        else:
            email_id = get_value(data, 'backup_mail')
            if email_id:
                email_row = new_contact.append("email_ids", {})
                email_row.email_id = email_id
                email_row.is_primary = 1
            
        # private phone
        is_primary_phone = str(get_value(data, 'is_primary_phone'))
        if is_primary_phone:
            is_primary_phone_row = new_contact.append("phone_nos", {})
            is_primary_phone_row.phone = is_primary_phone
            is_primary_phone_row.is_primary_phone = 1
            
        # mobile phone
        is_primary_mobile_no = str(get_value(data, 'is_primary_mobile_no'))
        if is_primary_mobile_no:
            is_primary_mobile_no_row = new_contact.append("phone_nos", {})
            is_primary_mobile_no_row.phone = is_primary_mobile_no
            is_primary_mobile_no_row.is_primary_mobile_no = 1
            
        # other (company) phone
        phone = str(get_value(data, 'phone'))
        if phone:
            phone_row = new_contact.append("phone_nos", {})
            phone_row.phone = phone
            
        if not existing:
            new_contact.insert()
        else:
            new_contact.save(ignore_permissions=True)
        
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
    postfach_nummer = get_value(data, 'postfach_nummer')
    
    if int(postfach_check) == 0:
        if postfach_nummer:
            postfach = 1
            address_line1 = strasse = 'Postfach'
    if int(postfach_check) == -1:
        postfach = 1
        address_line1 = strasse = 'Postfach'
    
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
        strasse = '-'
      
    # daten anlage
    try:
        existing = check_if_update(str(get_value(data, 'adress_id')), "Address")
        if not existing:
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
                'city': city,
                'adress_id': str(get_value(data, 'adress_id'))
            })
            new_address.insert()
        else:
            new_address = frappe.get_doc("Address", existing)
            new_address.address_title = get_value(data, 'address_title')
            new_address.address_line1 = address_line1
            new_address.address_line2 = address_line2
            new_address.strasse = strasse
            new_address.sektion = get_sektion(get_value(data, 'sektion'))
            new_address.pincode = plz
            new_address.plz = plz
            new_address.postfach = postfach
            new_address.postfach_nummer = postfach_nummer
            new_address.city = city
            new_address.save(ignore_permissions=True)
            
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
    
    customer_group = get_customer_group(get_value(data, 'leistung_id'))
    
    try:
        existing = check_if_update(str(get_value(data, 'adress_id')), "Customer")
        if not existing:
            new_customer = frappe.get_doc({
                'doctype': 'Customer',
                'customer_name': customer_name,
                'customer_addition': customer_addition,
                'customer_type': customer_type,
                'adress_id': str(get_value(data, 'adress_id')),
                'customer_group': customer_group
            })
            new_customer.insert()
        else:
            new_customer = frappe.get_doc("Customer", existing)
            new_customer.customer_name = customer_name
            new_customer.customer_addition = customer_addition
            new_customer.customer_type = customer_type
            new_customer.customer_group = customer_group
            new_customer.save(ignore_permissions=True)
            
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
        if not end_datum_raw:
            end_datum_raw = get_value(data, 'datum_kuend_per').split(" ")[0]
            if not end_datum_raw:
                end_datum_raw = ''
                abo_status = 'Active'
        
        try:
            # update existing Abo
            mitglied_id = get_value(data, 'mitglied_id')
            existing_abo = frappe.db.sql("""SELECT `name` FROM `tabmp Abo` WHERE `mitglied_id` = '{mitglied_id}' LIMIT 1""".format(mitglied_id=mitglied_id), as_dict=True)
            
            if len(existing_abo) > 0:
                new_abo = frappe.get_doc("mp Abo", existing_abo[0].name)
                new_abo.type = abo_type
                new_abo.start_date = start_datum_raw.replace("/", "-")
                new_abo.end_date = end_datum_raw
                new_abo.status = abo_status
                new_abo.invoice_recipient = customer
                new_abo.customer = customer
                new_abo.recipient_contact = contact
                new_abo.recipient_address = address
                new_abo.magazines_qty_ir = get_value(data, 'zeitung_anzahl')
                new_abo.mitglied_id = get_value(data, 'mitglied_id')
                new_abo.save(ignore_permissions=True)
                
            else:
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
                    'magazines_qty_ir': get_value(data, 'zeitung_anzahl') or 0,
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
            found_entry = False
            for recipient in existing_abo.recipient:
                if recipient.magazines_recipient == customer:
                    found_entry = True
                    recipient.magazines_qty_mr = get_value(data, 'zeitung_anzahl_adresse') or 0
            
            if not found_entry:
                row = existing_abo.append('recipient', {})
                row.magazines_recipient = customer
                row.recipient_contact = contact
                row.recipient_address = address
                row.magazines_qty_mr = get_value(data, 'zeitung_anzahl_adresse')
            
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

def get_customer_group(id):
    if id == 198:
        return 'Abonnement'
    if id == 199:
        return 'Abonnement gratis'
    if id == 200:
        return 'Buchhandel'
    if id == 201:
        return 'Buchhandel Ausland'
    if id == 203:
        return 'Abonnement MV-Sektion'
    # Fallback
    return 'Unspezifisch'
        
def get_value(row, value):
    value = row[hm[value]]
    if not pd.isnull(value):
        try:
            if isinstance(value, str):
                return value.strip()
            else:
                return value
        except:
            return value
    else:
        return ''

def check_if_update(id, dt):
    data = frappe.db.sql("""SELECT `name` FROM `tab{dt}` WHERE `adress_id` = '{id}'""".format(dt=dt, id=id), as_dict=True)
    if len(data) > 0:
        return data[0].name
    else:
        return False

def clear_data():
    frappe.db.sql("""SET SQL_SAFE_UPDATES = 0""", as_list=True)
    frappe.db.sql("""DELETE FROM `tabContact Phone`""", as_list=True)
    frappe.db.sql("""DELETE FROM `tabContact Email`""", as_list=True)
    frappe.db.sql("""DELETE FROM `tabmp Abo`""", as_list=True)
    frappe.db.sql("""DELETE FROM `tabContact`""", as_list=True)
    frappe.db.sql("""DELETE FROM `tabAddress`""", as_list=True)
    frappe.db.sql("""DELETE FROM `tabDynamic Link`""", as_list=True)
    frappe.db.sql("""DELETE FROM `tabCustomer`""", as_list=True)
    frappe.db.sql("""DELETE FROM `tabmp Abo Invoice`""", as_list=True)
    frappe.db.sql("""DELETE FROM `tabmp Abo Recipient`""", as_list=True)
    frappe.db.sql("""SET SQL_SAFE_UPDATES = 1""", as_list=True)
    print("Done")

def check_customer_group(customer_group=['Abonnement', 'Abonnement gratis', 'Buchhandel', 'Buchhandel Ausland', 'Abonnement MV-Sektion', 'Unspezifisch']):
    for group in customer_group:
        if not frappe.db.exists('Customer Group', group):
            new_group = frappe.get_doc({
                'doctype': 'Customer Group',
                'customer_group_name': group,
                'parent_customer_group': 'All Customer Groups'
            })
            new_group.insert()
            frappe.db.commit()
    return

# ----------------------------------------------
# Import Werbedaten
# ----------------------------------------------
def import_werbedaten(site_name, file_name, limit=False):
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
    
    # check and/or create customer_groups
    check_customer_group(customer_group=['Werbedaten'])
    
    for index, row in df.iterrows():
        if count <= max_loop:
            nicht_importieren = str(get_werbe_value(row, 'Nicht_Importieren')).replace(".0", "")
            if nicht_importieren != '1' or nicht_importieren != '-1':
                # --------------------------------------------------------------------------------
                # get data
                vid = str(get_werbe_value(row, 'vid')).replace(".0", "")
                vid_firma = str(get_werbe_value(row, 'vid_firma')).replace(".0", "")
                idabo = str(get_werbe_value(row, 'idAbo'))
                # /get data
                # --------------------------------------------------------------------------------
                
                # --------------------------------------------------------------------------------
                # update data based on idAbo
                if idabo:
                    # bestehende abo Kunde
                    if len(idabo.split(":")) > 1:
                        # fehler mehere Abo verknüpfungen
                        frappe.log_error('{0}'.format(row), "Mehrere idAbo verknüpfungen: {0}".format(idabo))
                    else:
                        # suche kunde anhand idabo
                        customer = find_customer(idabo=idabo)
                        if not customer:
                            frappe.log_error('{0}'.format(row), "Kunde mit idAbo nicht gefunden: {0}".format(idabo))
                        else:
                            update_status = update_werbe_customer(row, customer)
                            if not update_status['updated']:
                                frappe.log_error('{0}'.format(row), "Update Kunde ({0}) mit idAbo fehlgeschlagen: {1}".format(customer, update_status['error']))
                            else:
                                update_status = update_werbe_contact(row, customer)
                                if not update_status['updated']:
                                    frappe.log_error('{0}'.format(row), "Update Kontakt von Kunde ({0}) mit idAbo fehlgeschlagen: {1}".format(customer, update_status['error']))
                                else:
                                    if update_status['address']:
                                        update_status = update_werbe_address(row, update_status['address'])
                                        if not update_status['updated']:
                                            frappe.log_error('{0}'.format(row), "Update Adresse von Kunde ({0}) mit idAbo fehlgeschlagen: {1}".format(customer, update_status['error']))
                # update data based on vid
                # or
                # import new data
                else:
                    # suche kunde mit vid
                    customer = find_customer(vid=vid)
                    if not customer:
                        # anlage kunde und/oder kontakt und adresse
                        if vid == vid_firma:
                            customer = create_werbe_customer(row)
                        else:
                            if vid_firma:
                                # suche kunde anhand vid_firma
                                customer = find_customer(vid=vid_firma)
                            else:
                                customer = create_werbe_customer(row)
                        if not customer and vid == vid_firma:
                            frappe.log_error('{0}'.format(row), "Kunden Anlage fehlgeschlagen: vid = {0}".format(vid))
                        elif not customer and vid != vid_firma:
                            frappe.log_error('{0}'.format(row), "Kunden Suche fehlgeschlagen: vid_firma = {0}".format(vid_firma))
                        else:
                            address = create_werbe_address(row, customer)
                            if not address:
                                frappe.log_error('{0}'.format(row), "Adressen Anlage fehlgeschlagen: Kunde {0}".format(customer))
                            else:
                                contact = create_werbe_contact(row, customer, address)
                                if not contact:
                                    frappe.log_error('{0}'.format(row), "Kontakt Anlage fehlgeschlagen: Kunde {0}".format(customer))
                    else:
                        # update kontakt und adresse & ggf. kunde
                        if vid == vid_firma:
                            # update kunde
                            update_status = update_werbe_customer(row, customer)
                            if not update_status['updated']:
                                frappe.log_error('{0}'.format(row), "Update Kunde ({0}) mit idAbo fehlgeschlagen: {1}".format(customer, update_status['error']))
                            else:
                                update_status = update_werbe_contact(row, customer)
                                if not update_status['updated']:
                                    frappe.log_error('{0}'.format(row), "Update Kontakt von Kunde ({0}) mit idAbo fehlgeschlagen: {1}".format(customer, update_status['error']))
                                else:
                                    if update_status['address']:
                                        update_status = update_werbe_address(row, update_status['address'])
                                        if not update_status['updated']:
                                            frappe.log_error('{0}'.format(row), "Update Adresse von Kunde ({0}) mit idAbo fehlgeschlagen: {1}".format(customer, update_status['error']))
            print("{count} of {max_loop} --> {percent}".format(count=count, max_loop=max_loop, percent=((100 / max_loop) * count)))
            count += 1
        else:
            break

def get_werbe_value(row, value):
    value = row[value]
    if not pd.isnull(value):
        try:
            if isinstance(value, str):
                value = value.strip()
                if value != 'NULL':
                    return value
                else:
                    return ''
            else:
                return value
        except:
            return value
    else:
        return ''
                
def find_customer(idabo=False, vid=False):
    if not idabo and not vid:
        return False
    
    if idabo:
        customer = frappe.db.sql("""SELECT `name` FROM `tabCustomer` WHERE `adress_id` = '{idabo}'""".format(idabo=idabo), as_dict=True)
        if len(customer) > 0:
            if len(customer) > 1:
                return False
            else:
                return customer[0].name
        else:
            return False
    if vid:
        customer = frappe.db.sql("""SELECT `name` FROM `tabCustomer` WHERE `vid` = '{vid}'""".format(vid=vid), as_dict=True)
        if len(customer) > 0:
            if len(customer) > 1:
                return False
            else:
                return customer[0].name
        else:
            return False


def update_werbe_customer(row, customer):
    try:
        # get data
        vid = str(get_werbe_value(row, 'vid')).replace(".0", "")
        quelle = str(get_werbe_value(row, 'Quelle'))
        nur_eine_zusendung = str(get_werbe_value(row, 'Firma wünscht nur eine Zusendung')).replace(".0", "")
        if nur_eine_zusendung == '1' or nur_eine_zusendung == '-1':
            nur_eine_zusendung = 1
        else:
            nur_eine_zusendung = 0
        
        customer = frappe.get_doc("Customer", customer)
        customer.nur_eine_zusendung = nur_eine_zusendung
        customer.import_quelle = quelle
        customer.vid = vid
        customer.save()
        frappe.db.commit()
        
        # tags
        tags = str(get_werbe_value(row, 'dtTags'))
        if tags:
            for tag in tags.split(":"):
                add_tag(tag, 'Customer', customer.name)
        
        return {
            'updated': True
        }
    except Exception as err:
        return {
            'updated': False,
            'error': err
        }

def update_werbe_contact(row, customer):
    try:
        contact = frappe.db.sql("""SELECT `parent` FROM `tabDynamic Link` WHERE `link_name` = '{related_customer}' AND `parenttype` = 'Contact'""".format(related_customer=customer), as_dict=True)
        if len(contact) > 0:
            if len(contact) > 1:
                # suche zusätzlich nach vid
                contact = frappe.db.sql("""SELECT `name` AS `parent` FROM `tabContact` WHERE `vid` = '{vid}'""".format(vid=str(get_werbe_value(row, 'vid')).replace(".0", "")), as_dict=True)
                if len(contact) > 1:
                    return {
                        'updated': False,
                        'error': 'Mehrere Kontakte gefunden'
                    }
                elif len(contact) < 1:
                    return {
                        'updated': False,
                        'error': 'Kein Kontakt (mit vid) und mehrere (mit kunde) gefunden'
                    }
            # treffer verarbeitung
            contact = frappe.get_doc("Contact", contact[0].parent)
            # get data
            nur_eine_zusendung = str(get_werbe_value(row, 'Firma wünscht nur eine Zusendung')).replace(".0", "")
            if nur_eine_zusendung == '1' or nur_eine_zusendung == '-1':
                nur_eine_zusendung = 1
            else:
                nur_eine_zusendung = 0
            keine_werbung = str(get_werbe_value(row, 'dtWünschtKeineWerbung')).replace(".0", "")
            if keine_werbung == '1' or keine_werbung == '-1':
                keine_werbung = 1
            else:
                keine_werbung = 0
            summe_bezahlt = get_werbe_value(row, 'summe_bezahlt')
            vid = str(get_werbe_value(row, 'vid')).replace(".0", "")
            vid_firma = str(get_werbe_value(row, 'vid_firma')).replace(".0", "")
            idabo = get_werbe_value(row, 'idAbo')
            idedoobox = get_werbe_value(row, 'idEdoobox')
            idschlichtungsbehoerde = get_werbe_value(row, 'idSchlichtungsbehoerde')
            idfaktura = get_werbe_value(row, 'idFaktura')
            
            contact.nur_eine_zusendung = nur_eine_zusendung
            contact.keine_werbung = keine_werbung
            contact.werbesperre = keine_werbung
            contact.summe_bezahlt = summe_bezahlt
            contact.vid = vid
            contact.vid_firma = vid_firma
            contact.idabo = idabo
            contact.idedoobox = idedoobox
            contact.idschlichtungsbehoerde = idschlichtungsbehoerde
            contact.idfaktura = idfaktura
            contact.save()
            frappe.db.commit()
            
            # tags
            tags = str(get_werbe_value(row, 'dtTags'))
            if tags:
                for tag in tags.split(":"):
                    add_tag(tag, 'Contact', contact.name)
            
            return {
                'updated': True,
                'address': contact.address
            }
        else:
            return {
                'updated': False,
                'error': 'Kein Kontakt gefunden'
            }
    except Exception as err:
        return {
            'updated': False,
            'error': err
        }

def update_werbe_address(row, address):
    try:
        address = frappe.get_doc("Address", address)
        vid = str(get_werbe_value(row, 'vid')).replace(".0", "")
        vid_firma = str(get_werbe_value(row, 'vid_firma')).replace(".0", "")
        idschlichtungsbehoerde = get_werbe_value(row, 'idSchlichtungsbehoerde')
        address.vid = vid
        address.vid_firma = vid_firma
        address.idschlichtungsbehoerde = idschlichtungsbehoerde
        address.save()
        frappe.db.commit()
                
        # tags
        tags = str(get_werbe_value(row, 'dtTags'))
        if tags:
            for tag in tags.split(":"):
                add_tag(tag, 'Address', address.name)
        
        return {
            'updated': True
        }
    except Exception as err:
        return {
            'updated': False,
            'error': err
        }


def create_werbe_customer(data):
    customer_group = 'Werbedaten'
    import_quelle = str(get_werbe_value(data, 'Quelle'))
    vid = str(get_werbe_value(data, 'vid')).replace(".0", "")
    
    nur_eine_zusendung = str(get_werbe_value(data, 'Firma wünscht nur eine Zusendung'))
    if nur_eine_zusendung == '1':
        nur_eine_zusendung = 1
    else:
        nur_eine_zusendung = 0
    
    company_name = get_werbe_value(data, 'Firma')
    if company_name:
        customer_type = 'Company'
        customer_name = company_name
    else:
        customer_type = 'Individual'
        customer_name = (" ").join((get_werbe_value(data, 'Vorname'), get_werbe_value(data, 'Name')))
    
    try:
        new_customer = frappe.get_doc({
            'doctype': 'Customer',
            'customer_name': customer_name,
            'customer_addition': '',
            'customer_type': customer_type,
            'vid': vid,
            'customer_group': customer_group,
            'import_quelle': import_quelle,
            'nur_eine_zusendung': nur_eine_zusendung
        })
        new_customer.insert()
        
        # tags
        tags = str(get_werbe_value(data, 'dtTags'))
        if tags:
            for tag in tags.split(":"):
                add_tag(tag, 'Customer', new_customer.name)
            
        frappe.db.commit()
        return new_customer.name
    except Exception as err:
        return False

def create_werbe_address(data, customer):
    # get datas
    address_line1 = strasse = str(get_werbe_value(data, 'Strasse'))
    address_line2 = zusatz = get_werbe_value(data, 'Adresszusatz')
    pincode = plz = get_werbe_value(data, 'PLZ')
    city = get_werbe_value(data, 'Ort')
    vid = str(get_werbe_value(data, 'vid')).replace(".0", "")
    vid_firma = str(get_werbe_value(data, 'vid_firma')).replace(".0", "")
    idschlichtungsbehoerde = get_werbe_value(data, 'idSchlichtungsbehoerde')
    
    postfach = str(get_werbe_value(data, 'postfach_v')).replace(".0", "")
    if postfach == '1' or postfach == '-1':
        postfach = 1
    else:
        postfach = 0
    postfach_nummer = str(get_werbe_value(data, 'postfach_nummer_v')).replace(".0", "")
    
    if not address_line2:
        edoobox_data = get_werbe_value(data, 'edoobox_data')
        if edoobox_data:
            address_line2 = zusatz = edoobox_data
    
    # validierung
    if not address_line1:
        # NUR FÜR TESTZWECKE!
        address_line1 = strasse = 'KEINE STRASSE: TESTIMPORT'
        # ~ return {
            # ~ 'success': False,
            # ~ 'data': data,
            # ~ 'error': 'Keine Strasse hinterlegt'
        # ~ }
    if not plz:
        # NUR FÜR TESTZWECKE!
        plz = 'KEINE PLZ: TESTIMPORT'
        # ~ return {
            # ~ 'success': False,
            # ~ 'data': data,
            # ~ 'error': 'Keine PLZ hinterlegt'
        # ~ }
    if not city:
        # NUR FÜR TESTZWECKE!
        city = 'KEIN ORT: TESTIMPORT'
        # ~ return {
            # ~ 'success': False,
            # ~ 'data': data,
            # ~ 'error': 'Kein Ort hinterlegt'
        # ~ }
        
    # daten anlage
    try:
        new_address = frappe.get_doc({
            'doctype': 'Address',
            'address_title': vid,
            'address_line1': address_line1,
            'address_line2': address_line2,
            'strasse': strasse,
            'sektion': 'MP',
            'pincode': plz,
            'plz': plz,
            'postfach': postfach,
            'postfach_nummer': postfach_nummer,
            'city': city,
            'vid': vid,
            'vid_firma': vid_firma,
            'country': 'Schweiz',
            'idschlichtungsbehoerde': idschlichtungsbehoerde
        })
        new_address.insert()
        
        link = new_address.append("links", {})
        link.link_doctype = 'Customer'
        link.link_name = customer
        new_address.save(ignore_permissions=True)
        
        # tags
        tags = str(get_werbe_value(data, 'dtTags'))
        if tags:
            for tag in tags.split(":"):
                add_tag(tag, 'Address', new_address.name)
            
        frappe.db.commit()
        return new_address.name
    except Exception as err:
        return False

def create_werbe_contact(data, customer, address):
    # check mandatory fields
    first_name = str(get_werbe_value(data, 'Vorname'))
    last_name = str(get_werbe_value(data, 'Name'))
    company_name = str(get_werbe_value(data, 'Firma'))
    vid = str(get_werbe_value(data, 'vid')).replace(".0", "")
    designation = str(get_werbe_value(data, 'Titel'))
    summe_bezahlt = str(get_werbe_value(data, 'summe_bezahlt'))
    vid_firma = str(get_werbe_value(data, 'vid_firma')).replace(".0", "")
    idabo = str(get_werbe_value(data, 'idAbo'))
    idedoobox = str(get_werbe_value(data, 'idEdoobox'))
    idschlichtungsbehoerde = get_werbe_value(data, 'idSchlichtungsbehoerde')
    idfaktura = str(get_werbe_value(data, 'idFaktura'))
    salutation = str(get_werbe_value(data, 'Anrede'))
    
    keine_werbung = str(get_werbe_value(data, 'dtWünschtKeineWerbung')).replace(".0", "")
    if keine_werbung == '1' or keine_werbung == '-1':
        keine_werbung = 1
    else:
        keine_werbung = 0
        
    nur_eine_zusendung = str(get_werbe_value(data, 'Firma wünscht nur eine Zusendung')).replace(".0", "")
    if nur_eine_zusendung == '1' or nur_eine_zusendung == '-1':
        nur_eine_zusendung = 1
    else:
        nur_eine_zusendung = 0
    
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
        new_contact = frappe.get_doc({
            'doctype': 'Contact',
            'first_name': first_name,
            'last_name': last_name,
            'salutation': salutation,
            'sektion': 'MP',
            'company_name': company_name,
            'mp_password': '',
            'mp_abo_old': '',
            'adress_id': '',
            'vid': vid,
            'designation': designation,
            'nur_eine_zusendung': nur_eine_zusendung,
            'summe_bezahlt': summe_bezahlt,
            'vid_firma': vid_firma,
            'keine_werbung': keine_werbung,
            'idabo': idabo,
            'idedoobox': idedoobox,
            'idschlichtungsbehoerde': idschlichtungsbehoerde,
            'idfaktura': idfaktura,
            'address': address
        })
        new_contact.insert()
        
        # email
        email_id = get_werbe_value(data, 'eMail')
        if email_id:
            email_row = new_contact.append("email_ids", {})
            email_row.email_id = email_id
            email_row.is_primary = 1
            
        # private phone
        is_primary_phone = str(get_werbe_value(data, 'Telefonnummer'))
        if is_primary_phone:
            is_primary_phone_row = new_contact.append("phone_nos", {})
            is_primary_phone_row.phone = is_primary_phone
            is_primary_phone_row.is_primary_phone = 1
            
        link = new_contact.append("links", {})
        link.link_doctype = 'Customer'
        link.link_name = customer
        new_contact.save(ignore_permissions=True)
        
        # tags
        tags = str(get_werbe_value(data, 'dtTags'))
        if tags:
            for tag in tags.split(":"):
                add_tag(tag, 'Contact', new_contact.name)
            
        frappe.db.commit()
        return new_contact.name
        
    except Exception as err:
        print(err)
        return False

# ----------------------------------------------
# Import Schlichtungsbehörden
# ----------------------------------------------
def import_schlichtungsbehoerden(site_name, file_name, limit=False):
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
            idschlichtungsbehoerde = get_werbe_value(row, 'id')
            kontakt = frappe.db.sql("""SELECT `name` FROM `tabContact` WHERE `idschlichtungsbehoerde` = '{idschlichtungsbehoerde}'""".format(idschlichtungsbehoerde=idschlichtungsbehoerde), as_dict=True)
            if len(kontakt) > 0:
                if len(kontakt) > 1:
                    frappe.log_error('{0}'.format(row), "Mehrere Schlichtungsbehörden zu ID {0} gefunden".format(idschlichtungsbehoerde))
                else:
                    try:
                        contact = frappe.get_doc("Contact", kontakt[0].name)
                        contact.first_name = str(get_werbe_value(row, 'Anschrift_1'))
                        contact.last_name = str(get_werbe_value(row, 'Anschrift_2'))
                        contact.designation = str(get_werbe_value(row, 'Behoerdenname'))
                        # email
                        email_id = str(get_werbe_value(row, 'Email'))
                        if email_id:
                            contact.email_ids = []
                            email_row = contact.append("email_ids", {})
                            email_row.email_id = email_id
                            email_row.is_primary = 1
                            
                        # private phone
                        is_primary_phone = str(get_werbe_value(row, 'Telefon'))
                        if is_primary_phone:
                            contact.phone_nos = []
                            is_primary_phone_row = contact.append("phone_nos", {})
                            is_primary_phone_row.phone = is_primary_phone
                            is_primary_phone_row.is_primary_phone = 1
                        # fax
                        fax = str(get_werbe_value(row, 'Telefax'))
                        if fax:
                            if not is_primary_phone:
                                contact.phone_nos = []
                            is_primary_phone_row = contact.append("phone_nos", {})
                            is_primary_phone_row.phone = fax
                            
                        contact.save()
                        
                        
                        if contact.address:
                            address = frappe.get_doc("Address", contact.address)
                            if str(get_werbe_value(row, 'Strasse')):
                                address.strasse = str(get_werbe_value(row, 'Strasse'))
                                address.address_line1 = str(get_werbe_value(row, 'Strasse'))
                            else:
                                address.strasse = 'KEINE STRASSE'
                                address.address_line1 = 'KEINE STRASSE'
                            if str(get_werbe_value(row, 'Adresszusatz')):
                                address.zusatz = str(get_werbe_value(row, 'Adresszusatz'))
                                address.address_line2 = str(get_werbe_value(row, 'Adresszusatz'))
                            else:
                                address.zusatz = ''
                                address.address_line2 = ''
                            if str(get_werbe_value(row, 'Postfach')):
                                address.postfach = 1
                                address.postfach_nummer = str(get_werbe_value(row, 'Postfach'))
                            else:
                                address.postfach = 0
                                address.postfach_nummer = ''
                            address.plz = str(get_werbe_value(row, 'Ort')).split(" ")[0]
                            address.pincode = str(get_werbe_value(row, 'Ort')).split(" ")[0]
                            address.city = str(get_werbe_value(row, 'Ort')).replace(str(get_werbe_value(row, 'Ort')).split(" ")[0] + " ", "")
                            address.save()
                        else:
                            frappe.log_error('{0}'.format(row), "Keine Adresse zur Schlichtungsbehörden mit ID {0} gefunden".format(idschlichtungsbehoerde))
                            address = False
                        
                        customer = contact.links[0].link_name
                        try:
                            titel = str(get_werbe_value(row, 'Anschrift_1'))
                            if str(get_werbe_value(row, 'Behoerdenname')):
                                titel += ' ' + str(get_werbe_value(row, 'Behoerdenname'))
                            elif str(get_werbe_value(row, 'Anschrift_2')):
                                titel += ' ' + str(get_werbe_value(row, 'Anschrift_2'))
                            
                            bgsvit = str(get_werbe_value(row, 'wertv_BGSVIT'))
                            if not bgsvit:
                                bgsvit = 'keine feste Regelung'
                            elif bgsvit == 'beide':
                                bgsvit = 'beide Varianten'
                            elif bgsvit == 'BG':
                                bgsvit = 'gem. Bundesgericht'
                            elif bgsvit == 'SVIT':
                                bgsvit = 'gem. SVIT-Kommentar'
                            svit_kommentar = str(get_werbe_value(row, 'wertv_bemerk'))
                            
                            new_sb = frappe.get_doc({
                                'doctype': 'Arbitration Authority',
                                'id': idschlichtungsbehoerde,
                                'kanton': str(get_werbe_value(row, 'Kanton')),
                                'titel': titel,
                                'kuendigungstermine': str(get_werbe_value(row, 'Kuendigungstermine')),
                                'pauschalen': str(get_werbe_value(row, 'Pauschalen')),
                                'sb_sitz': str(get_werbe_value(row, 'SB-Sitz')),
                                'elektronische_eingaben': str(get_werbe_value(row, 'Eingaben')),
                                'rechtsberatung': str(get_werbe_value(row, 'Rechtsberatung')),
                                'bemerkungen': str(get_werbe_value(row, 'Bemerkungen')),
                                'homepage': str(get_werbe_value(row, 'Homepage')),
                                'customer': customer,
                                'adresse': address.name if address else '',
                                'kontakt': contact.name,
                                'bgsvit': bgsvit,
                                'svit_kommentar': svit_kommentar or ''
                            })
                            new_sb.insert()
                            for gemeinde in str(get_werbe_value(row, 'Gemeinden')).split(", "):
                                link = new_sb.append("gemeinden", {})
                                link.municipality = gemeinde
                            new_sb.save()
                                
                            frappe.db.commit()
                        except Exception as err:
                            frappe.log_error('{0}'.format(row), "Anlage Schlichtungsbehörden mit ID {0} fehlgeschlagen: {1}".format(idschlichtungsbehoerde, err))
                    except Exception as err:
                            frappe.log_error('{0}'.format(row), "Master Fail: {0}".format(err))
            else:
                frappe.log_error('{0}'.format(row), "Schlichtungsbehörde {0} nicht gefunden".format(idschlichtungsbehoerde))
            print("{count} of {max_loop} --> {percent}".format(count=count, max_loop=max_loop, percent=((100 / max_loop) * count)))
            count += 1
        else:
            break

def customer_fullname_to_contact():
    contacts = frappe.db.sql("""SELECT
                                    `parent`,
                                    `link_name`
                                FROM `tabDynamic Link`
                                WHERE `parenttype` = 'Contact'
                                AND `link_doctype` = 'Customer'""", as_dict=True)
    total = len(contacts)
    loop = 1
    errors = ''
    for contact in contacts:
        try:
            customer_fullname = frappe.get_doc("Customer", contact.link_name).customer_name
            update = frappe.db.sql("""UPDATE `tabContact` SET `customer_fullname` = '{customer_fullname}' WHERE `name` = '{parent}'""".format(customer_fullname=customer_fullname, parent=contact.parent), as_list=True)
            print("{0} of {1}".format(loop, total))
            loop += 1
        except Exception as err:
            errors += '{0}, '.format(contact.parent)
    
    print("Fehlgeschlagen:")
    print(errors)
    return

def add_abo_tags():
    abos = frappe.db.sql("""SELECT `name` FROM `tabmp Abo` WHERE `status` = 'Active'""", as_dict=True)
    total = len(abos)
    loop = 1
    for abo in abos:
        print("{0} of {1}".format(loop, total))
        a = frappe.get_doc("mp Abo", abo.name)
        add_tag('Abo-Inhaber', 'Contact', a.recipient_contact)
        for k in a.recipient:
            add_tag('Abo-Empfänger', 'Contact', k.recipient_contact)
        loop += 1

# ----------------------------------------------
# Import EduBox Daten
# ----------------------------------------------
def import_edubox_daten(site_name, file_name):
    # display all coloumns for error handling
    pd.set_option('display.max_rows', None, 'display.max_columns', None)
    
    # read csv
    df = pd.read_csv('/home/frappe/frappe-bench/sites/{site_name}/private/files/{file_name}'.format(site_name=site_name, file_name=file_name))
    
    # loop through rows
    count = 1
    index = df.index
    max_loop = len(index)
    
    vorgaenger_name = ''
    vorgaenger_kunde = ''
    
    for index, row in df.iterrows():
        try:
            if str(get_werbe_value(row, 'company')) and str(get_werbe_value(row, 'company')) == vorgaenger_name:
                address = create_edubox_address(vorgaenger_kunde, row)
                create_edubox_kontakt(vorgaenger_kunde, address, row)
            else:
                vorgaenger_name = str(get_werbe_value(row, 'company'))
                vorgaenger_kunde = create_edubox_kunde(row)
                address = create_edubox_address(vorgaenger_kunde, row)
                create_edubox_kontakt(vorgaenger_kunde, address, row)
            print("{0} of {1}".format(count, max_loop))
            count += 1
        except Exception as err:
            frappe.log_error('{0}\n\n{1}'.format(str(err), row), "Import EduBox Daten")

def create_edubox_kunde(row):
    if not str(get_werbe_value(row, 'company')):
        customer_type = 'Individual'
        customer_name = str(get_werbe_value(row, 'first_name')) + str(get_werbe_value(row, 'last_name'))
        customer_addition = ''
    else:
        customer_type = 'Company'
        customer_name = str(get_werbe_value(row, 'company'))
        customer_addition = str(get_werbe_value(row, 'data_1'))
    import_quelle = "edoobox_20220929.csv"
    
    new_customer = frappe.get_doc({
        'doctype': 'Customer',
        'customer_name': customer_name,
        'customer_addition': customer_addition,
        'customer_type': customer_type,
        'import_quelle': import_quelle
    })
    new_customer.insert()
    
    return new_customer.name

def create_edubox_address(kunde, row):
    strasse= address_line1 = str(get_werbe_value(row, 'street'))
    address_line2 = ''
    zusatz = ''
    plz = str(int(get_werbe_value(row, 'postcode')))
    city = str(get_werbe_value(row, 'location'))
    country = 'Schweiz'
    
    new_address = frappe.get_doc({
        'doctype': 'Address',
        'address_title': kunde,
        'address_line1': address_line1,
        'address_line2': address_line2,
        'zusatz': zusatz,
        'strasse': strasse,
        'pincode': plz,
        'plz': plz,
        'city': city,
        'country': country,
        'links': [{
            'link_doctype': 'Customer',
            'link_name': kunde
        }]
    })
    new_address.insert()
    
    return new_address.name

def create_edubox_kontakt(kunde, adresse, row):
    first_name = str(get_werbe_value(row, 'first_name'))
    last_name = str(get_werbe_value(row, 'last_name'))
    salutation = str(get_werbe_value(row, 'gender'))
    if str(get_werbe_value(row, 'email')):
        email_ids = [{
            'email_id': str(get_werbe_value(row, 'email')),
            'is_primary': 1
        }]
    else:
        email_ids = []
    if str(get_werbe_value(row, 'phone_number')):
        phone_nos = [{
            'phone': str(get_werbe_value(row, 'phone_number')),
            'is_primary_phone': 1
        }]
    else:
        phone_nos = []
    
    new_contact = frappe.get_doc({
        'doctype': 'Contact',
        'first_name': first_name,
        'last_name': last_name,
        'salutation': salutation,
        'address': adresse,
        'email_ids': email_ids,
        'phone_nos': phone_nos,
        'links': [{
            'link_doctype': 'Customer',
            'link_name': kunde
        }],
        'idedoobox': str(get_werbe_value(row, 'id'))
    })
    new_contact.insert()
    
    return
