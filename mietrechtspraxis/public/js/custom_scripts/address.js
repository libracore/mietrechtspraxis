// Copyright (c) 2021, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Address', {
	refresh: function(frm) {
        cur_frm.set_df_property('address_line1','hidden', 1);
        toggle_strasse_mandatory(frm);
	},
    postfach: function(frm) {
        toggle_strasse_mandatory(frm)
    },
    validate: function(frm) {
        copy_to_address_line1(frm);
        copy_to_address_line2(frm);
    }
});


function copy_to_address_line1(frm) {
    if (!cur_frm.doc.postfach) {
        cur_frm.set_value("address_line1", cur_frm.doc.strasse);
    } else {
        if (cur_frm.doc.strasse) {
		cur_frm.set_value("address_line1", cur_frm.doc.strasse);
	} else {
	    cur_frm.set_value("address_line1", 'Postfach');
	}
    }
}

function copy_to_address_line2(frm) {
    cur_frm.set_value("address_line2", cur_frm.doc.zusatz);
}

function toggle_strasse_mandatory(frm) {
    if (!cur_frm.doc.postfach) {
        cur_frm.set_df_property('strasse','reqd', 1);
    } else {
        cur_frm.set_df_property('strasse','reqd', 0);
    }
}
