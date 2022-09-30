// Copyright (c) 2022, libracore and contributors
// For license information, please see license.txt

frappe.listview_settings['Werbeversand'] = {
    add_fields: ["status"],
    get_indicator: function(doc) {
        if (doc.status == "Neu") {
            return [__("Neu"), "orange", "status,=," + "Neu"]
        }
        
        if (doc.status == "In Arbeit") {
            return [__("In Arbeit"), "blue", "status,=," + "In Arbeit"]
        }
        
        if (doc.status == "Abgeschlossen") {
            return [__("Abgeschlossen"), "green", "status,=," + "Abgeschlossen"]
        }
        
        if (doc.status == "Fehlgeschlagen") {
            return [__("Fehlgeschlagen"), "red", "status,=," + "Fehlgeschlagen"]
        }
    }
};
