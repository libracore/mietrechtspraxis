frappe.listview_settings['Sales Order'] = {
    add_fields: ["base_grand_total", "customer_name", "currency", "delivery_date",
        "per_delivered", "per_billed", "status", "order_type", "name"],
    get_indicator: function (doc) {
        if (doc.status === "Closed") {
            return [__("Closed"), "green", "status,=,Closed"];

        } else if (doc.status === "On Hold") {
            // on hold
            return [__("On Hold"), "orange", "status,=,On Hold"];
        } else if (doc.order_type !== "Maintenance"
            && flt(doc.per_delivered, 6) < 100 && frappe.datetime.get_diff(doc.delivery_date) < 0) {
            // not delivered & overdue
            return [__("Overdue"), "red", "per_delivered,<,100|delivery_date,<,Today|status,!=,Closed"];

        } else if (doc.order_type !== "Maintenance"
            && flt(doc.per_delivered, 6) < 100 && doc.status !== "Closed") {
            // not delivered

            if (flt(doc.grand_total) === 0) {
                // not delivered (zero-amount order)

                return [__("To Deliver"), "orange",
                    "per_delivered,<,100|grand_total,=,0|status,!=,Closed"];
            } else if (flt(doc.per_billed, 6) < 100) {
                // not delivered & not billed

                return [__("To Deliver and Bill"), "orange",
                    "per_delivered,<,100|per_billed,<,100|status,!=,Closed"];
            } else {
                // not billed

                return [__("To Deliver"), "orange",
                    "per_delivered,<,100|per_billed,=,100|status,!=,Closed"];
            }

        } else if ((flt(doc.per_delivered, 6) === 100)
            && flt(doc.grand_total) !== 0 && flt(doc.per_billed, 6) < 100 && doc.status !== "Closed") {
            // to bill

            return [__("To Bill"), "orange", "per_delivered,=,100|per_billed,<,100|status,!=,Closed"];

        } else if ((flt(doc.per_delivered, 6) === 100)
            && (flt(doc.grand_total) === 0 || flt(doc.per_billed, 6) == 100) && doc.status !== "Closed") {
            return [__("Completed"), "green", "per_delivered,=,100|per_billed,=,100|status,!=,Closed"];

        }else if (doc.order_type === "Maintenance" && flt(doc.per_delivered, 6) < 100 && doc.status !== "Closed"){

            if(flt(doc.per_billed, 6) < 100 ){
                return [__("To Deliver and Bill"), "orange", "per_delivered,=,100|per_billed,<,100|status,!=,Closed"];
            }else if(flt(doc.per_billed, 6) === 100){
                return [__("To Deliver"), "orange", "per_delivered,=,100|per_billed,=,100|status,!=,Closed"];
            }
        }

    },
    onload: function(listview) {
        var method = "erpnext.selling.doctype.sales_order.sales_order.close_or_unclose_sales_orders";
        listview.page.add_menu_item(__("Close"), function() {
            listview.call_for_selected_items(method, {"status": "Closed"});
        });

        listview.page.add_menu_item(__("Re-open"), function() {
            listview.call_for_selected_items(method, {"status": "Submitted"});
        });
        
        
        listview.page.add_menu_item( __("Bestellungen verrechnen"), function() {
            frappe.confirm(
                'Wollen Sie Aufträge anhand Tags verrechnen?',
                function(){
                    // on yes
                    get_tags();
                },
                function(){
                    // on no
                }
            )
        });
    }
};

function create_invoice(tag, posting_date) {
    console.log(tag);
    frappe.dom.freeze('Bitte warten, erstelle Rechnungen...');
    frappe.call({
        'method': "mietrechtspraxis.mietrechtspraxis.utils.so_to_sinv.create_invoices",
        'args': {
            'tag': tag,
            'posting_date': posting_date
        },
        'callback': function(r) {
            var jobname = r.message;
            console.log(jobname)
            if (jobname != 'keine') {
                let prozess_refresher = setInterval(prozess_refresh_handler, 3000, jobname);
                function prozess_refresh_handler(jobname) {
                    frappe.call({
                    'method': "mietrechtspraxis.mietrechtspraxis.mahnungen.mahnungen.is_mahnungs_job_running",
                        'args': {
                            'jobname': jobname
                        },
                        'callback': function(res) {
                            if (res.message == 'refresh') {
                                clearInterval(prozess_refresher);
                                frappe.dom.unfreeze();
                                cur_list.refresh();
                            }
                        }
                    });
                }
            } else {
                frappe.dom.unfreeze();
                frappe.msgprint("Es gibt keine Aufträge zum verrechnen.");
            }
        }
    });
}

function get_tags(){
    frappe.call({
        method:"frappe.desk.tags.get_tags",
        args:{
            doctype: 'Sales Order',
            txt: '',
            cat_tags: '[]'
        },
        callback: function(r) {
            var tags = r.message.join("\n");
            frappe.prompt([
                {'fieldname': 'tag', 'fieldtype': 'Select', 'label': 'Tag', 'reqd': 1, 'options': tags},
                {'fieldname': 'posting_date', 'fieldtype': 'Date', 'label': 'Buchungsdatum der Rechnung', 'reqd': 1, 'default': frappe.datetime.get_today()}
            ],
            function(values){
                create_invoice(values.tag, values.posting_date);
            },
            'Auswahl Aufträge',
            'Rechnungen erstellen'
            )
        }
    });
}
