// Copyright (c) 2021, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Arbitration Authority', {
		mapping_liste: function(frm) {
			frappe.route_options = {"schlichtungsstelle": frm.doc.id};
            frappe.set_route("List", "Mapping Schlichtungsstellen", "List");
		},
		refresh: function(frm) {
		var aa_id = frm.doc.id
		frm.add_custom_button(__("PLZ/Ort Liste"),  function() {
			frappe.route_options = {"schlichtungsstelle": aa_id}
            frappe.set_route("List", "Mapping Schlichtungsstellen", "List");
		});
		load_html_aa_mapping(frm);
	}
});

function load_html_aa_mapping(frm) {
    frappe.call({
        method: "mietrechtspraxis.mietrechtspraxis.doctype.arbitration_authority.arbitration_authority.get_schlichtungsbehoerden_mapping",
        args:{
                'aa_id': cur_frm.doc.name
        },
        callback: function(r)
        {
            cur_frm.set_df_property('aa_mapping_html','options', r.message);
            add_jump_icons_event_handler(frm);
            add_trash_icons_event_handler(frm);
            add_route_to_list_view_event_handler(frm);
        }
    });
}