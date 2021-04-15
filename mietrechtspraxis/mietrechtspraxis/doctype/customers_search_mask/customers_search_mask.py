# -*- coding: utf-8 -*-
# Copyright (c) 2021, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class CustomersSearchMask(Document):
    def search(self):
        filters = []
        query_filter = ''
        
        # contact filters
        if self.firstname:
            filters.append("""`customers_search_mask`.`first_name` LIKE '%{first_name}%'""".format(first_name=self.firstname))
        if self.lastname:
            filters.append("""`customers_search_mask`.`last_name` LIKE '%{last_name}%'""".format(last_name=self.lastname))
        if self.email:
            filters.append("""(`customers_search_mask`.`email_id` LIKE '%{email_id}%' OR `customers_search_mask`.`other_mails` LIKE '%{email_id}%')""".format(email_id=self.email))
        if self.phone:
            filters.append("""AND (`customers_search_mask`.`phone` LIKE '%{phone}%' OR `customers_search_mask`.`other_phones` LIKE '%{phone}%')""".format(phone=self.phone))
        if self.mobile:
            filters.append("""(`customers_search_mask`.`mobile_no` LIKE '%{mobile_no}%' OR `customers_search_mask`.`other_phones` LIKE '%{mobile_no}%')""".format(mobile_no=self.mobile))
        
        # address filters
        if self.address_line1:
            filters.append("""`customers_search_mask`.`address_line1` LIKE '%{address_line1}%'""".format(address_line1=self.address_line1))
        if self.address_line2:
            filters.append("""`customers_search_mask`.`address_line2` LIKE '%{address_line2}%'""".format(address_line2=self.address_line2))
        if self.plz:
            filters.append("""`customers_search_mask`.`pincode` LIKE '%{pincode}%'""".format(pincode=self.plz))
        if self.city:
            filters.append("""`customers_search_mask`.`city` LIKE '%{city}%'""".format(city=self.city))
        if self.country:
            filters.append("""`customers_search_mask`.`country` LIKE '%{country}%'""".format(country=self.country))
            
        if len(filters) > 0:
            query_filter = 'WHERE ' + ' AND '.join(filters)
        
        sql_query = ("""
            SELECT
                `customers_search_mask`.`contact_name`,
                `customers_search_mask`.`first_name`,
                `customers_search_mask`.`last_name`,
                `customers_search_mask`.`email_id`,
                `customers_search_mask`.`other_mails`,
                `customers_search_mask`.`phone`,
                `customers_search_mask`.`mobile_no`,
                `customers_search_mask`.`other_phones`,
                `customers_search_mask`.`address_name`,
                `customers_search_mask`.`address_line1`,
                `customers_search_mask`.`address_line2`,
                `customers_search_mask`.`city`,
                `customers_search_mask`.`pincode`,
                `customers_search_mask`.`country`,
                `customers_search_mask`.`customer_link`
            FROM (
                -- all contacts with linked address
                SELECT
                    `tabContact`.`name` AS `contact_name`,
                    `tabContact`.`first_name`,
                    `tabContact`.`last_name`,
                    `tabContact`.`email_id`,
                    GROUP_CONCAT(`CE`.`email_id`) AS `other_mails`,
                    `tabContact`.`phone`,
                    `tabContact`.`mobile_no`,
                    GROUP_CONCAT(`CP`.`phone`) AS `other_phones`,
                    `tabAddress`.`name` AS `address_name`,
                    `tabAddress`.`address_line1`,
                    `tabAddress`.`address_line2`,
                    `tabAddress`.`city`,
                    `tabAddress`.`pincode`,
                    `tabAddress`.`country`,
                    `DL1`.`link_name` AS `customer_link`
                FROM `tabContact`
                JOIN `tabAddress` ON `tabContact`.`address` = `tabAddress`.`name`
                LEFT JOIN `tabDynamic Link` AS `DL1` ON (`tabContact`.`name` = `DL1`.`parent` AND `DL1`.`link_doctype` = 'Customer')
                LEFT JOIN `tabContact Email` AS `CE` ON (`tabContact`.`name` = `CE`.`parent` AND `CE`.`is_primary` != 1)
                LEFT JOIN `tabContact Phone` AS `CP` ON (`tabContact`.`name` = `CP`.`parent` AND `CP`.`is_primary_phone` != 1 AND `CP`.`is_primary_mobile_no` != 1)
                GROUP BY `DL1`.`link_name`, `tabContact`.`name`
                UNION
                -- all contacts without linked address
                SELECT
                    `tabContact`.`name` AS `contact_name`,
                    `tabContact`.`first_name`,
                    `tabContact`.`last_name`,
                    `tabContact`.`email_id`,
                    GROUP_CONCAT(`CE`.`email_id`) AS `other_mails`,
                    `tabContact`.`phone`,
                    `tabContact`.`mobile_no`,
                    GROUP_CONCAT(`CP`.`phone`) AS `other_phones`,
                    NULL AS `address_name`,
                    NULL AS `address_line1`,
                    NULL AS `address_line2`,
                    NULL AS `city`,
                    NULL AS `pincode`,
                    NULL AS `country`,
                    `DL1`.`link_name` AS `customer_link`
                FROM `tabContact`
                LEFT JOIN `tabDynamic Link` AS `DL1` ON (`tabContact`.`name` = `DL1`.`parent` AND `DL1`.`link_doctype` = 'Customer')
                LEFT JOIN `tabContact Email` AS `CE` ON (`tabContact`.`name` = `CE`.`parent` AND `CE`.`is_primary` != 1)
                LEFT JOIN `tabContact Phone` AS `CP` ON (`tabContact`.`name` = `CP`.`parent` AND `CP`.`is_primary_phone` != 1 AND `CP`.`is_primary_mobile_no` != 1)
                WHERE `tabContact`.`address` IS NULL
                GROUP BY `DL1`.`link_name`, `tabContact`.`name`
                UNION
                -- all addresses which are not linked in a contact
                SELECT
                    NULL AS `contact_name`,
                    NULL AS `first_name`,
                    NULL AS `last_name`,
                    NULL AS `email_id`,
                    NULL AS `other_mails`,
                    NULL AS `phone`,
                    NULL AS `mobile_no`,
                    NULL AS `other_phones`,
                    `tabAddress`.`name` AS `address_name`,
                    `tabAddress`.`address_line1`,
                    `tabAddress`.`address_line2`,
                    `tabAddress`.`city`,
                    `tabAddress`.`pincode`,
                    `tabAddress`.`country`,
                    `DL1`.`link_name` AS `customer_link`
                FROM `tabAddress`
                LEFT JOIN `tabDynamic Link` AS `DL1` ON (`tabAddress`.`name` = `DL1`.`parent` AND `DL1`.`link_doctype` = 'Customer')
                WHERE `tabAddress`.`name` NOT IN (
                    SELECT `tabContact`.`address` FROM `tabContact` WHERE `tabContact`.`address` IS NOT NULL
                )
            ) AS `customers_search_mask`
            {query_filter}
        """.format(query_filter=query_filter))
        search_results = frappe.db.sql(sql_query, as_dict=True)
            
        return search_results
        
    def validate(self):
        self.get("__onload")['search_results'] = self.search()
    def onload(self):
        self.get("__onload")['search_results'] = self.search()
    pass
