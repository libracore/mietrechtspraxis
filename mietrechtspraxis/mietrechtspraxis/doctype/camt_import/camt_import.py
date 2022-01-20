# -*- coding: utf-8 -*-
# Copyright (c) 2022, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from bs4 import BeautifulSoup
import hashlib
import json
from datetime import datetime
import operator
import re
import six
from frappe.utils.background_jobs import enqueue
from decimal import Decimal, ROUND_HALF_UP

class CAMTImport(Document):
    pass

@frappe.whitelist()
def read_camt054(file_path, account):
    # get uploaded camt file
    physical_path = "/home/frappe/frappe-bench/sites/{0}{1}".format(frappe.local.site_path.replace("./", ""), file_path)
    with open(physical_path, 'r') as f:
        content = f.read()
        
    soup = BeautifulSoup(content, 'lxml')
    
    # general information
    try:
        iban = soup.document.bktocstmrdbtcdtntfctn.ntfctn.acct.id.iban.get_text()
    except:
        # node not found, probably wrong format
        frappe.throw("Das CAMT File konnte nicht gelesen werden.")
        
    # transactions
    new_payment_entries = read_camt_transactions(soup.find_all('ntry'), account, False)
    message = _("Successfully imported {0} payments.".format(len(new_payment_entries)))
    frappe.msgprint(message)
    return { "records": str(new_payment_entries), "anz": len(new_payment_entries) }

def read_camt_transactions(transaction_entries, account, auto_submit=False):
    new_payment_entries = []
    for entry in transaction_entries:
        entry_soup = BeautifulSoup(six.text_type(entry), 'lxml')
        date = entry_soup.bookgdt.dt.get_text()
        transactions = entry_soup.find_all('txdtls')
        # fetch entry amount as fallback
        entry_amount = float(entry_soup.amt.get_text())
        entry_currency = entry_soup.amt['ccy']
        for transaction in transactions:
            transaction_soup = BeautifulSoup(six.text_type(transaction), 'lxml')
            try:
                unique_reference = transaction_soup.refs.acctsvcrref.get_text()
                amount = float(transaction_soup.amt.get_text())
                currency = transaction_soup.amt['ccy']
                try:
                    party_soup = BeautifulSoup(six.text_type(transaction_soup.dbtr), 'lxml')
                    customer_name = party_soup.nm.get_text()
                    try:
                        street = party_soup.strtnm.get_text()
                        try:
                            street_number = party_soup.bldgnb.get_text()
                            address_line = "{0} {1}".format(street, street_number)
                        except:
                            address_line = street
                            
                    except:
                        address_line = ""
                    try:
                        plz = party_soup.pstcd.get_text()
                    except:
                        plz = ""
                    try:
                        town = party_soup.twnnm.get_text()
                    except:
                        town = ""
                    try:
                        country = party_soup.ctry.get_text()
                    except:
                        party_iban = ""
                    customer_address = "{0}, {1}, {2}".format(address_line, plz, town)
                    try:
                        customer_iban = "{0}".format(transaction_soup.dbtracct.id.iban.get_text())
                    except:
                        customer_iban = ""
                except:
                    # CRDT: use RltdPties:Dbtr
                    #party_soup = BeautifulSoup(str(transaction_soup.txdtls.rltdpties.dbtr)) 
                    try:
                        customer_iban = transaction_soup.dbtracct.id.iban.get_text()
                    except Exception as e:
                        customer_iban = ""
                        frappe.log_error("Error parsing customer info: {0} ({1})".format(e, six.text_type(transaction_soup.dbtr)))
                        # key related parties not found / no customer info
                        customer_name = "Postschalter"
                        customer_address = ""
                try:
                    charges = float(transaction_soup.chrgs.ttlchrgsandtaxamt.get_text())
                except:
                    charges = 0.0
                # paid or received: (DBIT: paid, CRDT: received)
                credit_debit = transaction_soup.cdtdbtind.get_text()
                try:
                    # try to find ESR reference
                    transaction_reference = transaction_soup.rmtinf.strd.cdtrrefinf.ref.get_text()
                except:
                    try:
                        # try to find a user-defined reference (e.g. SINV.)
                        transaction_reference = transaction_soup.rmtinf.ustrd.get_text()
                    except:
                        try:
                            # try to find an end-to-end ID
                            transaction_reference = transaction_soup.refs.endtoendid.get_text()
                        except:
                            transaction_reference = unique_reference
                if credit_debit == "CRDT":
                    inserted_payment_entry = create_payment_entry(date=date, to_account=account, received_amount=amount, 
                        transaction_id=unique_reference, remarks="ESR/QRR: {0}, {1}, {2}, IBAN: {3}".format(
                        transaction_reference, customer_name, customer_address, customer_iban), 
                        auto_submit=False)
                    if inserted_payment_entry:
                        new_payment_entries.append(inserted_payment_entry.name)
            except Exception as e:
                frappe.msgprint("Parsing error: {0}:{1}".format(six.text_type(transaction), e))
                pass
    return new_payment_entries

