// Copyright (c) 2021, libracore AG and contributors
// For license information, please see license.txt

frappe.listview_settings['Arbitration Authority'] = {
    onload: function(listview) {
        listview.page.add_menu_item(__("Sammel-PDF Drucken"), function() {
            print_pdf();
            show_alert({message:__("Der Backgroudjob wurde gestartet"), indicator:'orange'});
        });
    }
};

function print_pdf() {
    frappe.call({
        "method": "mietrechtspraxis.mietrechtspraxis.doctype.arbitration_authority.arbitration_authority.get_sammel_pdf",
        "args": {}
    });
}
