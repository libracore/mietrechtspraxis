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
