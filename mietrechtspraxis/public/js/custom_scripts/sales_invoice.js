// Copyright (c) 2021, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Sales Invoice', {
    validate: function(frm) {
        get_qrr_reference(frm);
    }
});


function get_qrr_reference(frm) {
    frappe.call({
        "method": "mietrechtspraxis.mietrechtspraxis.utils.qrr_reference.get_qrr_reference",
        "args": {
            "reference_raw": "00 00000 00000 00000 " + cur_frm.doc.name.replace("MP-R-", "") + " 0000"
        },
        "async": false,
        "callback": function(response) {
            var qrr_reference = response.message;
            cur_frm.set_value('esr_reference', qrr_reference);
        }
    });
}
