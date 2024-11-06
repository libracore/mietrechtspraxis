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
                            WHERE `r`.`magazines_qty_mr` > 0
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
                            {limit_filter}
                            """.format(filter_keine_doppel_rechnung=filter_keine_doppel_rechnung, limit_filter=limit_filter), as_dict=True)
        if qty:
            return len(abos_exkl)
        else:
            return abos_exkl

def get_abos_for_begleitschreiben(typ, ausland=False):
    if typ == 'Kündigung':
        if ausland:
            land_filter = """
                AND `r`.`recipient_address` IN (SELECT `name` FROM `tabAddress` WHERE `country` != 'Schweiz')
            """
        else:
            land_filter = """
                AND `r`.`recipient_address` IN (SELECT `name` FROM `tabAddress` WHERE `country` = 'Schweiz')
            """
        abos = frappe.db.sql("""
                                SELECT
                                    `r`.`parent` AS `abo`,
                                    `r`.`magazines_qty_mr` AS `anz`,
                                    `r`.`magazines_recipient` AS `recipient_name`,
                                    `r`.`recipient_contact` AS `recipient_contact`,
                                    `r`.`recipient_address` AS `recipient_address`
                                FROM `tabmp Abo Recipient` AS `r`
                                LEFT JOIN `tabmp Abo` AS `a` ON `r`.`parent` = `a`.`name`
                                WHERE `a`.`status` = 'Actively terminated'
                                {land_filter}
                                ORDER BY `r`.`magazines_qty_mr` DESC
                            """.format(land_filter=land_filter), as_dict=True)
        return abos
    
    if typ in ['Gratis-Abo', 'Jahres-Abo', 'Jahres-Legi-Abo']:
        from datetime import datetime
        if typ == 'Gratis-Abo':
            typ_filter = """
                AND `r`.`abo_type` = 'Gratis-Abo'
                AND `r`.`magazines_recipient` NOT IN (
                    SELECT `invoice_recipient` FROM `tabmp Abo`
                    WHERE `name` IN (
                        SELECT `parent` FROM `tabmp Abo Invoice` WHERE `year` = '{year}'
                    )
                )
            """.format(year=datetime.now().year + 1)
        else:
            typ_filter = """
                AND `r`.`abo_type` IN ('Jahres-Abo', 'Jahres-Legi-Abo')
                AND `r`.`magazines_recipient` NOT IN (
                    SELECT `invoice_recipient` FROM `tabmp Abo`
                    WHERE `name` IN (
                        SELECT `parent` FROM `tabmp Abo Invoice` WHERE `year` = '{year}'
                    )
                )
            """.format(year=datetime.now().year + 1)

        if ausland:
            land_filter = """
                AND `r`.`recipient_address` IN (SELECT `name` FROM `tabAddress` WHERE `country` != 'Schweiz')
            """
        else:
            land_filter = """
                AND `r`.`recipient_address` IN (SELECT `name` FROM `tabAddress` WHERE `country` = 'Schweiz')
            """
        
        abos = frappe.db.sql("""
                                SELECT
                                    `r`.`parent` AS `abo`,
                                    `r`.`magazines_qty_mr` AS `anz`,
                                    `r`.`magazines_recipient` AS `recipient_name`,
                                    `r`.`recipient_contact` AS `recipient_contact`,
                                    `r`.`recipient_address` AS `recipient_address`
                                FROM `tabmp Abo Recipient` AS `r`
                                LEFT JOIN `tabmp Abo` AS `a` ON `r`.`parent` = `a`.`name`
                                WHERE `a`.`status` = 'Active'
                                {typ_filter}
                                {land_filter}
                                ORDER BY `r`.`magazines_qty_mr` DESC
                            """.format(land_filter=land_filter, typ_filter=typ_filter), as_dict=True)
        return abos