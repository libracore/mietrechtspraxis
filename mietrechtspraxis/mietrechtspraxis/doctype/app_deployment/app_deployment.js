// Copyright (c) 2024, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('App Deployment', {
    mietrechtspraxis: function(frm) {
        cur_frm.call({
            method: "deploy_app",
            args: {app: 'mietrechtspraxis'}
        }).then((r) => {
            frappe.msgprint(r.message);
        });
    }
});
