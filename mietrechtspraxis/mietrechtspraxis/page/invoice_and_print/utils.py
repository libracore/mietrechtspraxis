# -*- coding: utf-8 -*-
# Copyright (c) 2024, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def get_abos_for_invoicing(selected_type, year, qty=False, limit=False):
    filter_keine_doppel_rechnung = """SELECT `parent` FROM `tabmp Abo Invoice` WHERE `year` = '{year}'""".format(year=year)
    
    if limit:
        limit_filter = ' LIMIT {limit}'.format(limit=limit)
    else:
        limit_filter = ''

    if selected_type == 'invoice_inkl':
        # Rechnung & Zeitschrift (physikalisch & digital)
        abos_inkl = frappe.db.sql("""
                            SELECT
                                `a`.`name` AS `name`,
                                `a`.`magazines_qty_total` AS `print_jahr_qty`,
                                `a`.`digital_qty` AS `digital_jahr_qty`,
                                `a`.`gratis_print_qty` AS `print_gratis_qty`,
                                `a`.`gratis_digital_qty` AS `digital_gratis_qty`,
                                `a`.`legi_print_qty` AS `print_legi_qty`,
                                `a`.`legi_digital_qty` AS `digital_legi_qty`,
                                `r`.`magazines_qty_mr` AS `inhaber_exemplar`
                            FROM `tabmp Abo` AS `a`
                            LEFT JOIN `tabmp Abo Recipient` AS `r` ON `a`.`invoice_recipient` = `r`.`magazines_recipient`
                            WHERE
                                `r`.`magazines_qty_mr` > 0
                                AND `a`.`status` = 'Active'
                                AND `a`.`name` NOT IN ({filter_keine_doppel_rechnung})
                            ORDER BY `inhaber_exemplar` DESC
                            {limit_filter}
                            """.format(filter_keine_doppel_rechnung=filter_keine_doppel_rechnung, limit_filter=limit_filter), as_dict=True)
        if qty:
            return len(abos_inkl)
        else:
            return abos_inkl
    else:
        # Rechnung ohne Zeitschrift
        abos_exkl = frappe.db.sql("""
                            SELECT
                                `a`.`name` AS `name`,
                                `a`.`magazines_qty_total` AS `print_jahr_qty`,
                                `a`.`digital_qty` AS `digital_jahr_qty`,
                                `a`.`gratis_print_qty` AS `print_gratis_qty`,
                                `a`.`gratis_digital_qty` AS `digital_gratis_qty`,
                                `a`.`legi_print_qty` AS `print_legi_qty`,
                                `a`.`legi_digital_qty` AS `digital_legi_qty`,
                                0 AS `inhaber_exemplar`
                            FROM `tabmp Abo` AS `a`
                            WHERE `a`.`name` NOT IN (
                                    SELECT
                                        `a`.`name`
                                    FROM `tabmp Abo` AS `a`
                                    LEFT JOIN `tabmp Abo Recipient` AS `r` ON `a`.`invoice_recipient` = `r`.`magazines_recipient`
                                    WHERE
                                        `r`.`magazines_qty_mr` > 0
                            )
                            AND `a`.`name` NOT IN ({filter_keine_doppel_rechnung})
                            AND `a`.`status` = 'Active'
                            ORDER BY `qty_total` DESC
                            {limit_filter}
                            """.format(filter_keine_doppel_rechnung=filter_keine_doppel_rechnung, limit_filter=limit_filter), as_dict=True)
        if qty:
            return len(abos_exkl)
        else:
            return abos_exkl