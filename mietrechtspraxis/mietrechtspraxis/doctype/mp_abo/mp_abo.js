// Copyright (c) 2021, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('mp Abo', {
	refresh: function(frm) {
        // add custom buttons
        frm.add_custom_button(__("Go to Customers Search Mask"), function() {
            go_to_customers_search_mask(frm);
        });
        if (!frm.doc.__islocal) {
           frm.add_custom_button(__("User Login"), function() {
                create_user_login(frm);
            }, __("Create"));
            if (cur_frm.doc.type == 'Jahres-Abo') {
                frm.add_custom_button(__("Sales Invoice"), function() {
                    create_sales_invoice(frm);
                }, __("Create"));
            }
            frm.add_custom_button(__("Sammel PDF"), function() {
                create_sammel_pdf(frm);
            }, __("Create"));
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
        
        // set address html
        if (!frm.doc.__islocal) {
           fetch_address(frm);
        }
	},
    invoice_recipient: function(frm) {
        // set address html
        fetch_address(frm);
        
        // clear link fields
        if (!cur_frm.doc.invoice_recipient) {
            cur_frm.set_value('recipient_contact', '');
            cur_frm.set_value('recipient_address', '');
        }
    },
    recipient_contact: function(frm) {
        // set address html
        fetch_address(frm);
    },
    recipient_address: function(frm) {
        // set address html
        fetch_address(frm);
    }
});

function go_to_customers_search_mask(frm) {
    frappe.set_route("Form", "Customers Search Mask");
}

function create_user_login(frm) {
    //tbd
    frappe.msgprint("tbd");
}

function create_sales_invoice(frm) {
    frappe.call({
        "method": "mietrechtspraxis.mietrechtspraxis.doctype.mp_abo.mp_abo.create_invoice",
        "args": {
            "abo": cur_frm.doc.name
        },
        "async": false,
        "callback": function(response) {
            cur_frm.reload_doc();
            frappe.msgprint("Die Rechnung (" + response.message + ") wurde erstellt und der Rechnungstabelle hinzugefügt.");
        }
    });
}

function create_sammel_pdf(frm) {
    frappe.prompt([
        {'fieldname': 'sinv', 'fieldtype': 'Link', 'label': __("Sales Invoice"), 'reqd': 1, 'options': 'Sales Invoice'}  
    ],
    function(values){
        //tbd
        frappe.msgprint("tbd");
    },
    __('Select Invoice'),
    __('Print')
    );
}

// set address html
function fetch_address(frm) {
    if (cur_frm.doc.invoice_recipient && cur_frm.doc.recipient_contact && cur_frm.doc.recipient_address) {
        frappe.call({
            "method": "mietrechtspraxis.mietrechtspraxis.doctype.mp_abo.mp_abo.get_address_html",
            "args": {
                "customer": cur_frm.doc.invoice_recipient,
                "contact": cur_frm.doc.recipient_contact,
                "address": cur_frm.doc.recipient_address
            },
            "async": false,
            "callback": function(response) {
                var html = response.message;
                if (cur_frm.get_field("invoice_recipient_address_html").df.options != html) {
                    cur_frm.set_df_property('invoice_recipient_address_html','options', html);
                    cur_frm.refresh();
                }
            }
        });
    } else {
        if (cur_frm.get_field("invoice_recipient_address_html").df.options != '<p></p>') {
            cur_frm.set_df_property('invoice_recipient_address_html','options', '<p></p>');
            cur_frm.refresh();
        }
    }
}
