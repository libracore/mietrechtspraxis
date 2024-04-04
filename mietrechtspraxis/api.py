# -*- coding: utf-8 -*-
# Copyright (c) 2021, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _
import requests
from mietrechtspraxis.mietrechtspraxis.doctype.mietrechtspraxis_api.mietrechtspraxis_api import _request
from mietrechtspraxis.mietrechtspraxis.doctype.arbitration_authority.arbitration_authority import _get_sb
from datetime import datetime
from frappe.config import get_modules_from_all_apps
from frappe.exceptions import DoesNotExistError

@frappe.whitelist(allow_guest=True)
def request(**kwargs):
    return _request(**kwargs)

@frappe.whitelist(allow_guest=True)
def get_sb(**kwargs):
    return _get_sb(**kwargs)

@frappe.whitelist(allow_guest=True)
def mp_shop(**kwargs):
    def get_mp_shop_item_groups():
        item_groups = frappe.db.sql("""SELECT
                                            `name` AS `item_group`,
                                            `description` AS `description`
                                        FROM `tabItem Group`
                                        WHERE `show_in_website` = 1
                                        ORDER BY `weightage` ASC
                                    """, as_dict=True)
        return item_groups
    
    def get_mp_shop_items(item_group):
        items = frappe.db.sql("""SELECT
                                    `name` AS `item_code`,
                                    `item_name` AS `item_name`,
                                    `web_long_description` AS `description`,
                                    NULL AS `rate`,
                                    `website_image` AS `image`
                                FROM `tabItem`
                                WHERE `show_in_website` = 1
                                AND `name` IN (
                                    SELECT
                                        `parent`
                                    FROM `tabWebsite Item Group`
                                    WHERE `item_group` = '{item_group}'
                                )
                                ORDER BY `weightage` ASC
                            """.format(item_group=item_group), as_dict=True)
        for item in items:
            item = get_mp_shop_rate(item)
        
        return items
    
    def get_mp_shop_rate(item):
        rate = frappe.db.sql("""SELECT
                                    `price_list_rate` AS `rate`
                                FROM `tabItem Price`
                                WHERE `item_code` = '{item_code}'
                                AND `selling` = 1
                                AND (
                                    `valid_from` IS NULL
                                    OR
                                    `valid_from` <= CURDATE()
                                )
                                AND (
                                    `valid_upto` IS NULL
                                    OR
                                    `valid_upto` >= CURDATE()
                                )
                                ORDER BY `price_list_rate` DESC
                            """.format(item_code=item.item_code), as_dict=True)
        
        return_rate = 0
        if len(rate) > 1:
            return_rate = rate[0].rate
            frappe.log_error("Mehere Preise für {item_code} gefunden!".format(item_code=item.item_code), "MP Shop API")
        if len(rate) < 1:
            frappe.log_error("Kein Preis für {item_code} gefunden!".format(item_code=item.item_code), "MP Shop API")
        else:
            return_rate = rate[0].rate
        
        item.rate = return_rate
        return item
    
    data = []
    item_groups = get_mp_shop_item_groups()
    
    for item_group in item_groups:
        items = get_mp_shop_items(item_group.item_group)
        
        data.append({
            'item_group': item_group.item_group,
            'description': item_group.description,
            'items': items
        })
    
    return data

@frappe.whitelist(allow_guest=True)
def check_hash_and_create_user(**kwargs):
    if not kwargs['hash'] and not kwargs['e_mail']:
        raise frappe.AuthenticationError
    if kwargs['hash'] == '' or kwargs['e_mail'] == '':
        raise frappe.AuthenticationError
    
    contacts = frappe.db.sql("""
                                SELECT `name`
                                FROM `tabContact`
                                WHERE `erstregistrations_hash` = '{0}'
                            """.format(kwargs['hash']), as_dict=True)
    
    if len(contacts) != 1:
        raise frappe.AuthenticationError
    else:
        contact = frappe.get_doc("Contact", contacts[0].name)
        if contact.mp_web_user:
            raise frappe.AuthenticationError
        from mietrecht_ch.mietrecht_ch.doctype.antwort_auf_das_formular.api import __add_role_mp__, __create_base_user__, clean_response
        MP_ABO_ROLE = "mp_web_user_abo"
        try:
            user = frappe.get_doc('User', kwargs['e_mail'])
            __add_role_mp__(user)
        except DoesNotExistError:
            request_data = {
                'email': kwargs['e_mail'],
                'billing_address': {
                    'first_name': contact.first_name,
                    'last_name': contact.last_name
                }
            }
            user = __create_base_user__(request_data)
            __add_role_mp__(user)
        except:
            clean_response()
            raise frappe.AuthenticationError
        finally:
            contact.mp_web_user = user.name
            row = contact.append('email_ids', {})
            row.email_id = kwargs['e_mail']
            row.is_primary = 1
            contact.save(ignore_permissions=True)
            frappe.clear_messages()
            clean_response()

@frappe.whitelist(allow_guest=True)
def check_reset_password(user):
    if user=="Administrator":
        return 'not allowed'

    try:
        user = frappe.get_doc("User", user)
        if not user.enabled:
            return 'disabled'

        reset_password(user.name)

        return frappe.msgprint(_("Password reset instructions have been sent to your email"))

    except frappe.DoesNotExistError:
        frappe.clear_messages()
        return 'not found'

def reset_password(user):
    from frappe.utils import random_string, get_url

    key = random_string(32)
    frappe.db.set_value("User", user, 'reset_password_key', key)

    url = "/pwd-update?key=" + key

    link = get_url(url)
    
    send_login_mail(user, "Passwort zurücksetzen", "pwd_reset_mail", {"link": link}, now=True)

    return link

def send_login_mail(username, subject, template, add_args, now=None):
    """send mail with login details"""
    from frappe.utils.user import get_user_fullname
    from frappe.utils import get_url

    user = frappe.get_doc("User", username)
    full_name = get_user_fullname(frappe.session['user'])
    if full_name == "Guest":
        full_name = "Administrator"
    

    args = {
        'first_name': user.first_name or user.last_name or "",
        'last_name': user.last_name or "",
        'user': user.name,
        'title': subject,
        'login_url': get_url(),
        'user_fullname': full_name
    }

    args.update(add_args)

    sender = full_name

    frappe.sendmail(recipients=user.email, sender=sender, subject=subject,
        template=template, args=args, header=[subject, "green"],
        delayed=(not now) if now!=None else user.flags.delay_emails, retry=3)

@frappe.whitelist(allow_guest=True)
def _update_password(new_password, logout_all_sessions=0, key=None, old_password=None):
    from frappe.core.doctype.user.user import update_password
    finish = update_password(new_password, logout_all_sessions, key, old_password)
    return 'https://www.mietrecht.ch/'