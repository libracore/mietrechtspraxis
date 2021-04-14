// Copyright (c) 2021, libracore AG and contributors
// For license information, please see license.txt
frappe.provide("erpnext.utils");

frappe.ui.form.on('Customers Search Mask', {
	refresh: function(frm) {
        // change button from "Save" to "Search"
        $('[data-label="' + __("Save") + '"]')[0].innerHTML = __('Search');
        
        // add custom button
        frm.add_custom_button(__("Clear Search Fields"), function() {
            clear_search_fields(frm);
        });
        $(cur_frm.fields_dict['search_result_html'].wrapper).html(frappe.render_template("customers_search_mask_results", cur_frm.doc.__onload));
	},
    onload: function(frm) {
        // clear all fields for fresh start
        clear_search_fields(frm);
    }
});

function clear_search_fields(frm) {
    cur_frm.set_value('firstname', '');
    cur_frm.set_value('lastname', '');
    cur_frm.set_value('email', '');
    cur_frm.set_value('phone', '');
    cur_frm.set_value('mobile', '');
    cur_frm.set_value('address_line1', '');
    cur_frm.set_value('address_line2', '');
    cur_frm.set_value('plz', '');
    cur_frm.set_value('city', '');
    cur_frm.set_value('country', '');
}
