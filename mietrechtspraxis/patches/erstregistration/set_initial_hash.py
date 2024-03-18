import frappe
from frappe import _

def execute():
    try:
        print("Set initial Hash")
        frappe.reload_doc("Contacts", "doctype", "Contact")
        loop = 1
        contacts = frappe.db.sql("""SELECT `name` from `tabContact` WHERE `email_id` IS NULL or `email_id` = ''""", as_dict=True)
        total = len(contacts)
        for contact in contacts:
            print("{0} of {1}".format(loop, total))
            regist_hash = frappe.generate_hash(length=10)
            set_hash = frappe.db.sql("""UPDATE `tabContact` SET `erstregistrations_hash` = '{0}' WHERE `name` = '{1}'""".format(regist_hash, contact.name.replace("'", "''")), as_list=True)
            loop += 1
        print("Done")
    except Exception as err:
        print("Patch failed")
        print(str(err))
        pass
    return