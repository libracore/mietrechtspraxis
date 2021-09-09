// Copyright (c) 2021, libracore AG and contributors
// For license information, please see license.txt
frappe.provide("erpnext.utils");

frappe.ui.form.on('Customers Search Mask', {
	refresh: function(frm) {
        // set intro
        cur_frm.set_intro(__('You can use two wildcards:<br>- The percent sign (%) represents zero, one, or multiple characters<br>- The underscore sign (_) represents one, single character'));
        
        // change button from "Save" to "Search"
        change_button_to_Search();
        
        // add custom button
        frm.add_custom_button(__("Clear Search Fields"), function() {
            clear_search_fields(frm);
        });
        frm.add_custom_button(__("Create new Customer"), function() {
            create_new_customer(frm);
        });
	},
    onload: function(frm) {
        // clear all fields for fresh start
        clear_search_fields(frm);
        // change button from "Save" to "Search"
        setTimeout(function(){ change_button_to_Search(); }, 1000);
    },
    validate: function(frm) {
        frappe.call({
            "method": "mietrechtspraxis.mietrechtspraxis.doctype.customers_search_mask.customers_search_mask.search_results",
            "args": {
                "self": cur_frm.doc
            },
            "async": false,
            "callback": function(response) {
                var data = response.message;
                console.log(data);
                $(frm.fields_dict["search_result_html"].wrapper).html(data);
            }
        });
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
    cur_frm.set_value('is_company', 0);
    cur_frm.set_value('company', '');
    cur_frm.set_value('postfach', 0);
    cur_frm.set_value('postfach_nummer', '');
    cur_frm.set_value('abo_nummer', '');
    remove_mandatory(frm);
}

function create_new_customer(frm) {
    var firstname = '!';
    if (cur_frm.doc.firstname) {
        firstname = cur_frm.doc.firstname;
    }
    var lastname = '!';
    if (cur_frm.doc.lastname) {
        lastname = cur_frm.doc.lastname;
    }
    var email = '!';
    if (cur_frm.doc.email) {
        email = cur_frm.doc.email;
    }
    var phone = '!';
    if (cur_frm.doc.phone) {
        phone = cur_frm.doc.phone;
    }
    var mobile = '!';
    if (cur_frm.doc.mobile) {
        mobile = cur_frm.doc.mobile;
    }
    var address_line1 = '!';
    if (cur_frm.doc.address_line1) {
        address_line1 = cur_frm.doc.address_line1;
    }
    var address_line2 = '!';
    if (cur_frm.doc.address_line2) {
        address_line2 = cur_frm.doc.address_line2;
    }
    var plz = '!';
    if (cur_frm.doc.plz) {
        plz = cur_frm.doc.plz;
    }
    var city = '!';
    if (cur_frm.doc.city) {
        city = cur_frm.doc.city;
    }
    var country = '!';
    if (cur_frm.doc.country) {
        country = cur_frm.doc.country;
    }
    
    var customer_type = 'Individual';
    var customer_name = ''
    if (cur_frm.doc.is_company == 1) {
        customer_type = 'Company';
        if (cur_frm.doc.company) {
            customer_name = cur_frm.doc.company;
        } else {
            customer_name = '!';
        }
    }
    
    // check mandatory
    if ((firstname != '!' || lastname != '!') && (address_line1 != '!' && plz != '!' && city != '!' && customer_name != '!')) {
        remove_mandatory(frm);
        frappe.call({
            "method": "mietrechtspraxis.mietrechtspraxis.doctype.customers_search_mask.customers_search_mask.create_customer",
            "args": {
                "firstname": firstname,
                "lastname": lastname,
                "email": email,
                "phone": phone,
                "mobile": mobile,
                "address_line1": address_line1,
                "address_line2": address_line2,
                "plz": plz,
                "city": city,
                "country": country,
                "customer_type": customer_type,
                "customer_name": customer_name
            },
            "async": false,
            "callback": function(response) {
                var customer = response.message;
                cur_frm.set_value('firstname', firstname.replace("!", ""));
                cur_frm.set_value('lastname', lastname.replace("!", ""));
                cur_frm.set_value('email', email.replace("!", ""));
                cur_frm.set_value('phone', phone.replace("!", ""));
                cur_frm.set_value('mobile', mobile.replace("!", ""));
                cur_frm.set_value('address_line1', address_line1.replace("!", ""));
                cur_frm.set_value('address_line2', address_line2.replace("!", ""));
                cur_frm.set_value('plz', plz.replace("!", ""));
                cur_frm.set_value('city', city.replace("!", ""));
                cur_frm.set_value('country', country.replace("!", ""));
                cur_frm.set_value('company', customer_name.replace("!", ""));
                cur_frm.save();
            }
        });
    } else {
        set_mandatory(frm);
        cur_frm.save();
    }
}

function set_mandatory(frm) {
    cur_frm.set_df_property('firstname','reqd','1');
    cur_frm.set_df_property('lastname','reqd','1');
    cur_frm.set_df_property('address_line1','reqd','1');
    cur_frm.set_df_property('plz','reqd','1');
    cur_frm.set_df_property('city','reqd','1');
    if (cur_frm.doc.is_company == 1) {
        cur_frm.set_df_property('company','reqd','1');
    }
}

function remove_mandatory(frm) {
    cur_frm.set_df_property('firstname','reqd', 0);
    cur_frm.set_df_property('lastname','reqd', 0);
    cur_frm.set_df_property('address_line1','reqd', 0);
    cur_frm.set_df_property('plz','reqd', 0);
    cur_frm.set_df_property('city','reqd', 0);
    cur_frm.set_df_property('company','reqd', 0);
}

function change_button_to_Search() {
    for (var i = 0; i<$('[data-label="Save"]').length; i++) {
        if ($('[data-label="Save"]')[i]) {
            $('[data-label="Save"]')[i].innerHTML = __('Search');
        }
    }
    for (var y = 0; y<$('[data-label="Speichern"]').length; y++) {
        if ($('[data-label="Speichern"]')[y]) {
            $('[data-label="Speichern"]')[y].innerHTML = __('Search');
        }
    }
}
