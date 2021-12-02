// Copyright (c) 2021, libracore AG and contributors
// For license information, please see license.txt

frappe.listview_settings['Arbitration Authority'] = {
    onload: function(listview) {
        listview.page.add_menu_item(__("Sammel-PDF Drucken"), function() {
            frappe.prompt([
                {'fieldname': 'no_letterhead', 'fieldtype': 'Check', 'label': 'Ohne Briefkopf', 'default': 0}  
            ],
            function(values){
                print_pdf(values['no_letterhead']);
                show_alert({message:__("Der Backgroudjob wurde gestartet"), indicator:'orange'});
            },
            'Briefkopf',
            'Sammel-PDF erstellen'
            );
        });
    }
};

function print_pdf(no_letterhead) {
    frappe.call({
        "method": "mietrechtspraxis.mietrechtspraxis.doctype.arbitration_authority.arbitration_authority.get_sammel_pdf",
        "args": {'no_letterhead': no_letterhead}
    });
}
