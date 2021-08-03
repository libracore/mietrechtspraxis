# -*- coding: utf-8 -*-
# Copyright (c) 2021, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class ArbitrationAuthority(Document):
    pass


def _get_sb(**kwargs):
    '''
    call on [IP]/api/method/mietrechtspraxis.api.get_sb
    Mandatory Parameter:
        - token
        - plz
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
    
    # check that plz is present
    try:
        plz = kwargs['plz']
    except:
        # 400 Bad Request (Missing PLZ)
        return raise_4xx(400, 'Bad Request', 'PLZ Required')
        
    search = frappe.db.sql("""
                                SELECT
                                    `schlichtungsbehoerde`.`titel` AS `Titel`,
                                    `schlichtungsbehoerde`.`telefon` AS `Telefon`,
                                    `schlichtungsbehoerde`.`kuendigungstermine` AS `Kündigungstermine`,
                                    `schlichtungsbehoerde`.`pauschalen` AS `Pauschalen`,
                                    `schlichtungsbehoerde`.`rechtsberatung` AS `Rechtsberatung`,
                                    `schlichtungsbehoerde`.`elektronische_eingaben` AS `elektronische Eingaben`,
                                    `schlichtungsbehoerde`.`homepage` AS `Homepage`,
                                    GROUP_CONCAT(`geminendentbl`.`gemeinde` ORDER BY `geminendentbl`.`gemeinde` ASC SEPARATOR ', ') AS `Zuständig für die Gemeinden`
                                FROM `tabArbitration Authority` AS `schlichtungsbehoerde`
                                LEFT JOIN `tabGemeinde Multiselect` AS `geminendentbl` ON `schlichtungsbehoerde`.`name`=`geminendentbl`.`parent`
                                WHERE `schlichtungsbehoerde`.`name` IN (
                                    SELECT `parent` FROM `tabGemeinde Multiselect`
                                    WHERE `name` IN (
                                        SELECT `municipality` FROM `tabPincode`
                                        WHERE `pincode` = '{plz}'
                                    )
                                )""".format(plz=plz), as_dict=True)
    if len(search) > 0 and search[0]['Titel']:
        result = search[0]
        answer = {
            'Allgemein': get_informations(plz),
            'Schlichtungsbehörde': result
        }
        return raise_200(answer)
    else:
        # 404 Not Found
        return raise_4xx(404, 'Not Found', 'No results')
        
def get_informations(plz):
    kanton = frappe.db.sql("""
                            SELECT `canton` FROM `tabPincode`
                            WHERE `pincode` = '{plz}'
                            """.format(plz=plz), as_dict=True)
    
    if len(kanton) > 0:
        search = frappe.db.sql("""
                                SELECT
                                    `informationen`,
                                    `homepage`,
                                    `gesetzessammlung`,
                                    `formulare`
                                FROM `tabKantonsinformationen`
                                WHERE `name` = '{kanton}'
                                """.format(kanton=kanton[0].canton), as_dict=True)
        if len(search) > 0:
            result = search[0]
        else:
            result = {}
        return result
    else:
        # 404 Not Found
        return raise_4xx(404, 'Not Found', 'No results')
        
def raise_4xx(code, title, message):
    # 4xx Bad Request / Unauthorized / Not Found
    return ['{code} {title}'.format(code=code, title=title), {
        "error": {
            "code": code,
            "message": "{message}".format(message=message)
        }
    }]
    
def raise_200(answer):
    return ['200 OK', answer]
