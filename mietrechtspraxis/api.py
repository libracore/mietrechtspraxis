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
