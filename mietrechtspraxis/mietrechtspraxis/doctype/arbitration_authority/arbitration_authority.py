# -*- coding: utf-8 -*-
# Copyright (c) 2021, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from datetime import datetime
from PyPDF2 import PdfFileWriter
from frappe.utils.file_manager import save_file

class ArbitrationAuthority(Document):
    pass


def _get_sb(**kwargs):
    '''
    call on [IP]/api/method/mietrechtspraxis.api.get_sb
    Mandatory Parameter:
        - plz
    '''
    
    # check that plz_city is present
    try:
        plz_city = kwargs['plz_city']
    except:
        # 400 Bad Request (Missing PLZ/City)
        return raise_4xx(400, 'Bad Request', 'PLZ/City Required')
        
    answer = []
    
    # lookup for plz
    city_results = frappe.db.sql("""
                                    SELECT
                                        `city`,
                                        `municipality`,
                                        `canton`,
                                        `pincode` AS `plz`
                                    FROM `tabPincode`
                                    WHERE `pincode` = '{plz_city}'
                                    ORDER BY `city` ASC
                                    """.format(plz_city=plz_city), as_dict=True)
    if len(city_results) < 1:
        # lookup for city
        city_results = frappe.db.sql("""
                                        SELECT
                                            `city`,
                                            `municipality`,
                                            `canton`,
                                            `pincode` AS `plz`
                                        FROM `tabPincode`
                                        WHERE `city` LIKE '%{plz_city}%'
                                        ORDER BY `city` ASC
                                        """.format(plz_city=plz_city), as_dict=True)
                            
    if len(city_results) > 0:
        for city in city_results:
            data = {}
            data['plz'] = city.plz
            data['ort'] = city.city
            data['gemeinde'] = city.municipality
            data['kanton'] = city.canton
            data['allgemein'] = get_informations(city.canton)
            schlichtungsbehoerden = frappe.db.sql("""
                                                                SELECT
                                                                    `schlichtungsbehoerde`.`titel` AS `Titel`,
                                                                    `schlichtungsbehoerde`.`name` AS `schlichtungsbehoerde_id`,
                                                                    `contact`.`phone` AS `Telefon`,
                                                                    `contact`.`email_id` AS `email`,
                                                                    `schlichtungsbehoerde`.`kuendigungstermine` AS `Kündigungstermine`,
                                                                    `schlichtungsbehoerde`.`pauschalen` AS `Pauschalen`,
                                                                    `schlichtungsbehoerde`.`rechtsberatung` AS `Rechtsberatung`,
                                                                    `schlichtungsbehoerde`.`elektronische_eingaben` AS `elektronische Eingaben`,
                                                                    `schlichtungsbehoerde`.`homepage` AS `Homepage`,
                                                                    `schlichtungsbehoerde`.`sb_sitz` AS `Sitz`,
                                                                    `address`.`plz` AS `plz`,
                                                                    `address`.`city` AS `ort`,
                                                                    `address`.`strasse` AS `strasse`,
                                                                    `address`.`zusatz` AS `adressen_zusatz`,
                                                                    NULL AS `zustaendig_fuer_gemeinden`
                                                                FROM `tabArbitration Authority` AS `schlichtungsbehoerde`
                                                                LEFT JOIN `tabMunicipality Table` AS `geminendentbl` ON `schlichtungsbehoerde`.`name`=`geminendentbl`.`parent`
                                                                LEFT JOIN `tabContact` AS `contact` ON `schlichtungsbehoerde`.`kontakt`=`contact`.`name`
                                                                LEFT JOIN `tabAddress` AS `address` ON `schlichtungsbehoerde`.`adresse`=`address`.`name`
                                                                WHERE `geminendentbl`.`municipality` = '{municipality}'
                                                                """.format(municipality=city.municipality), as_dict=True)
            
            
            for schlichtungsbehoerde in schlichtungsbehoerden:
                zustaendig_fuer_gemeinden = frappe.db.sql("""
                                                            SELECT
                                                                group_concat(`municipality` ORDER BY `municipality` ASC) `geminendentbl`
                                                            FROM `tabMunicipality Table` AS `geminendentbl`
                                                            WHERE `parent` = '{schlichtungsbehoerde_id}'
                                                            """.format(schlichtungsbehoerde_id=schlichtungsbehoerde.schlichtungsbehoerde_id), as_dict=True)
                if len(zustaendig_fuer_gemeinden) > 0:
                    schlichtungsbehoerde.zustaendig_fuer_gemeinden = zustaendig_fuer_gemeinden[0].geminendentbl
            
            data['schlichtungsbehoerde'] = schlichtungsbehoerden
            answer.append(data)
            
        if len(answer) > 0:
            return raise_200(answer)
        else:
            # 404 Not Found
            return raise_4xx(404, 'Not Found', 'No results')
    else:
        # 404 Not Found
        return raise_4xx(404, 'Not Found', 'No results')
        
def get_informations(kanton):
    search = frappe.db.sql("""
                            SELECT
                                `mietgerichte`,
                                `kosten`,
                                `anfangsmietzins`,
                                `anwalt_vertretung`,
                                `bemerkungen`,
                                `homepage`,
                                `formulare`,
                                `gesetzessammlung`
                            FROM `tabKantonsinformationen`
                            WHERE `kanton` = '{kanton}'
                            """.format(kanton=kanton), as_dict=True)
    if len(search) > 0:
        result = search[0]
    else:
        result = {}
    return result
        
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


@frappe.whitelist()
def get_sammel_pdf(no_letterhead=1):
    frappe.enqueue(method=_get_sammel_pdf, queue='long', job_name='Schlichtungsbehörden Sammel-PDF', **{'no_letterhead': no_letterhead})
    return

def _get_sammel_pdf(no_letterhead=1):
    output = PdfFileWriter()
    schlichtungsbehoerden = frappe.db.sql("""SELECT `name` FROM `tabArbitration Authority`""", as_dict=True)
    for schlichtungsbehoerde in schlichtungsbehoerden:
        output = frappe.get_print("Arbitration Authority", schlichtungsbehoerde.name, 'Datenüberprüfung', as_pdf = True, output = output, no_letterhead = no_letterhead)
        output = frappe.get_print("Arbitration Authority", schlichtungsbehoerde.name, 'Fragebogen für Schlichtungsbehörden', as_pdf = True, output = output, no_letterhead = no_letterhead)
    
    pdf = frappe.utils.pdf.get_file_data_from_writer(output)
    
    now = datetime.now()
    ts = "{0:04d}-{1:02d}-{2:02d}".format(now.year, now.month, now.day)
    file_name = "{0}_{1}.pdf".format('SB_Sammel-PDF', ts)
    save_file(file_name, pdf, '', '', is_private=1)
    return
    