# create a payment entry
def create_payment_entry(date, to_account, received_amount, transaction_id, remarks, auto_submit=False):
    # get default customer
    default_customer = get_default_customer()
    if not frappe.db.exists('Payment Entry', {'reference_no': transaction_id}):
        # create new payment entry
        new_payment_entry = frappe.get_doc({'doctype': 'Payment Entry'})
        new_payment_entry.payment_type = "Receive"
        new_payment_entry.party_type = "Customer";
        new_payment_entry.party = default_customer
        # date is in DD.MM.YYYY
        new_payment_entry.posting_date = date
        new_payment_entry.paid_to = to_account
        new_payment_entry.received_amount = received_amount
        new_payment_entry.paid_amount = received_amount
        new_payment_entry.reference_no = transaction_id
        new_payment_entry.reference_date = date
        new_payment_entry.remarks = remarks
        inserted_payment_entry = new_payment_entry.insert()
        if auto_submit:
            new_payment_entry.submit()
        frappe.db.commit()
        return inserted_payment_entry
    else:
        return None
    
def get_default_customer():
    default_customer = frappe.get_value("ERPNextSwiss Settings", "ERPNextSwiss Settings", "default_customer")
    if not default_customer:
        default_customer = "Guest"
    return default_customer

@frappe.whitelist()
def auto_match():
    # prepare array of matched payments
    matched_payments = []
    # read all new payments
    new_payments = get_unallocated_payment_entries()['unallocated_payment_entries']
    # loop through all unpaid sales invoices
    pending_sales_invoices = get_open_sales_invoices()['unpaid_sales_invoices']
    for unpaid_sales_invoice in pending_sales_invoices:
        # only check Sales Invoice records with an ESR reference
        if unpaid_sales_invoice['esr_reference']:
            for payment in new_payments:
                if unpaid_sales_invoice['esr_reference'].replace(' ', '') in payment['remarks']:
                    matched_payment_entry = match(unpaid_sales_invoice['name'], payment['name'])['payment_entry']
                    matched_payments.append(matched_payment_entry)
    frappe.msgprint("{0} Zahlungen wurden zugeordnet".format(len(matched_payments)))
    return { 'anz': len(matched_payments), 'payments': str(matched_payments) }

def get_unallocated_payment_entries():
    # get unallocated payment entries
    sql_query = ("""SELECT `name`, `party`, `paid_amount`, `posting_date`, `remarks` 
                FROM `tabPayment Entry` 
                WHERE `docstatus` = 0  
                  AND `payment_type` = 'Receive' 
                ORDER BY `posting_date` ASC""")
    unallocated_payment_entries = frappe.db.sql(sql_query, as_dict=True)
    return {'unallocated_payment_entries': unallocated_payment_entries }

def get_open_sales_invoices():
    # get unpaid sales invoices
    sql_query = ("""SELECT `name`, `customer`, `base_grand_total`, `outstanding_amount`, `due_date`, `esr_reference` 
                FROM `tabSales Invoice` 
                WHERE `docstatus` = 1 AND `outstanding_amount` > 0 
                ORDER BY `due_date` ASC""")
    unpaid_sales_invoices = frappe.db.sql(sql_query, as_dict=True)
    return {'unpaid_sales_invoices': unpaid_sales_invoices }

def match(sales_invoice, payment_entry):
    # get the customer
    customer = frappe.get_value("Sales Invoice", sales_invoice, "customer")
    if customer:
        payment_entry_record = frappe.get_doc("Payment Entry", payment_entry)
        if payment_entry:
            # assign the actual customer
            payment_entry_record.party = customer            
            payment_entry_record.save()
            
            # now, add the reference to the sales invoice
            create_reference(payment_entry, sales_invoice)
            
            # and finally submit the payment entry (direct submit will void the reference :-( )
            #payment_entry_record.submit()
            
            return { 'payment_entry': payment_entry_record.name }
        else:
            return { 'error': "Payment entry not found" }
    else:
        return { 'error': "Customer not found" }

