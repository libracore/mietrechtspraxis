// Copyright (c) 2021, libracore AG and contributors
// For license information, please see license.txt

cur_frm.dashboard.add_transactions([
	{
		'label': 'Mietrechtspraxis',
		'items': [
			'mp Abo'
		]
	}
]);

frappe.ui.form.on('Customer', {
	refresh: function(frm) {
        get_mp_abos(frm);
	}
});


function get_mp_abos(frm) {
    frappe.call({
        "method": "mietrechtspraxis.mietrechtspraxis.doctype.mp_abo.mp_abo.get_abo_list",
        "args": {
            "customer": cur_frm.doc.name
        },
        "async": false,
        "callback": function(response) {
            var data = response.message;
            console.log(data);
        }
    });
}
