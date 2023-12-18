# -*- coding: utf-8 -*-
# Copyright (c) 2021, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def deactivate_abo_user():
    def has_valid_abo(username):
        active_abo_qty = frappe.db.count('mp Abo', {'status': ['!=', 'Inactive'], 'abo_user': username})
        if active_abo_qty > 0:
            return True
        else:
            return False
    
    def has_valid_bestellung(username):
        # welche bestellung?!
        return False
    
    def deactivate_abo_user(default_role, username):
        frappe.db.sql("""
            DELETE FROM `tabHas Role` WHERE `role` = '{default_role}' AND `parent` = '{username}'
        """.format(default_role=default_role, username=username))
        frappe.clear_cache()
        return True
    
    default_role = frappe.db.get_single_value('mp Abo Settings', 'rolle_abo_inhaber') or 'undefined'
    active_abo_users = frappe.db.sql("""
        SELECT `parent` AS `user` FROM `tabHas Role`
        WHERE `role` = '{default_role}'
    """.format(default_role=default_role), as_dict=True)

    for active_abo_user in active_abo_users:
        if not has_valid_abo(active_abo_user.user):
            if not has_valid_bestellung(active_abo_user.user):
                deactivate_abo_user(default_role, active_abo_user.user)
    
    return