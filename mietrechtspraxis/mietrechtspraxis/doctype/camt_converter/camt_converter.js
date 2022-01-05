// Copyright (c) 2022, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('CAMT Converter', {
    refresh: function(frm) {
        // auto save
        if (frm.doc.__islocal) {
           cur_frm.save();
        }
    },
    import: function(frm) {
        frappe.call({
            method: 'mietrechtspraxis.mietrechtspraxis.doctype.camt_converter.camt_converter.read_camt054',
            args: {
                file_path: cur_frm.doc.camt_file
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
    },
    match: function(frm) {
        frappe.call({
            method: 'mietrechtspraxis.mietrechtspraxis.doctype.camt_converter.camt_converter.auto_match',
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
            method: 'mietrechtspraxis.mietrechtspraxis.doctype.camt_converter.camt_converter.submit_all',
            args: {},
            freeze: true,
            freeze_message: 'Buche Zahlungen...',
            callback: function(r) {
                if (r.message) {
                    var feedback = r.message;
                    if (feedback.anz_unsubmitted < 1) {
                        cur_frm.set_value("submitted_payments", feedback.submitted);
                        cur_frm.set_value("anz_submitted_payments", feedback.anz_submitted);
                        cur_frm.set_value("status", "Closed");
                        cur_frm.save();
                    } else {
                        cur_frm.set_value("submitted_payments", feedback.submitted);
                        cur_frm.set_value("anz_submitted_payments", feedback.anz_submitted);
                        cur_frm.set_value("unsubmitted_payments", feedback.unsubmitted);
                        cur_frm.set_value("anz_unsubmitted_payments", feedback.anz_unsubmitted);
                        cur_frm.set_value("status", "Partially Processed");
                        cur_frm.save();
                    }
                }
            }
        });
    },
    show_overpaid: function(frm) {
        frappe.call({
            method: 'mietrechtspraxis.mietrechtspraxis.doctype.camt_converter.camt_converter.get_overpaid_payments',
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
            method: 'mietrechtspraxis.mietrechtspraxis.doctype.camt_converter.camt_converter.get_unassigned_payments',
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
            method: 'mietrechtspraxis.mietrechtspraxis.doctype.camt_converter.camt_converter.generate_report',
            args: {
                'camt_record': cur_frm.doc.name
            },
            freeze: true,
            freeze_message: 'Analysiere Daten und erstelle Bericht...',
            callback: function(r) {
                if (r.message) {
                    var feedback = r.message;
                    if (feedback.status == 'ok') {
                        frappe.msgprint("Bericht erstellt");
                    } else {
                        frappe.msgprint(feedback.feedback_message);
                    }
                } else {
                    frappe.msgprint("Etwas ist schief gelaufen...");
                }
            }
        });
    }
});
