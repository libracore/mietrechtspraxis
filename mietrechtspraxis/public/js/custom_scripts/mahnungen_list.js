frappe.listview_settings['Payment Reminder'] = {
    onload: function(listview) {
        listview.page.add_menu_item( __("Create Payment Reminders"), function() {
            frappe.prompt(
                [
                    {'fieldname': 'company', 'fieldtype': 'Link', 'options': 'Company', 'label': __('Company'), 'reqd': 1, 'default': frappe.defaults.get_user_default('company')}
                ],
                function(values){
                    create_payment_reminders(values);
                },
                __("Create Payment Reminders"),
                __("Create")
            );
        });
        
        listview.page.add_menu_item( __("Alle Entwurfs-Mahnungen buchen"), function() {
            frappe.confirm(
                'Wollen Sie alle Entwurfs-Mahnungen buchen?',
                function(){
                    // on yes
                    submit_mahnungen([], 1)
                },
                function(){
                    // on no
                }
            )
        });
        
        listview.page.add_menu_item( __("Alle Entwurfs-Mahnungen löschen"), function() {
            frappe.confirm(
                'Wollen Sie alle Entwurfs-Mahnungen löschen?',
                function(){
                    // on yes
                    delete_mahnungen()
                },
                function(){
                    // on no
                }
            )
        });
        
        listview.page.add_menu_item( __("Erstellung Sammel-PDF"), function() {
            frappe.confirm(
                'Wollen Sie ein Mahnungs Sammel-PDF erstellen?',
                function(){
                    // on yes
                    frappe.prompt([
                        {'fieldname': 'date', 'fieldtype': 'Date', 'label': 'Buchungsdatum', 'reqd': 1}  
                    ],
                    function(values){
                        print_mahnungen(values.date);
                    },
                    'Auswahl Mahnungen',
                    'Drucken'
                    )
                },
                function(){
                    // on no
                }
            )
        });
        
        $("[data-label='Submit']").parent().unbind();
        $("[data-label='Submit']").parent().click(function(){
            frappe.confirm('Möchten Sie die Markierten Mahnungen buchen?',
            () => {
                var selected_mahnungen = cur_list.get_checked_items();
                submit_mahnungen(selected_mahnungen, 0);
            }, () => {
                // No
            })
            
        });
    }
}

function print_mahnungen(date) {
    frappe.dom.freeze('Bitte warten, drucke Mahnungen...');
    frappe.call({
        'method': "mietrechtspraxis.mietrechtspraxis.mahnungen.mahnungen.print_mahnungen",
        'args': {
            'date': date
        },
        'callback': function(r) {
            var jobname = r.message;
            if (jobname != 'keine') {
                let mahnung_refresher = setInterval(mahnung_refresher_handler, 3000, jobname);
                function mahnung_refresher_handler(jobname) {
                    frappe.call({
                    'method': "mietrechtspraxis.mietrechtspraxis.mahnungen.mahnungen.is_mahnungs_job_running",
                        'args': {
                            'jobname': jobname
                        },
                        'callback': function(res) {
                            if (res.message == 'refresh') {
                                clearInterval(mahnung_refresher);
                                frappe.dom.unfreeze();
                                cur_list.refresh();
                            }
                        }
                    });
                }
            } else {
                frappe.dom.unfreeze();
                frappe.msgprint("Es gibt keine Mahnungen zum drucken.");
            }
        }
    });
}

function create_payment_reminders(values) {
    frappe.call({
        'method': "erpnextswiss.erpnextswiss.doctype.payment_reminder.payment_reminder.create_payment_reminders",
        'args': {
            'company': values.company
        },
        'callback': function(response) {
            frappe.show_alert( __("Payment Reminders created") );
        }
    });
}

function submit_mahnungen(mahnungen, alle) {
    frappe.dom.freeze('Bitte warten, buche Mahnungen...');
    frappe.call({
        'method': "mietrechtspraxis.mietrechtspraxis.mahnungen.mahnungen.bulk_submit",
        'args': {
            'mahnungen': mahnungen,
            'alle': alle
        },
        'callback': function(r) {
            var jobname = r.message;
            if (jobname != 'keine') {
                jobname = "Buche Mahnungen " + jobname;
                let mahnung_refresher = setInterval(mahnung_refresher_handler, 3000, jobname);
                function mahnung_refresher_handler(jobname) {
                    frappe.call({
                    'method': "mietrechtspraxis.mietrechtspraxis.mahnungen.mahnungen.is_mahnungs_job_running",
                        'args': {
                            'jobname': jobname
                        },
                        'callback': function(res) {
                            if (res.message == 'refresh') {
                                clearInterval(mahnung_refresher);
                                frappe.dom.unfreeze();
                                cur_list.refresh();
                            }
                        }
                    });
                }
            } else {
                frappe.dom.unfreeze();
                frappe.msgprint("Es gibt keine Mahnungen zum verbuchen.");
            }
        }
    });
}

function delete_mahnungen() {
    frappe.dom.freeze('Bitte warten, lösche Entwurfs-Mahnungen...');
    frappe.call({
        'method': "mietrechtspraxis.mietrechtspraxis.mahnungen.mahnungen.bulk_delete",
        'callback': function(r) {
            var jobname = r.message;
            if (jobname != 'keine') {
                jobname = "Lösche Entwurfs-Mahnungen " + jobname;
                let mahnung_refresher = setInterval(mahnung_refresher_handler, 3000, jobname);
                function mahnung_refresher_handler(jobname) {
                    frappe.call({
                    'method': "mietrechtspraxis.mietrechtspraxis.mahnungen.mahnungen.is_mahnungs_job_running",
                        'args': {
                            'jobname': jobname
                        },
                        'callback': function(res) {
                            if (res.message == 'refresh') {
                                clearInterval(mahnung_refresher);
                                frappe.dom.unfreeze();
                                cur_list.refresh();
                            }
                        }
                    });
                }
            } else {
                frappe.dom.unfreeze();
                frappe.msgprint("Es gibt keine Mahnungen zum löschen.");
            }
        }
    });
}
