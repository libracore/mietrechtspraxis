# -*- coding: utf-8 -*-
# Copyright (c) 2021, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class CustomersSearchMask(Document):
    def search(self):
        where_clause = ''
        if self.firstname:
            where_clause += """ AND `first_name` LIKE '%{first_name}%'""".format(first_name=self.firstname)
        if self.lastname:
            where_clause += """ AND `last_name` LIKE '%{last_name}%'""".format(last_name=self.lastname)
        if self.email:
            where_clause += """ AND `email_id` LIKE '%{email_id}%'""".format(email_id=self.email)
        if self.phone:
            where_clause += """ AND `phone` LIKE '%{phone}%'""".format(phone=self.phone)
        if self.mobile:
            where_clause += """ AND `mobile_no` LIKE '%{mobile_no}%'""".format(mobile_no=self.mobile)
        
        contact_sql_query = ("""SELECT * FROM `tabContact` WHERE
                                    `docstatus` = 0{where_clause}""".format(where_clause=where_clause))
        contacts = frappe.db.sql(contact_sql_query, as_dict=True)
        
        for contact in contacts:
            contact_record = frappe.get_doc("Contact", contact.name)
            contact['email_ids'] = contact_record.email_ids
            contact['phone_nos'] = contact_record.phone_nos
            
        return contacts
        
    def validate(self):
        self.get("__onload")['search_results'] = self.search()
    def onload(self):
        self.get("__onload")['search_results'] = self.search()
    pass
