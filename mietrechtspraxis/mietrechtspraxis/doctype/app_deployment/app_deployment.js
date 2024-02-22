// Copyright (c) 2024, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('App Deployment', {
    mietrechtspraxis: function(frm) {
        if (window.location.hostname.includes("mp-test")) {
            cur_frm.call({
                method: "deploy_app",
                args: {app: 'mietrechtspraxis'}
            }).then((r) => {
                frappe.msgprint(r.message);
            });
        } else {
            frappe.msgprint("Diese Funktion ist nur im Testsystem verfügbar.");
        }
    },
    mietrecht_ch: function(frm) {
        if (window.location.hostname.includes("mp-test")) {
            cur_frm.call({
                method: "deploy_app",
                args: {app: 'mietrecht_ch'}
            }).then((r) => {
                frappe.msgprint(r.message);
            });
        } else {
            frappe.msgprint("Diese Funktion ist nur im Testsystem verfügbar.");
        }
    }
});
