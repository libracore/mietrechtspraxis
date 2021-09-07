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
            filters.append("""(`customers_search_mask`.`phone` LIKE '%{phone}%' OR `customers_search_mask`.`other_phones` LIKE '%{phone}%')""".format(phone=self.phone))
        if self.mobile:
            filters.append("""(`customers_search_mask`.`mobile_no` LIKE '%{mobile_no}%' OR `customers_search_mask`.`other_phones` LIKE '%{mobile_no}%')""".format(mobile_no=self.mobile))
        
        # address filters
        if self.address_line1:
            filters.append("""`customers_search_mask`.`strasse` LIKE '%{strasse}%'""".format(strasse=self.address_line1))
        if self.address_line2:
            filters.append("""`customers_search_mask`.`zusatz` LIKE '%{zusatz}%'""".format(zusatz=self.address_line2))
        if self.plz:
            filters.append("""`customers_search_mask`.`pincode` LIKE '%{pincode}%'""".format(pincode=self.plz))
        if self.city:
            filters.append("""`customers_search_mask`.`city` LIKE '%{city}%'""".format(city=self.city))
        if self.country:
            filters.append("""`customers_search_mask`.`country` LIKE '%{country}%'""".format(country=self.country))
            
        # company filters
        if self.is_company:
            if self.company:
                filters.append("""`customers_search_mask`.`customer_link` IN (SELECT `name` FROM `tabCustomer` WHERE `customer_type` = 'Company' AND `customer_name` LIKE '%{company}%')""".format(company=self.company))
            else:
                filters.append("""`customers_search_mask`.`customer_link` IN (SELECT `name` FROM `tabCustomer` WHERE `customer_type` = 'Company')""")
            
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
                `customers_search_mask`.`strasse`,
                `customers_search_mask`.`zusatz`,
                `customers_search_mask`.`city`,
                `customers_search_mask`.`pincode`,
                `customers_search_mask`.`country`,
                `customers_search_mask`.`customer_link`,
                `customers_search_mask`.`customer_name`
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
                    `tabAddress`.`strasse`,
                    `tabAddress`.`zusatz`,
                    `tabAddress`.`city`,
                    `tabAddress`.`pincode`,
                    `tabAddress`.`country`,
                    `DL1`.`link_name` AS `customer_link`,
                    `cus`.`customer_name` AS `customer_name`
                FROM `tabContact`
                JOIN `tabAddress` ON `tabContact`.`address` = `tabAddress`.`name`
                LEFT JOIN `tabDynamic Link` AS `DL1` ON (`tabContact`.`name` = `DL1`.`parent` AND `DL1`.`link_doctype` = 'Customer')
                LEFT JOIN `tabContact Email` AS `CE` ON (`tabContact`.`name` = `CE`.`parent` AND `CE`.`is_primary` != 1)
                LEFT JOIN `tabContact Phone` AS `CP` ON (`tabContact`.`name` = `CP`.`parent` AND `CP`.`is_primary_phone` != 1 AND `CP`.`is_primary_mobile_no` != 1)
                LEFT JOIN `tabCustomer` AS `cus` ON `DL1`.`link_name` = `cus`.`name`
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
                    NULL AS `strasse`,
                    NULL AS `zusatz`,
                    NULL AS `city`,
                    NULL AS `pincode`,
                    NULL AS `country`,
                    `DL1`.`link_name` AS `customer_link`,
                    `cus`.`customer_name` AS `customer_name`
                FROM `tabContact`
                LEFT JOIN `tabDynamic Link` AS `DL1` ON (`tabContact`.`name` = `DL1`.`parent` AND `DL1`.`link_doctype` = 'Customer')
                LEFT JOIN `tabContact Email` AS `CE` ON (`tabContact`.`name` = `CE`.`parent` AND `CE`.`is_primary` != 1)
                LEFT JOIN `tabContact Phone` AS `CP` ON (`tabContact`.`name` = `CP`.`parent` AND `CP`.`is_primary_phone` != 1 AND `CP`.`is_primary_mobile_no` != 1)
                LEFT JOIN `tabCustomer` AS `cus` ON `DL1`.`link_name` = `cus`.`name`
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
                    `tabAddress`.`strasse`,
                    `tabAddress`.`zusatz`,
                    `tabAddress`.`city`,
                    `tabAddress`.`pincode`,
                    `tabAddress`.`country`,
                    `DL1`.`link_name` AS `customer_link`,
                    `cus`.`customer_name` AS `customer_name`
                FROM `tabAddress`
                LEFT JOIN `tabDynamic Link` AS `DL1` ON (`tabAddress`.`name` = `DL1`.`parent` AND `DL1`.`link_doctype` = 'Customer')
                LEFT JOIN `tabCustomer` AS `cus` ON `DL1`.`link_name` = `cus`.`name`
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

@frappe.whitelist()
def create_customer(firstname, lastname, email, phone, mobile, address_line1, address_line2, plz, city, country, customer_type, customer_name):
    if customer_type == 'Individual':
        fullname = firstname if firstname != '!' else ''
        fullname += " " + lastname if lastname != '!' else ''
    else:
        fullname = customer_name
    
    # create customer
    customer = frappe.get_doc({
        "doctype": "Customer",
        "customer_type": customer_type,
        "customer_name": fullname
    })
    customer.insert()
    
    # create address
    address = frappe.get_doc({
        "doctype": "Address",
        "address_type": "Billing",
        "address_line1": address_line1,
        "address_line2": address_line2 if address_line2 != '!' else '',
        "strasse": address_line1,
        "zusatz": address_line2 if address_line2 != '!' else '',
        "city": city,
        "country": country if country != '!' else '',
        "pincode": plz,
        "links": [
            {
                "link_doctype": "Customer",
                "link_name": customer.name
            }
        ]
        
    })
    address.insert()
    
    # create contact
    numbers = []
    if phone != '!':
        primary_phone = {
                            "phone": phone,
                            "is_primary_phone": 1
                        }
        numbers.append(primary_phone)
    if mobile != '!':
        primary_mobile = {
                            "phone": mobile,
                            "is_primary_mobile_no": 1
                        }
        numbers.append(primary_mobile)
    
    contact = frappe.get_doc({
        "doctype": "Contact",
        "first_name": firstname if firstname != '!' else '-',
        "last_name": lastname if lastname != '!' else '',
        "address": address.name,
        "email_ids": [
            {
                "email_id": email,
                "is_primary": 1
            }
        ] if email != '!' else [],
        "phone_nos": numbers,
        "links": [
            {
                "link_doctype": "Customer",
                "link_name": customer.name
            }
        ]
        
    })
    contact.insert()

    return customer.name
