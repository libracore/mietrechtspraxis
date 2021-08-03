# -*- coding: utf-8 -*-
# Copyright (c) 2021, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _
import requests
import json
import hashlib
from cryptography.fernet import Fernet, InvalidToken
from frappe.utils import cstr, encode
from mietrechtspraxis.mietrechtspraxis.doctype.mp_abo.mp_abo import create_random_pw

class mietrechtspraxisAPI(Document):
	pass

def _request(**kwargs):
    '''
    call on [IP]/api/method/mietrechtspraxis.api.request
    Mandatory Parameter:
        - token
        - method
        - username
    '''
    
    # check that token is present
    try:
        token = kwargs['token']
    except:
        # 400 Bad Request (Missing Token)
        return raise_4xx(400, 'Bad Request', 'Token Required')
        
    # check that token is correct
    if not token == frappe.db.get_single_value('mietrechtspraxis API', 'token'):
        # 401 Unauthorized (Invalid Token)
        return raise_4xx(401, 'Unauthorized', 'Invalid Token')
        
    # route to method
    try:
        method = kwargs['method']
    except:
        # 400 Bad Request (Missing Method)
        return raise_4xx(400, 'Bad Request', 'Missing Method')
        
    if method == 'login':
        return check_login(**kwargs)
    elif method == 'update':
        return update(**kwargs)
    elif method == 'reset':
        return pw_reset(**kwargs)
    elif method == 'reset_mail':
        return pw_reset_mail(**kwargs)
    elif method == 'newsletter':
        return newsletter(**kwargs)
    else:
        # 404 Not Found (unknown method)
        return raise_4xx(404, 'Not Found', 'Unknown Method')
    
    
def check_login(**kwargs):
    # check username
    try:
        username = kwargs['username']
    except:
        # 400 Bad Request (Username Missing)
        return raise_4xx(400, 'Bad Request', 'Username Missing')
        
    mp_user = find_user(username)
    if mp_user:
        # check password
        try:
            password = kwargs['password']
        except:
            # 400 Bad Request (Password Missing)
            return raise_4xx(400, 'Bad Request', 'Password Missing')
            
        mp_password = hashlib.sha256()
        mp_password.update(encode("{pwd}".format(pwd=mp_user.mp_password)))
        if mp_password.hexdigest() == password:
            return raise_200()
        else:
            # 401 Unauthorized (Invalid Password)
            return raise_4xx(401, 'Unauthorized', 'Invalid Password')
    else:
        # 404 Not Found (No User-Credentials found)
        return raise_4xx(404, 'Not Found', 'No User-Credentials found')
    
def update(**kwargs):
    # check username
    try:
        username = kwargs['username']
    except:
        # 400 Bad Request (Username Missing)
        return raise_4xx(400, 'Bad Request', 'Username Missing')
        
    # check user data for update
    try:
        user_data = kwargs['user']
    except:
        # 400 Bad Request (User-Data Missing)
        return raise_4xx(400, 'Bad Request', 'User-Data Missing')
        
    mp_user = find_user(username)
    if mp_user:
        old_data = {}
        user_data = json.loads(kwargs['user'])
        if 'salutation' in user_data:
            old_data['salutation'] = mp_user.salutation
            mp_user.salutation = user_data['salutation']
        if 'firstname' in user_data:
            old_data['firstname'] = mp_user.first_name
            mp_user.first_name = user_data['firstname']
        if 'lastname' in user_data:
            old_data['lastname'] = mp_user.last_name
            mp_user.last_name = user_data['lastname']
        if 'email' in user_data:
            for email in mp_user.email_ids:
                if email.is_primary:
                    old_data['email'] = email.email_id
                    email.email_id = user_data['email']
                    mp_user.email_id = user_data['email']
        if 'newsletters' in user_data:
            old_data['newsletters'] = {}
            old_data['newsletters']['1'] = mp_user.nl_1
            old_data['newsletters']['2'] = mp_user.nl_2
            old_data['newsletters']['3'] = mp_user.nl_3
            old_data['newsletters']['4'] = mp_user.nl_4
            mp_user.nl_1 = user_data['newsletters']['1']
            mp_user.nl_2 = user_data['newsletters']['2']
            mp_user.nl_3 = user_data['newsletters']['3']
            mp_user.nl_4 = user_data['newsletters']['4']
        if 'new_password' in user_data:
            # zuerst encrypt(mp_user.mp_password)!!!
            old_data['password'] = mp_user.mp_password
            # zuerst decrypt(user_data['new_password'])!!!
            mp_user.mp_password = user_data['new_password']
        
        mp_user.save(ignore_permissions=True)
        frappe.db.commit()
        
        return raise_200({'old_data': old_data, 'updated_data': user_data})
    else:
        # 404 Not Found (No User found)
        return raise_4xx(404, 'Not Found', 'No User found')
    
