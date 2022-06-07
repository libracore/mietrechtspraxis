# -*- coding: utf-8 -*-
# Copyright (c) 2018-2022, libracore (https://www.libracore.com) and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from datetime import datetime
import json
from frappe.utils.data import today, now
from frappe.utils.background_jobs import enqueue
from frappe import _
import frappe, os
from PyPDF2 import PdfFileWriter


@frappe.whitelist()
def bulk_submit(mahnungen, alle):
    mahnungen = json.loads(mahnungen)
    if len(mahnungen) < 1:
        if int(alle) == 1:
            mahnungen = frappe.get_list('Payment Reminder', filters={'docstatus': 0}, fields=['name'])
            if len(mahnungen) < 1:
                return 'keine'
        else:
            return 'keine'
    
    args = {
        'mahnungen': mahnungen
    }
    enqueue("mietrechtspraxis.mietrechtspraxis.mahnungen.mahnungen.bulk_submit_bgj", queue='long', job_name='Buche Mahnungen {0}'.format(mahnungen[0]["name"]), timeout=5000, **args)
    return mahnungen[0]["name"]
    
def bulk_submit_bgj(mahnungen):
    for mahnung in mahnungen:
        mahnung = frappe.get_doc("Payment Reminder", mahnung["name"])
        mahnung.update_reminder_levels()
        mahnung.submit()
    return

@frappe.whitelist()
def bulk_delete():
    mahnungen = frappe.get_list('Payment Reminder', filters={'docstatus': 0}, fields=['name'])
    if len(mahnungen) < 1:
        return 'keine'
    
    args = {
        'mahnungen': mahnungen
    }
    enqueue("mietrechtspraxis.mietrechtspraxis.mahnungen.mahnungen.bulk_delete_bgj", queue='long', job_name='Lösche Entwurfs-Mahnungen {0}'.format(mahnungen[0]["name"]), timeout=5000, **args)
    return mahnungen[0]["name"]
    
def bulk_delete_bgj(mahnungen):
    for mahnung in mahnungen:
        mahnung = frappe.get_doc("Payment Reminder", mahnung["name"])
        mahnung.delete()
    return

@frappe.whitelist()
def is_mahnungs_job_running(jobname):
    from frappe.utils.background_jobs import get_jobs
    running = get_info(jobname)
    return running

def get_info(jobname):
    from rq import Queue, Worker
    from frappe.utils.background_jobs import get_redis_conn
    from frappe.utils import format_datetime, cint, convert_utc_to_user_timezone
    colors = {
        'queued': 'orange',
        'failed': 'red',
        'started': 'blue',
        'finished': 'green'
    }
    conn = get_redis_conn()
    queues = Queue.all(conn)
    workers = Worker.all(conn)
    jobs = []
    show_failed=False

    def add_job(j, name):
        if j.kwargs.get('site')==frappe.local.site:
            jobs.append({
                'job_name': j.kwargs.get('kwargs', {}).get('playbook_method') \
                    or str(j.kwargs.get('job_name')),
                'status': j.status, 'queue': name,
                'creation': format_datetime(convert_utc_to_user_timezone(j.created_at)),
                'color': colors[j.status]
            })
            if j.exc_info:
                jobs[-1]['exc_info'] = j.exc_info

    for w in workers:
        j = w.get_current_job()
        if j:
            add_job(j, w.name)

    for q in queues:
        if q.name != 'failed':
            for j in q.get_jobs(): add_job(j, q.name)

    if cint(show_failed):
        for q in queues:
            if q.name == 'failed':
                for j in q.get_jobs()[:10]: add_job(j, q.name)
    
    found_job = 'refresh'
    for job in jobs:
        if job['job_name'] == jobname:
            found_job = True

    return found_job

@frappe.whitelist()
def print_mahnungen(date):
    mahnungen = frappe.get_list('Payment Reminder', filters={'docstatus': 1, 'date': date}, fields=['name'])
    if len(mahnungen) < 1:
        return 'keine'
    
    args = {
        'date': date
    }
    enqueue("mietrechtspraxis.mietrechtspraxis.mahnungen.mahnungen.blk_print_mahnungen", queue='long', job_name='Erstelle Mahnungs Sammel-PDF', timeout=5000, **args)
    return 'Erstelle Mahnungs Sammel-PDF'

def blk_print_mahnungen(date):
    save_counter = 1
    
    rm_log = frappe.get_doc({
        "doctype": "RM Log",
        'start': now(),
        'status': 'Job gestartet',
        'typ': 'Mahnungen'
    })
    rm_log.insert()
    frappe.db.commit()
    
    bind_source = "/assets/mietrechtspraxis/sinvs_for_print/{date}.pdf".format(date=rm_log.name)
    physical_path = "/home/frappe/frappe-bench/sites" + bind_source
    dest=str(physical_path)
    
    output = PdfFileWriter()
    
    mahnungen = frappe.db.sql("""SELECT `name` FROM `tabPayment Reminder` WHERE `date` = '{date}' AND `docstatus` = 1""".format(date=date), as_dict=True)
    
    for mahnung in mahnungen:
        # create rm_log:
        try:
            row = rm_log.append('mahnungen', {})
            row.mahnung = mahnung.name
            if save_counter == 250:
                rm_log.save(ignore_permissions=True)
                frappe.db.commit()
                save_counter = 1
            else:
                save_counter += 1
        except:
            frappe.log_error(frappe.get_traceback(), 'create rm_log failed: {ref_dok}'.format(ref_dok=mahnung.name))
        
        try:
            output = frappe.get_print("Payment Reminder", mahnung.name, 'Mahnung', as_pdf = True, output = output, no_letterhead = 1, ignore_zugferd=True)
        except:
            frappe.log_error(frappe.get_traceback(), 'print_pdf failed: {ref_dok}'.format(ref_dok=mahnung.name))
    
    rm_log.save(ignore_permissions=True)
    frappe.db.commit()
    
    try:
        if isinstance(dest, str): # when dest is a file path
            destdir = os.path.dirname(dest)
            if destdir != '' and not os.path.isdir(destdir):
                os.makedirs(destdir)
            with open(dest, "wb") as w:
                output.write(w)
        else: # when dest is io.IOBase
            output.write(dest)
    except:
        frappe.log_error(frappe.get_traceback(), 'save_pdf failed: {ref_dok}'.format(ref_dok=rm_log.name))
    
    rm_log.ende = now()
    rm_log.status = 'PDF erstellt'
    rm_log.save(ignore_permissions=True)
    frappe.db.commit()
