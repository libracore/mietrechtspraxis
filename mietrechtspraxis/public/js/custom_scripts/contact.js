// Copyright (c) 2021-2024, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Contact', {
	refresh: function(frm) {
        frm.fields_dict.mp_web_user.get_query = function(doc, cdt, cdn) {
            return {
                query: "frappe.core.doctype.user.user.user_query",
                filters: {ignore_user_type: 1}
            }
        }
        frm.refresh_field("mp_web_user");

        cur_frm.fields_dict.mp_login.collapse();
	}
});