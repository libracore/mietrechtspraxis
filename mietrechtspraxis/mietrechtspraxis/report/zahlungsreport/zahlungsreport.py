# Copyright (c) 2013, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
    data = []
    columns = [
        {"label": _("Zahlungsbeleg"), "fieldname": "payment_entry", "fieldtype": "Link", "options": "Payment Entry", "width": 150},
        {"label": _("Rechnungsbeleg"), "fieldname": "sales_invoice", "fieldtype": "Link", "options": "Sales Invoice", "width": 150},
        {"label": _("Erhaltener Betrag"), "fieldname": "paid_amount", "fieldtype": "Currency", "width": 150},
        {"label": _("Verbuchter Betrag"), "fieldname": "allocated_amount", "fieldtype": "Currency", "width": 150},
        {"label": _("Defferenz Betrag"), "fieldname": "differenz", "fieldtype": "Currency", "width": 150}
    ]
    labels = []
    payment_entries = frappe.db.sql("""SELECT `name` FROM `tabPayment Entry` WHERE `creation` >= '{date}' and `creation` <= '{to_date}' ORDER BY `docstatus` ASC""".format(date=filters.date + " 00:00:00", to_date=filters.date + " 23:59:59"), as_dict=True)
    for payment_entry in payment_entries:
        pe = frappe.get_doc("Payment Entry", payment_entry.name)
        pe_data = {
            'payment_entry': pe.name,
            'sales_invoice': "<span style='color:red;'>Nicht zugewiesen</span>",
            'paid_amount': pe.paid_amount,
            'allocated_amount': 0,
            'differenz': 0
        }
        for entry in pe.references:
            if entry.reference_doctype == 'Sales Invoice':
                pe_data['sales_invoice'] = entry.reference_name
                pe_data['allocated_amount'] = entry.allocated_amount
                sinv = frappe.get_doc("Sales Invoice", entry.reference_name)
                for item in sinv.items:
                    if item.income_account.split(" - ")[0] not in labels:
                        labels.append(item.income_account.split(" - ")[0])
                    if item.income_account.split(" - ")[0] not in pe_data:
                        pe_data[item.income_account.split(" - ")[0]] = 0
                    pe_data[item.income_account.split(" - ")[0]] += item.amount
        if pe_data['paid_amount'] != pe_data['allocated_amount']:
            pe_data['differenz'] = pe_data['paid_amount'] - pe_data['allocated_amount']
            
        data.append(pe_data)
    for label in labels:
        columns.append({"label": label, "fieldname": label, "fieldtype": "Currency", "width": 100})
        for entry in data:
            if label not in entry:
                entry[label] = 0
    return columns, data
