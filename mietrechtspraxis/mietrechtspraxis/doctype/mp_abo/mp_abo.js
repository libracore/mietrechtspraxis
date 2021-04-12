// Copyright (c) 2021, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('mp Abo', {
	refresh: function(frm) {
        frm.add_custom_button(__("Go to Customers Search Mask"), function() {
            go_to_customers_search_mask(frm);
        });
        if (!frm.doc.__islocal) {
           frm.add_custom_button(__("Create User-Login"), function() {
                create_user_login(frm);
            });
        }
	}
});

function go_to_customers_search_mask(frm) {
    frappe.set_route("Form", "Customers Search Mask");
}

function create_user_login(frm) {
    //tbd
    frappe.msgprint("tbd");
}