def pw_reset(**kwargs):
    # check username
    try:
        username = kwargs['username']
    except:
        # 400 Bad Request (Username Missing)
        return raise_4xx(400, 'Bad Request', 'Username Missing')
        
    mp_user = find_user(username)
    if mp_user:
        # check new_password
        try:
            new_password = kwargs['new_password']
        except:
            # 400 Bad Request (New Password Missing)
            return raise_4xx(400, 'Bad Request', 'New Password Missing')
        # zuerst new_password = encrypt(new_password)!!!
        mp_user.mp_password = new_password
        mp_user.save(ignore_permissions=True)
        frappe.db.commit()
        return raise_200()
    else:
        # 404 Not Found (No User found)
        return raise_4xx(404, 'Not Found', 'No User found')
    
def pw_reset_mail(**kwargs):
    # check username
    try:
        username = kwargs['username']
    except:
        # 400 Bad Request (Username Missing)
        return raise_4xx(400, 'Bad Request', 'Username Missing')
        
    mp_user = find_user(username)
    if mp_user:
        if mp_user.email_id:
            new_password = create_random_pw()
            mp_user.mp_password = new_password
            mp_user.save(ignore_permissions=True)
            frappe.db.commit()
            frappe.sendmail(recipients=mp_user.email_id, message="Ihr neues Passwort lautet: {pwd}".format(pwd=new_password))
            return raise_200()
        else:
            # 400 Bad Request (User has no E-Mail)
            return raise_4xx(400, 'Bad Request', 'User has no E-Mail')
    else:
        # 404 Not Found (No User found)
        return raise_4xx(404, 'Not Found', 'No User found')
    
def newsletter(**kwargs):
    # check email
    try:
        email = kwargs['email']
    except:
        # 400 Bad Request (E-Mail Missing)
        return raise_4xx(400, 'Bad Request', 'E-Mail Missing')
        
    # check newsletter data
    try:
        newsletter = json.loads(kwargs['newsletters'])
    except:
        # 400 Bad Request (Newsletters Missing)
        return raise_4xx(400, 'Bad Request', 'Newsletters Missing')
        
    mp_user = find_user(username)
    if mp_user:
        old_data = {}
        old_data['newsletters'] = {}
        old_data['newsletters']['1'] = mp_user.nl_1
        old_data['newsletters']['2'] = mp_user.nl_2
        old_data['newsletters']['3'] = mp_user.nl_3
        old_data['newsletters']['4'] = mp_user.nl_4
        mp_user.nl_1 = newsletter['1']
        mp_user.nl_2 = newsletter['2']
        mp_user.nl_3 = newsletter['3']
        mp_user.nl_4 = newsletter['4']
        
        mp_user.save(ignore_permissions=True)
        frappe.db.commit()
        
        return raise_200({'old_data': old_data, 'updated_data': newsletter})
    else:
        # 404 Not Found (No User found)
        return raise_4xx(404, 'Not Found', 'No User found')
        
def find_user(search_key):
    # 1. Abo-Nr
    login = frappe.db.sql("""SELECT `name` FROM `tabContact` WHERE `mp_username` = '{search_key}'""".format(search_key=search_key), as_dict=True)
    if len(login) > 0:
        mp_user = frappe.get_doc("Contact", login[0].name)
        return mp_user
    else:
        # 2. old Abo-Nr.
        login = frappe.db.sql("""SELECT `name` FROM `tabContact` WHERE `mp_abo_old` = '{search_key}'""".format(search_key=search_key), as_dict=True)
        if len(login) > 0:
            mp_user = frappe.get_doc("Contact", login[0].name)
            return mp_user
        else:
            # 3. E-Mail based
            login = frappe.db.sql("""SELECT `name` FROM `tabContact` WHERE `email_id` = '{search_key}'""".format(search_key=search_key), as_dict=True)
            if len(login) > 0:
                mp_user = frappe.get_doc("Contact", login[0].name)
                return mp_user
            else:
                return False
    
def raise_4xx(code, title, message):
    # 4xx Bad Request / Unauthorized / Not Found
    return ['{code} {title}'.format(code=code, title=title), {
        "error": {
            "code": code,
            "message": "{message}".format(message=message)
        }
    }]
    
def raise_200(answer=False):
    # 200 OK
    if not answer:
        answer = {
            "code": 200,
            "message": "OK"
        }
    return ['200 OK', answer]
    

    
def get_encryption_key(new=False):
    if new:
        encryption_key = Fernet.generate_key().decode()
        return encryption_key
    else:
        return frappe.db.get_single_value('mietrechtspraxis API', 'secret_key')
    
def encrypt(pwd):
    if len(pwd) > 100:
        # encrypting > 100 chars will lead to truncation
        frappe.throw(_('Password cannot be more than 100 characters long'))

    cipher_suite = Fernet(encode(get_encryption_key()))
    cipher_text = cstr(cipher_suite.encrypt(encode(pwd)))
    return cipher_text

def decrypt(pwd):
    try:
        cipher_suite = Fernet(encode(get_encryption_key()))
        plain_text = cstr(cipher_suite.decrypt(encode(pwd)))
        return plain_text
    except InvalidToken:
        # encryption_key not valid
        frappe.throw(_('Encryption key is invalid'))
