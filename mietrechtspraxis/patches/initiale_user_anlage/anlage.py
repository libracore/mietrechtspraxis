import frappe
from frappe import _
from mietrecht_ch.mietrecht_ch.doctype.antwort_auf_das_formular.api import __add_role_mp__, __remove_modules_to_user__

def execute():
    try:
        print("Lege User an")
        loop = 1
        contacts = frappe.db.sql("""SELECT `name`, `email_id`, `first_name`, `last_name` from `tabContact` WHERE `email_id` IS NOT NULL AND `email_id` != ''""", as_dict=True)
        total = len(contacts)
        for contact in contacts:
            print("{0} of {1}".format(loop, total))
            has_abo = frappe.db.sql("""SELECT COUNT(`name`) AS `qty` FROM `tabmp Abo Recipient` WHERE
                                    `recipient_contact` = '{0}'
                                    AND `parent` IN (
                                        SELECT `name` FROM `tabmp Abo` WHERE `status` != 'Inactive'
                                    )""".format(contact.name), as_dict=True)[0].qty
            if has_abo > 0:
                MP_ABO_ROLE = "mp_web_user_abo"
                request_data = {
                    'email': contact.email_id,
                    'billing_address': {
                        'first_name': contact.first_name,
                        'last_name': contact.last_name
                    }
                }
                if not frappe.db.exists("User", contact.email_id):
                    user = __create_base_user__(request_data)
                    __add_role_mp__(user)
                    mp_web_user = user.name
                else:
                    mp_web_user = contact.email_id
                
                update_contact = frappe.db.sql("""UPDATE `tabContact` SET `mp_web_user` = '{0}' WHERE `name` = '{1}'""".format(mp_web_user, contact.name), as_list=True)
                frappe.db.commit()
            loop += 1
        print("Done")
    except Exception as err:
        print("Patch failed")
        print(str(err))
        pass
    return

    

def __create_base_user__(request):
    email = request.get('email')
    billing_address = request.get('billing_address', {})
    first_name = billing_address.get('first_name')
    last_name = billing_address.get('last_name')

    user = frappe.get_doc({
        "doctype":"User",
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "user_type": "Website User",
        "send_welcome_email": 0
    })


    user.flags.ignore_permissions = True
    user.flags.ignore_password_policy = True
    user.block_modules = __remove_modules_to_user__(request)
    user.insert()
    return user


    