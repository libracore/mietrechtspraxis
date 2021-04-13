// Copyright (c) 2021, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('mp Abo', {
	refresh: function(frm) {
        // add custom buttons
        frm.add_custom_button(__("Go to Customers Search Mask"), function() {
            go_to_customers_search_mask(frm);
        });
        if (!frm.doc.__islocal) {
           frm.add_custom_button(__("Create User-Login"), function() {
                create_user_login(frm);
            });
        }
        
        // apply filter to links fields
        cur_frm.fields_dict['recipient_contact'].get_query = function(doc) {
          return {
            filters: {
        	  "link_doctype": "Customer",
        	  "link_name": frm.doc.invoice_recipient
            }
          }
        };
        cur_frm.fields_dict['recipient_address'].get_query = function(doc) {
          return {
            filters: {
        	  "link_doctype": "Customer",
        	  "link_name": frm.doc.invoice_recipient
            }
          }
        };
        cur_frm.fields_dict.recipient.grid.get_field('recipient_contact').get_query = function(doc, cdt, cdn) {
          var child = locals[cdt][cdn];
          return {
            filters: {
        	  "link_doctype": "Customer",
        	  "link_name": child.magazines_recipient
            }
          }
        };
        cur_frm.fields_dict.recipient.grid.get_field('recipient_address').get_query = function(doc, cdt, cdn) {
          var child = locals[cdt][cdn];
          return {
            filters: {
        	  "link_doctype": "Customer",
        	  "link_name": child.magazines_recipient
            }
          }
        };
	}
});

function go_to_customers_search_mask(frm) {
    frappe.set_route("Form", "Customers Search Mask");
}

function create_user_login(frm) {
    //tbd
    frappe.msgprint("tbd");
}
