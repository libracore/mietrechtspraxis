// Copyright (c) 2022, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('CAMT Import', {
    refresh: function(frm) {
        // auto save
        if (frm.doc.__islocal) {
           cur_frm.save();
        }
        // filter account
        cur_frm.fields_dict['account'].get_query = function(doc) {
            return {
                filters: {
                    'account_type': 'Bank',
                    'company': cur_frm.doc.company
                }
            }
        }
        
        if (cur_frm.doc.status != 'Open') {
            cur_frm.set_df_property('account','read_only',1);
            cur_frm.set_df_property('company','read_only',1);
        }
    },
    import: function(frm) {
        if (cur_frm.doc.account) {
            if (cur_frm.is_dirty()) {
                frappe.msgprint("Bitte speichern Sie das Formular zuerst");
            } else {
                frappe.call({
                    method: 'mietrechtspraxis.mietrechtspraxis.doctype.camt_import.camt_import.read_camt054',
                    args: {
                        'file_path': cur_frm.doc.camt_file,
                        'account': cur_frm.doc.account
                    },
                    freeze: true,
                    freeze_message: 'Importiere Zahlungen...',
                    callback: function(r) {
                        if (r.message) {
                            var feedback = r.message;
                            if (feedback.anz > 0) {
                                cur_frm.set_value("importet_payments", feedback.records);
                                cur_frm.set_value("anz_importet_payments", feedback.anz);
                                cur_frm.set_value("status", "Imported");
                                cur_frm.save();
                            } else {
                                cur_frm.set_value("status", "Closed");
                                cur_frm.save();
                            }
                        }
                    }
                });
            }
        } else {
            frappe.msgprint("Bitte zuerst ein Bankkonto auswählen");
        }
    },
    match: function(frm) {
        frappe.call({
            method: 'mietrechtspraxis.mietrechtspraxis.doctype.camt_import.camt_import.auto_match',
            args: {},
            freeze: true,
            freeze_message: 'Matche Zahlungen...',
            callback: function(r) {
                if (r.message) {
                    var feedback = r.message;
                    if (feedback.anz > 0) {
                        cur_frm.set_value("matched_payments", feedback.payments);
                        cur_frm.set_value("anz_matched_payments", feedback.anz);
                        cur_frm.set_value("status", "Matched");
                        cur_frm.save();
                    }
                }
            }
        });
    },
    submitt_payments: function(frm) {
        frappe.call({
            method: 'mietrechtspraxis.mietrechtspraxis.doctype.camt_import.camt_import.submit_all',
            args: {
                'camt_import': cur_frm.doc.name
            },
            freeze: true,
            freeze_message: 'Buche Zahlungen...',
            callback: function(r) {
                //~ if (r.message) {
                    //~ var feedback = r.message;
                    //~ if (feedback.anz_unsubmitted < 1) {
                        //~ cur_frm.set_value("submitted_payments", feedback.submitted);
                        //~ cur_frm.set_value("anz_submitted_payments", feedback.anz_submitted);
                        //~ cur_frm.set_value("status", "Closed");
                        //~ cur_frm.save();
                    //~ } else {
                        //~ cur_frm.set_value("submitted_payments", feedback.submitted);
                        //~ cur_frm.set_value("anz_submitted_payments", feedback.anz_submitted);
                        //~ cur_frm.set_value("unsubmitted_payments", feedback.unsubmitted);
                        //~ cur_frm.set_value("anz_unsubmitted_payments", feedback.anz_unsubmitted);
                        //~ cur_frm.set_value("status", "Partially Processed");
                        //~ cur_frm.save();
                    //~ }
                //~ }
                frappe.set_route("background_jobs");
            }
        });
    },
    show_overpaid: function(frm) {
        frappe.call({
            method: 'mietrechtspraxis.mietrechtspraxis.doctype.camt_import.camt_import.get_overpaid_payments',
            args: {},
            freeze: true,
            freeze_message: 'Lade Überzahlungen...',
            callback: function(r) {
                if (r.message) {
                    var feedback = r.message;
                    if (feedback.anz > 0) {
                        frappe.route_options = {"name": ["in", feedback.overpaid_payments]}
                        frappe.set_route("List", "Payment Entry");
                    } else {
                        frappe.msgprint("Es wurden keine überzahlte Belege gefunden");
                    }
                } else {
                    frappe.msgprint("Es wurden keine überzahlte Belege gefunden");
                }
            }
        });
    },
    show_unassigned: function(frm) {
        frappe.call({
            method: 'mietrechtspraxis.mietrechtspraxis.doctype.camt_import.camt_import.get_unassigned_payments',
            args: {},
            freeze: true,
            freeze_message: 'Lade nicht zugewiesene Zahlungen...',
            callback: function(r) {
                if (r.message) {
                    var feedback = r.message;
                    if (feedback.anz > 0) {
                        frappe.route_options = {"name": ["in", feedback.unassigned_payments]}
                        frappe.set_route("List", "Payment Entry");
                    } else {
                        frappe.msgprint("Es wurden keine nicht zugewiesene Belege gefunden");
                    }
                } else {
                    frappe.msgprint("Es wurden keine nicht zugewiesene Belege gefunden");
                }
            }
        });
    },
    show_manual_match: function(frm) {
        frappe.set_route("match_payments");
    },
    close_camt_import: function(frm) {
        cur_frm.set_value("status", "Closed");
        cur_frm.save();
    },
    generate_report: function(frm) {
        frappe.call({
            method: 'mietrechtspraxis.mietrechtspraxis.doctype.camt_import.camt_import.generate_report',
            args: {
                'camt_record': cur_frm.doc.name
            },
            freeze: true,
            freeze_message: 'Analysiere Daten und erstelle Bericht...',
            callback: function(r) {
                cur_frm.reload_doc();
            }
        });
    }
});
