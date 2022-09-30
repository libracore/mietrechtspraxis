// Copyright (c) 2022, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Werbeversand', {
    on_submit: function(frm) {
        frappe.show_alert({message:"Der Backgroundjob wurde gestartet, verfolgen Sie den Fortschritt <a href='/desk#background_jobs'>hier</a>", indicator:'orange'}, 5);
    }
});
