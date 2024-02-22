# -*- coding: utf-8 -*-
# Copyright (c) 2024, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from mietrechtspraxis.mietrechtspraxis.doctype.mp_abo.mp_abo import valid_mp_web_user_abo

def validate_mp_web_user():
    antworten_auf_das_formular = frappe.db.sql("""
                                               SELECT `email`
                                               FROM `tabAntwort auf das Formular`
                                               WHERE
                                               `creation` < DATE_SUB(CURDATE(), INTERVAL 14 DAY);
                                               """, as_dict=True)
    for antwort_auf_das_formular in antworten_auf_das_formular:
        valid_mp_web_user_abo(antwort_auf_das_formular.email)