# creates the reference record in a payment entry
def create_reference(payment_entry, sales_invoice):
    # create a new payment entry reference
    reference_entry = frappe.get_doc({"doctype": "Payment Entry Reference"})
    reference_entry.parent = payment_entry
    reference_entry.parentfield = "references"
    reference_entry.parenttype = "Payment Entry"
    reference_entry.reference_doctype = "Sales Invoice"
    reference_entry.reference_name = sales_invoice
    reference_entry.total_amount = frappe.get_value("Sales Invoice", sales_invoice, "base_grand_total")
    reference_entry.outstanding_amount = frappe.get_value("Sales Invoice", sales_invoice, "outstanding_amount")
    paid_amount = frappe.get_value("Payment Entry", payment_entry, "paid_amount")
    if paid_amount > reference_entry.outstanding_amount:
        reference_entry.allocated_amount = reference_entry.outstanding_amount
    else:
        reference_entry.allocated_amount = paid_amount
    reference_entry.insert();
    # update unallocated amount
    payment_record = frappe.get_doc("Payment Entry", payment_entry)
    payment_record.unallocated_amount -= reference_entry.allocated_amount
    payment_record.save()
    return

@frappe.whitelist()
def submit_all(camt_import):
    args = {
        'camt_import': camt_import
    }
    enqueue("mietrechtspraxis.mietrechtspraxis.doctype.camt_import.camt_import._submit_all", queue='long', job_name='Buche Zahlungen (CAMT Import)', timeout=5000, **args)

def _submit_all(camt_import):
    # prepare array of (un-)submitted payments
    submitted_payments = []
    unsubmitted_payments = []
    # read all new payments
    new_payments = get_unallocated_payment_entries()['unallocated_payment_entries']
    # loop through all matched payments and submit them
    for payment_entry in new_payments:
        payment_entry_record = frappe.get_doc("Payment Entry", payment_entry)
        if not payment_entry_record.unallocated_amount > 0:
            payment_entry_record.submit()
            submitted_payments.append(payment_entry_record.name)
        else:
            unsubmitted_payments.append(payment_entry_record.name)
    
    frappe.msgprint("{0} Zahlungen verbucht, {1} Zahlungen <b>nicht</b> verbucht".format(len(submitted_payments), len(unsubmitted_payments)))
    
    camt_import = frappe.get_doc("CAMT Import", camt_import)
    if len(unsubmitted_payments) < 1:
        camt_import.submitted_payments = str(submitted_payments)
        camt_import.anz_submitted_payments = len(submitted_payments)
        camt_import.status = 'Closed'
    else:
        camt_import.submitted_payments = str(submitted_payments)
        camt_import.anz_submitted_payments = len(submitted_payments)
        camt_import.unsubmitted_payments = str(unsubmitted_payments)
        camt_import.anz_unsubmitted_payments = len(unsubmitted_payments)
        camt_import.status = 'Partially Processed'
    camt_import.save()
    return True
    #return { 'anz_submitted': len(submitted_payments), 'submitted': str(submitted_payments), 'anz_unsubmitted': len(unsubmitted_payments), 'unsubmitted': str(unsubmitted_payments) }

@frappe.whitelist()
def get_overpaid_payments():
    # get overpaid payment entries
    sql_query = ("""SELECT `name`
                FROM `tabPayment Entry` 
                WHERE `docstatus` = 0  
                  AND `payment_type` = 'Receive'
                  AND `unallocated_amount` > 0
                  AND `party` != '{party}'
                ORDER BY `posting_date` ASC""".format(party=get_default_customer()))
    _overpaid_payments = frappe.db.sql(sql_query, as_dict=True)
    overpaid_payments = []
    for o_pay in _overpaid_payments:
        overpaid_payments.append(o_pay.name)
    return {'overpaid_payments': overpaid_payments, 'anz': len(overpaid_payments) }

@frappe.whitelist()
def get_unassigned_payments():
    # get unassigned payment entries
    sql_query = ("""SELECT `name`
                FROM `tabPayment Entry` 
                WHERE `docstatus` = 0  
                  AND `payment_type` = 'Receive'
                  AND `unallocated_amount` > 0
                  AND `party` = '{party}'
                ORDER BY `posting_date` ASC""".format(party=get_default_customer()))
    _unassigned_payments = frappe.db.sql(sql_query, as_dict=True)
    unassigned_payments = []
    for u_pay in _unassigned_payments:
        unassigned_payments.append(u_pay.name)
    return {'unassigned_payments': unassigned_payments, 'anz': len(unassigned_payments) }

