// Copyright (c) 2021, libracore AG and contributors
// For license information, please see license.txt

frappe.listview_settings['RM Log'] = {
    add_fields: ["status"],
    get_indicator: function(doc) {
        var colors = {
            "Job gestartet": "blue",
            "PDF erstellt": "green",
            "Rechnungen storniert": "red"
        };
        return [doc.status, colors[doc.status], "status,=," + doc.status];
    }
};
