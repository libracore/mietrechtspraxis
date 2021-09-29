// Copyright (c) 2021, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('RM Log', {
    download_pdf: function(frm) {
        window.open("/assets/mietrechtspraxis/sinvs_for_print/" + cur_frm.doc.name + ".pdf", '_blank');
    },
    storno: function(frm) {
        frappe.confirm(
            'Wollen Sie die Rechnungen wirklich stornieren?',
            function(){
                frappe.show_alert({message:__("Bitte warten, die Rechnungen werden storniert."), indicator:'blue'});
                frappe.call({
                    "method": "mietrechtspraxis.mietrechtspraxis.doctype.rm_log.rm_log.sinv_storno",
                    "args": {
                        "rm_log": cur_frm.doc.name
                    },
                    "async": false,
                    "callback": function(response) {
                        cur_frm.reload_doc();
                        frappe.show_alert({message:__("Die Rechnungen wurden storniert."), indicator:'green'});
                    }
                });
            },
            function(){
                frappe.show_alert({message:__("Stornierung abgebrochen."), indicator:'green'});
            }
        )
        
        
    }
});
