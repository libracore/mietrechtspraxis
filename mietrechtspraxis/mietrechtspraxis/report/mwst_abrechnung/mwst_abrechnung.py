# Copyright (c) 2021, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from datetime import datetime, timedelta
from frappe import _

def execute(filters=None):
	columns = get_columns()
	
	data = get_data(filters.from_date, filters.to_date)
	
	return columns, data

def get_columns():
    return [
        {"label": _("Beschreibung"), "fieldname": "description", "fieldtype": "Data", "width": 200},
        {"label": _("Konto"), "fieldname": "account", "fieldtype": "Data", "width": 150},
        {"label": _("Betrag"), "fieldname": "amount", "fieldtype": "Data", "width": 150},
        {"label": _("Steuer"), "fieldname": "tax", "fieldtype": "Data", "width": 150}
    ]

def get_data(from_date, to_date):
    data = []
    
    data.append({'description': '<b>Umsätze</b>', 'account': '<b>Konto</b>', 'amount': '<b>Betrag</b>', 'tax': '<b>Steuer</b>'})
    
    summe_0p1 = 0.0
    summe_0p6 = 0.0
    summe_1p2 = 0.0
    summe_3p5 = 0.0
    summe_5p9 = 0.0
    summe_0p0 = 0.0
    summe_0p0spen = 0.0
    # 3000, 0.1
    sql_query = """SELECT 1.025 * IFNULL(SUM(`credit` - `debit`), 0) AS `amount` 
                   FROM `tabGL Entry` 
                   WHERE `posting_date` >= "{from_date}" 
                         AND `posting_date` <= "{to_date}" 
                         AND `account` LIKE "3000%MP";""".format(from_date=from_date, to_date=to_date)
    betrag = frappe.db.sql(sql_query, as_dict=True)[0]['amount']
    summe_0p1 += betrag
    data.append({'description': '', 'account': '3000', 'amount': "CHF {:,.2f}".format(betrag).replace(",", "'"), 'tax': ''})
    # 3100, 0.1
    sql_query = """SELECT 1.025 * IFNULL(SUM(`credit` - `debit`), 0) AS `amount` 
                   FROM `tabGL Entry` 
                   WHERE `posting_date` >= "{from_date}" 
                         AND `posting_date` <= "{to_date}" 
                         AND `account` LIKE "3100%MP";""".format(from_date=from_date, to_date=to_date)
    betrag = frappe.db.sql(sql_query, as_dict=True)[0]['amount']
    summe_0p1 += betrag
    data.append({'description': 'MV01 - 0.1%', 'account': '3100', 'amount': "CHF {:,.2f}".format(betrag).replace(",", "'"), 'tax': ''})
    #total 0.1%
    tax_0p1 = summe_0p1 * 0.001
    data.append({'description': '', 'account': '<b>Total</b>', 'amount': "<b>CHF {:,.2f}</b>".format(summe_0p1).replace(",", "'"), 
                 'tax': "<b>CHF {:,.2f}</b>".format(tax_0p1).replace(",", "'") })   
   # 3300.06, 0.6
    sql_query = """SELECT 1.025 * IFNULL(SUM(`credit` - `debit`), 0) AS `amount` 
                   FROM `tabGL Entry` 
                   WHERE `posting_date` >= "{from_date}" 
                         AND `posting_date` <= "{to_date}" 
                         AND `account` LIKE "3300%MP";""".format(from_date=from_date, to_date=to_date)
    betrag = frappe.db.sql(sql_query, as_dict=True)[0]['amount']
    summe_0p6 += betrag
    data.append({'description': '', 'account': '3300.06', 'amount': "CHF {:,.2f}".format(betrag).replace(",", "'"), 'tax': ''})
    # 3310, 0.6
    sql_query = """SELECT 1.025 * IFNULL(SUM(`credit` - `debit`), 0) AS `amount` 
                   FROM `tabGL Entry` 
                   WHERE `posting_date` >= "{from_date}" 
                         AND `posting_date` <= "{to_date}" 
                         AND `account` LIKE "3310%MP";""".format(from_date=from_date, to_date=to_date)
    betrag = frappe.db.sql(sql_query, as_dict=True)[0]['amount']
    summe_0p6 += betrag
    data.append({'description': 'MV06 - 0.6%', 'account': '3310', 'amount': "CHF {:,.2f}".format(betrag).replace(",", "'"), 'tax': ''})
    #total 0.6%
    tax_0p6 = summe_0p6 * 0.006
    data.append({'description': '', 'account': '<b>Total</b>', 'amount': "<b>CHF {:,.2f}</b>".format(summe_0p6).replace(",", "'"), 
                 'tax': "<b>CHF {:,.2f}</b>".format(tax_0p6).replace(",", "'") })
    # 3110, 1.2
    sql_query = """SELECT 1.077 * IFNULL(SUM(`credit` - `debit`), 0) AS `amount` 
                   FROM `tabGL Entry` 
                   WHERE `posting_date` >= "{from_date}" 
                         AND `posting_date` <= "{to_date}" 
                         AND `account` LIKE "3110%MP";""".format(from_date=from_date, to_date=to_date)
    betrag = frappe.db.sql(sql_query, as_dict=True)[0]['amount']
    summe_1p2 += betrag
    data.append({'description': 'MV12 - 1.2%', 'account': '3110', 'amount': "CHF {:,.2f}".format(betrag).replace(",", "'"), 'tax': ''})
    #total 1.2%
    tax_1p2 = summe_1p2 * 0.012
    data.append({'description': '', 'account': '<b>Total</b>', 'amount': "<b>CHF {:,.2f}</b>".format(summe_1p2).replace(",", "'"), 
                 'tax': "<b>CHF {:,.2f}</b>".format(tax_1p2).replace(",", "'") })
    # 3300.35, 3.5
    sql_query = """SELECT 1.077 * IFNULL(SUM(`credit` - `debit`), 0) AS `amount` 
                   FROM `tabGL Entry` 
                   WHERE `posting_date` >= "{from_date}" 
                         AND `posting_date` <= "{to_date}" 
                         AND `account` LIKE "3300.35%MP";""".format(from_date=from_date, to_date=to_date)
    betrag = frappe.db.sql(sql_query, as_dict=True)[0]['amount']
    summe_3p5 += betrag
    data.append({'description': '', 'account': '3300.35', 'amount': "CHF {:,.2f}".format(betrag).replace(",", "'"), 'tax': ''})
    # 3320.35, 3.5
    sql_query = """SELECT 1.077 * IFNULL(SUM(`credit` - `debit`), 0) AS `amount` 
                   FROM `tabGL Entry` 
                   WHERE `posting_date` >= "{from_date}" 
                         AND `posting_date` <= "{to_date}" 
                         AND `account` LIKE "3320.35%MP";""".format(from_date=from_date, to_date=to_date)
    betrag = frappe.db.sql(sql_query, as_dict=True)[0]['amount']
    summe_3p5 += betrag
    data.append({'description': '', 'account': '3320.35', 'amount': "CHF {:,.2f}".format(betrag).replace(",", "'"), 'tax': ''})
    # 3601, 3.5 verrechnung an sektion gibts auch mit 2.5 mwst, beides
    sql_query = """SELECT 1.077 * IFNULL(SUM(`credit` - `debit`), 0) AS `amount` 
                   FROM `tabGL Entry` 
                   WHERE `posting_date` >= "{from_date}" 
                         AND `posting_date` <= "{to_date}" 
                         AND `account` LIKE "3601%MP";""".format(from_date=from_date, to_date=to_date)
    betrag = frappe.db.sql(sql_query, as_dict=True)[0]['amount']
    summe_3p5 += betrag
    data.append({'description': 'MV35 - 3.5%', 'account': '3601', 'amount': "CHF {:,.2f}".format(betrag).replace(",", "'"), 'tax': ''})
    #total 3.5%
    tax_3p5 = summe_3p5 * 0.035
    data.append({'description': '', 'account': '<b>Total</b>', 'amount': "<b>CHF {:,.2f}</b>".format(summe_3p5).replace(",", "'"), 
                 'tax': "<b>CHF {:,.2f}</b>".format(tax_3p5).replace(",", "'") })
    # 3300.59, 5.9
    sql_query = """SELECT 1.077 * IFNULL(SUM(`credit` - `debit`), 0) AS `amount` 
                   FROM `tabGL Entry` 
                   WHERE `posting_date` >= "{from_date}" 
                         AND `posting_date` <= "{to_date}" 
                         AND `account` LIKE "3300.59%MP";""".format(from_date=from_date, to_date=to_date)
    betrag = frappe.db.sql(sql_query, as_dict=True)[0]['amount']
    summe_5p9 += betrag
    data.append({'description': '', 'account': '3300.59', 'amount': "CHF {:,.2f}".format(betrag).replace(",", "'"), 'tax': ''})
    # 3400, 5.9
    sql_query = """SELECT 1.077 * IFNULL(SUM(`credit` - `debit`), 0) AS `amount` 
                   FROM `tabGL Entry` 
                   WHERE `posting_date` >= "{from_date}" 
                         AND `posting_date` <= "{to_date}" 
                         AND `account` LIKE "3400%MP";""".format(from_date=from_date, to_date=to_date)
    betrag = frappe.db.sql(sql_query, as_dict=True)[0]['amount']
    summe_5p9 += betrag
    data.append({'description': '', 'account': '3400', 'amount': "CHF {:,.2f}".format(betrag).replace(",", "'"), 'tax': ''})
    # 3610, 5.9
    sql_query = """SELECT 1.077 * IFNULL(SUM(`credit` - `debit`), 0) AS `amount` 
                   FROM `tabGL Entry` 
                   WHERE `posting_date` >= "{from_date}" 
                         AND `posting_date` <= "{to_date}" 
                         AND `account` LIKE "3610%MP";""".format(from_date=from_date, to_date=to_date)
    betrag = frappe.db.sql(sql_query, as_dict=True)[0]['amount']
    summe_5p9 += betrag
    data.append({'description': 'MV59 - 5.9%', 'account': '3610', 'amount': "CHF {:,.2f}".format(betrag).replace(",", "'"), 'tax': ''})
    #total 5.9%
    tax_5p9 = summe_5p9 * 0.059
    data.append({'description': '', 'account': '<b>Total</b>', 'amount': "<b>CHF {:,.2f}</b>".format(summe_5p9).replace(",", "'"), 
                 'tax': "<b>CHF {:,.2f}</b>".format(tax_5p9).replace(",", "'") })
    # summe umsätze
    total_summen = summe_0p1 + summe_0p6 + summe_1p2 + summe_3p5 + summe_5p9
    total_steuern = tax_0p1 + tax_0p6 + tax_1p2 + tax_3p5 + tax_5p9
    data.append({'description': '<b>Total Umsätze MWST-pflichtig</b>', 'account': '<b>(Ziffer 299)</b>', 'amount': "<b>CHF {:,.2f}</b>".format(total_summen).replace(",", "'"),
                 'tax': "<b>CHF {:,.2f}</b>".format(total_steuern).replace(",", "'") })
    if total_summen > 0:
        avg_pps = (100 * total_steuern) / total_summen
    else:
        avg_pps = 0
    data.append({'description': 'Durchschnitts-PPS', 'account': '', 'amount': '', 'tax': "{:,.2f} %".format(avg_pps) })
    data.append({'description': '', 'account': '', 'amount': '', 'tax': ''})
    # excluded revenue
    # data.append({'description': 'Ausgenommene Umsätze', 'account': '', 'amount': '', 'tax': ''})
    # excluded = 0.0
    # # 6810
    # sql_query = """SELECT 1.0 * IFNULL(SUM(`credit` - `debit`), 0) AS `amount` 
                   # FROM `tabGL Entry` 
                   # WHERE `posting_date` >= "{from_date}" 
                         # AND `posting_date` <= "{to_date}" 
                         # AND `account` LIKE "6810%MP";""".format(from_date=from_date, to_date=to_date)
    # betrag = frappe.db.sql(sql_query, as_dict=True)[0]['amount']
    # excluded += betrag
    # data.append({'description': '', 'account': '6810', 'amount': "CHF {:,.2f}".format(betrag).replace(",", "'"), 'tax': '' })
    # # 6850
    # sql_query = """SELECT 1.0 * IFNULL(SUM(`credit` - `debit`), 0) AS `amount` 
                   # FROM `tabGL Entry` 
                   # WHERE `posting_date` >= "{from_date}" 
                         # AND `posting_date` <= "{to_date}" 
                         # AND `account` LIKE "6850%MP";""".format(from_date=from_date, to_date=to_date)
    # betrag = frappe.db.sql(sql_query, as_dict=True)[0]['amount']
    # excluded += betrag
    # data.append({'description': '', 'account': '6850', 'amount': "CHF {:,.2f}".format(betrag).replace(",", "'"), 'tax': '' })
    # # subventionen 3198
    # total_subventionen = 0.0
    # sql_query = """SELECT 1.0 * IFNULL(SUM(`credit` - `debit`), 0) AS `amount` 
                   # FROM `tabGL Entry` 
                   # WHERE `posting_date` >= "{from_date}" 
                         # AND `posting_date` <= "{to_date}" 
                         # AND `account` LIKE "3198%MP";""".format(from_date=from_date, to_date=to_date)
    # subventionen = frappe.db.sql(sql_query, as_dict=True)[0]['amount']
    # total_subventionen += subventionen
    # data.append({'description': 'Subventionen (Ziffer 900)', 'account': '3198', 'amount': "<b>CHF {:,.2f}</b>".format(subventionen).replace(",", "'"), 'tax': '' })
    # # subventionen 3298
    # total_subventionen = 0.0
    # sql_query = """SELECT 1.0 * IFNULL(SUM(`credit` - `debit`), 0) AS `amount` 
                   # FROM `tabGL Entry` 
                   # WHERE `posting_date` >= "{from_date}" 
                         # AND `posting_date` <= "{to_date}" 
                         # AND `account` LIKE "3298%MP";""".format(from_date=from_date, to_date=to_date)
    # subventionen = frappe.db.sql(sql_query, as_dict=True)[0]['amount']
    # total_subventionen += subventionen
    # data.append({'description': 'Subventionen (Ziffer 900)', 'account': '3298', 'amount': "<b>CHF {:,.2f}</b>".format(subventionen).replace(",", "'"), 'tax': '' })
    # # total subventionen
    # data.append({'description': '<b>Total Subventionen</b>', 'account': '<b>(Ziffer 900)</b>', 
                 # 'amount': "<b>CHF {:,.2f}</b>".format(total_subventionen).replace(",", "'"), 'tax': '' })
                 
    # 3200, 0 Ertrag Seminare
    sql_query = """SELECT 1.077 * IFNULL(SUM(`credit` - `debit`), 0) AS `amount` 
                   FROM `tabGL Entry` 
                   WHERE `posting_date` >= "{from_date}" 
                         AND `posting_date` <= "{to_date}" 
                         AND `account` LIKE "3200%MP";""".format(from_date=from_date, to_date=to_date)
    betrag = frappe.db.sql(sql_query, as_dict=True)[0]['amount']
    summe_0p0 += betrag
    data.append({'description': 'Ertrag Seminare', 'account': '3200', 'amount': "CHF {:,.2f}".format(betrag).replace(",", "'"), 'tax': ''})
    # 3500, 0 Mitgliederbeitraege
    sql_query = """SELECT 1.000 * IFNULL(SUM(`credit` - `debit`), 0) AS `amount` 
                   FROM `tabGL Entry` 
                   WHERE `posting_date` >= "{from_date}" 
                         AND `posting_date` <= "{to_date}" 
                         AND `account` LIKE "3500%MP";""".format(from_date=from_date, to_date=to_date)
    betrag = frappe.db.sql(sql_query, as_dict=True)[0]['amount']
    summe_0p0 += betrag
    data.append({'description': 'Mitgliederbeiträge', 'account': '3500', 'amount': "CHF {:,.2f}".format(betrag).replace(",", "'"), 'tax': ''})
    # 3610, 0 restlicher Ertrag GS
    sql_query = """SELECT 1.077 * IFNULL(SUM(`credit` - `debit`), 0) AS `amount` 
                   FROM `tabGL Entry` 
                   WHERE `posting_date` >= "{from_date}" 
                         AND `posting_date` <= "{to_date}" 
                         AND `account` LIKE "3610%MP";""".format(from_date=from_date, to_date=to_date)
    betrag = frappe.db.sql(sql_query, as_dict=True)[0]['amount']
    summe_0p0 += betrag
    data.append({'description': 'restlicher Ertrag GS', 'account': '3610', 'amount': "CHF {:,.2f}".format(betrag).replace(",", "'"), 'tax': ''})
    # total MV ausgenommen (Seminare, Mitgliederbeiträge, Ertrag GS)
    data.append({'description': '<b>Total MVAus</b>', 'account': '<b>(Ziffer 230)</b>', 
                 'amount': "<b>CHF {:,.2f}</b>".format(summe_0p0).replace(",", "'"), 'tax': '' })
    # spenden, beiträge GöV
    total_spenden = 0.0
    # 3540
    sql_query = """SELECT 1.0 * IFNULL(SUM(`credit` - `debit`), 0) AS `amount` 
                   FROM `tabGL Entry` 
                   WHERE `posting_date` >= "{from_date}" 
                         AND `posting_date` <= "{to_date}" 
                         AND `account` LIKE "3540%MP";""".format(from_date=from_date, to_date=to_date)
    betrag = frappe.db.sql(sql_query, as_dict=True)[0]['amount']
    total_spenden += betrag
    data.append({'description': 'Spenden, Beiträge GöV', 'account': '3540', 'amount': "CHF {:,.2f}".format(betrag).replace(",", "'"), 'tax': ''})
    # total spenden
    data.append({'description': '<b>Total Spenden</b>', 'account': '<b>(Ziffer 910)</b>', 
                 'amount': "<b>CHF {:,.2f}</b>".format(total_spenden).replace(",", "'"), 'tax': '' })
    data.append({'description': '', 'account': '', 'amount': '', 'tax': ''})
    # total ausgenommen
    data.append({'description': '<b>Total Umsätze ausgenommen</b>', 'account': '<b>(Ziffer 230)</b>', 'amount': "<b>CHF {:,.2f}</b>".format(summe_0p0 + total_spenden).replace(",", "'"), 'tax': '' })
    # total Gesamtumsatz
    total_200 = summe_0p0 + total_spenden + total_summen
    data.append({'description': '<b>Total Umsatz</b>', 'account': '<b>(Ziffer 200)</b>', 'amount': "<b>CHF {:,.2f}</b>".format(total_200).replace(",", "'"), 'tax': ''})

    return data