@frappe.whitelist()
def generate_report(camt_record):
    data = 'Filename:\n'
    camt_record = frappe.get_doc("CAMT Import", camt_record)
    data += str(camt_record.camt_file).split("/")[3] + "\n\n"
    verbuchte_zahlungen = ''
    anzahl_zahlungen = 0
    totalbetrag = 0.00
    einzahlungstaxen = 0.00
    erp_next_zahlung = 0.00
    konten = []
    konten_betraege = {}
    physical_path = "/home/frappe/frappe-bench/sites/{0}{1}".format(frappe.local.site_path.replace("./", ""), camt_record.camt_file)
    with open(physical_path, 'r') as f:
        content = f.read()
        
    soup = BeautifulSoup(content, 'lxml')
    filedatum = soup.document.bktocstmrdbtcdtntfctn.grphdr.credttm.get_text().split("T")[0]
    transaction_entries = soup.find_all('ntry')
    for entry in transaction_entries:
        entry_soup = BeautifulSoup(six.text_type(entry), 'lxml')
        date = entry_soup.bookgdt.dt.get_text()
        transactions = entry_soup.find_all('txdtls')
        # fetch entry amount as fallback
        entry_amount = float(entry_soup.amt.get_text())
        verbuchte_zahlungen += 'Datum: ' + frappe.utils.get_datetime(date).strftime('%d.%m.%Y') + ", Betrag: " + "{:,.2f}".format(proper_round(entry_amount, Decimal('0.01'))).replace(",", "'") + "\n"
        for transaction in transactions:
            transaction_soup = BeautifulSoup(six.text_type(transaction), 'lxml')
            unique_reference = transaction_soup.refs.acctsvcrref.get_text()
            totalbetrag += float(transaction_soup.amt.get_text())
            anzahl_zahlungen += 1
            try:
                einzahlungstaxen += float(transaction_soup.chrgs.ttlchrgsandtaxamt.get_text())
            except:
                einzahlungstaxen += 0.0
            _pe = frappe.db.sql("""SELECT `name` FROM `tabPayment Entry` WHERE `reference_no` = '{unique_reference}'""".format(unique_reference=unique_reference), as_dict=True)
            try:
                pe = frappe.get_doc("Payment Entry", _pe[0].name)
                erp_next_zahlung += float(pe.paid_amount)
                for _sinv in pe.references:
                    sinv = frappe.get_doc("Sales Invoice", _sinv.reference_name)
                    for item in sinv.items:
                        if item.income_account not in konten:
                            konten.append(item.income_account)
                            konten_betraege[item.income_account] = 0.00
                        konten_betraege[item.income_account] += float(item.amount)
            except:
                pass
    
    str_konten_betraege = ''
    for konto in konten:
        str_konten_betraege += konto + ": "
        str_konten_betraege += "{:,.2f}".format(proper_round(konten_betraege[konto], Decimal('0.01'))).replace(",", "'") + "\n"
    
    camt_record.zahlungsreport = data + \
        "Filedatum: " + frappe.utils.get_datetime(filedatum).strftime('%d.%m.%Y') + "\n\n" + \
        "Einzahlungstaxen: " + "{:,.2f}".format(proper_round(einzahlungstaxen, Decimal('0.01'))).replace(",", "'") + "\n\n" + \
        "Anzahl Zahlungen: " + str(anzahl_zahlungen) + "\n\n" + \
        "Totalbetrag: " + "{:,.2f}".format(proper_round(totalbetrag, Decimal('0.01'))).replace(",", "'") + "\n\n" + \
        "Verbuchte Zahlungen gem. CAMT File:\n" + str(verbuchte_zahlungen) + "\n\n" + \
        "In ERPNext verbuchte Zahlungen:\n" + "{:,.2f}".format(proper_round(erp_next_zahlung, Decimal('0.01'))).replace(",", "'") + "\n\n" + \
        "In ERPNext verbuchte Beträge zu Konten:\n" + str(str_konten_betraege)
    camt_record.save()
    return
    
def proper_round(number, decimals):
    return float(Decimal(number).quantize(decimals, ROUND_HALF_UP))
