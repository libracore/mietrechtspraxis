// Copyright (c) 2021, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('mp Abo', {
	setup: function(frm) {
        frm.set_indicator_formatter('sales_invoice',
			function(doc) { 
                return (doc.status != 'Paid') ? "red" : "green" ;
            }
        );
    },
    refresh: function(frm) {
        // add custom buttons
        frm.add_custom_button(__("Go to Customers Search Mask"), function() {
            go_to_customers_search_mask(frm);
        });
        if (!frm.doc.__islocal) {
           if (!cur_frm.doc.user_login_createt) {
               frm.add_custom_button(__("User Login"), function() {
                    if (!cur_frm.is_dirty()) {
                        create_user_login(frm);
                    } else {
                        frappe.msgprint("Bitte speichern Sie den Datensatz zuerst.");
                    }
                }, __("Create"));
            }
            if (cur_frm.doc.type == 'Jahres-Abo') {
                if (!exist_initial_sinv(frm)) {
                    frm.add_custom_button(__("Initial Rechnung"), function() {
                        if (!cur_frm.is_dirty()) {
                            create_sales_invoice(frm);
                        } else {
                            frappe.msgprint("Bitte speichern Sie den Datensatz zuerst.");
                        }
                    }, __("Create"));
                }
            }
            if (exist_initial_sinv(frm)||cur_frm.doc.type != 'Jahres-Abo') {
                if (cur_frm.doc.user_login_createt) {
                    frm.add_custom_button(__("Sammel PDF"), function() {
                        if (!cur_frm.is_dirty()) {
                            create_sammel_pdf(frm);
                        } else {
                            frappe.msgprint("Bitte speichern Sie den Datensatz zuerst.");
                        }
                    }, __("Create"));
                }
            }
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
    frappe.call({
        "method": "mietrechtspraxis.mietrechtspraxis.doctype.mp_abo.mp_abo.create_user_login",
        "args": {
            "abo": cur_frm.doc.name
        },
        "async": false,
        "callback": function(response) {
            cur_frm.reload_doc();
            frappe.msgprint("Das/Die User Logins(s) wurde(n) erstellt.");
        }
    });
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
    if (cur_frm.doc.type != 'Jahres-Abo') {
        // tbd
    } else {
        frappe.prompt([
            {'fieldname': 'sinv', 'fieldtype': 'Link', 'label': __("Sales Invoice"), 'reqd': 1, 'options': 'Sales Invoice', 'default': get_initial_sinv(frm), get_query: function(doc) {
                  return {
                    filters: {
                        "name": ["in", get_linked_sinvs(frm)]
                    }
                  }
                }
            }  
        ],
        function(values){
            //tbd
            frappe.msgprint("tbd");
        },
        __('Select Invoice'),
        __('Create')
        );
    }
}

// get linked sinvs as array
function get_linked_sinvs(frm) {
    var data = [];
    var sinv_tbl = cur_frm.doc.sales_invoices;
    for (var i=0; i<sinv_tbl.length; i++) {
        data.push(sinv_tbl[i].sales_invoice);
    }
    return data
}

// check linked sinvs for initial sinv
function exist_initial_sinv(frm) {
    var check = false;
    var sinv_tbl = cur_frm.doc.sales_invoices;
    for (var i=0; i<sinv_tbl.length; i++) {
        var d = new Date(cur_frm.doc.start_date);
        var year = d.getFullYear();
        if (sinv_tbl[i].year == year) {
            check = true;
        }
    }
    return check
}

// get initial sinv
function get_initial_sinv(frm) {
    var sinv = '';
    var sinv_tbl = cur_frm.doc.sales_invoices;
    for (var i=0; i<sinv_tbl.length; i++) {
        var d = new Date(cur_frm.doc.start_date);
        var year = d.getFullYear();
        if (sinv_tbl[i].year == year) {
            sinv = sinv_tbl[i].sales_invoice;
        }
    }
    return sinv
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
                $(frm.fields_dict["invoice_recipient_address_html"].wrapper).html(html);
            }
        });
    } else {
        if (cur_frm.get_field("invoice_recipient_address_html").df.options != '<p></p>') {
            cur_frm.set_df_property('invoice_recipient_address_html','options', '<p></p>');
            cur_frm.refresh();
        }
    }
}
