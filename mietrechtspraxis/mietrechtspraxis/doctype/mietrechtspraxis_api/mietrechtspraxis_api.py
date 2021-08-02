# -*- coding: utf-8 -*-
# Copyright (c) 2021, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _
import requests
import json

class mietrechtspraxisAPI(Document):
	pass

def _request(**kwargs):
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
        
    login = frappe.db.sql("""SELECT `mp_password` FROM `tabContact` WHERE `mp_username` = '{username}'""".format(username=username), as_dict=True)
    if len(login) > 0:
        login = login[0]
        
        # check password
        try:
            password = kwargs['password']
        except:
            # 400 Bad Request (Password Missing)
            return raise_4xx(400, 'Bad Request', 'Password Missing')
            
        if login.mp_password == password:
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
        
    login = frappe.db.sql("""SELECT `name` FROM `tabContact` WHERE `mp_username` = '{username}'""".format(username=username), as_dict=True)
    if len(login) > 0:
        mp_user = frappe.get_doc("Contact", login[0].name)
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
            old_data['password'] = mp_user.mp_password
            mp_user.mp_password = user_data['new_password']
        
        mp_user.save(ignore_permissions=True)
        frappe.db.commit()
        
        return raise_200({'old_data': old_data, 'updated_data': user_data})
    else:
        # 404 Not Found (No User found)
        return raise_4xx(404, 'Not Found', 'No User found')
    
def pw_reset(**kwargs):
    return
    
def pw_reset_mail(**kwargs):
    return
    
def newsletter(**kwargs):
    return
    
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
