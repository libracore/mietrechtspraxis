frappe.pages['invoice_and_print'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Rechnungslauf und Massendruck',
		single_column: true
	});

	frappe.invoice_and_print.make(page);
	
	// add the application reference
	frappe.breadcrumbs.add("mietrechtspraxis");
    setTimeout(function(){
        frappe.invoice_and_print.get_show_data();
    }, 500);
}

frappe.invoice_and_print = {
	start: 0,
	make: function(page) {
		var me = frappe.invoice_and_print;
		me.page = page;
		me.body = $('<div></div>').appendTo(me.page.main);
		var data = "";
		$(frappe.render_template('invoice_and_print', data)).appendTo(me.body);
        $("#show_data").on("click", function() {
            frappe.invoice_and_print.get_show_data();
        });
        $("#create_data").on("click", function() {
            frappe.invoice_and_print.create_data();
        });
	},
	get_show_data: function() {
        var sel_type = 'all';
        frappe.call({
            "method": "mietrechtspraxis.mietrechtspraxis.page.invoice_and_print.invoice_and_print.get_show_data",
            "args": {
                "sel_type": sel_type
            },
            "async": false,
            "callback": function(response) {
                var data = response.message;
                frappe.invoice_and_print.show_data(sel_type, data);
            }
        });
	},
    show_data: function(sel_type, data) {
        $("#chart_area").empty();
        $('<div id="chart"></div>').appendTo($("#chart_area"));
        frappe.invoice_and_print.show_donut_all(data);
        
    },
    show_donut_all: function(_data) {
        const data = {
            labels: ["Gratis-Abo", "Jahres-Abo", "Probe-Abo"
            ],
            datasets: [
                {
                    name: "Gratis-Abo", type: "donut",
                    values: [_data.gratis_qty, 0, 0]
                },
                {
                    name: "Jahres-Abo", type: "donut",
                    values: [0, _data.jahres_qty, 0]
                },
                {
                    name: "Probe-Abo", type: "donut",
                    values: [0, 0, _data.probe_qty]
                }
            ]
        }

        const chart = new frappe.Chart("#chart", {  // or a DOM element,
                                                    // new Chart() in case of ES6 module with above usage
            title: __("Magazine Typen Übersicht"),
            data: data,
            type: 'donut', // or 'axis-mixed', 'bar', 'line', 'scatter', 'pie', 'percentage'
            height: 250,
            colors: ['#7cd6fd', '#743ee2', '#ffa3ef']
        })
    },
    create_data: function() {
        var date = $("#date").val();
        var limit = String(parseInt($("#limit").val()));
        if (date) {
            frappe.confirm(
                'Wollen Sie ' + limit + ' Rechnungen mit dem Datum ' + frappe.datetime.obj_to_user(date) + " erstellen?",
                function(){
                    frappe.prompt([
                        {'fieldname': 'year', 'fieldtype': 'Int', 'label': 'Invoice Year', 'reqd': 1, 'default': new Date().getFullYear()}  
                    ],
                    function(values){
                        frappe.show_alert({message:__("Bitte warten, die Rechnungen werden erstellt/versendet."), indicator:'blue'});
                        $("#invoice_area").empty();
                        $("<div>Bitte warten...</div>").appendTo($("#invoice_area"));
                        frappe.call({
                            "method": "mietrechtspraxis.mietrechtspraxis.page.invoice_and_print.invoice_and_print.create_invoices",
                            "args": {
                                "date": date,
                                "year": values.year,
                                'limit': limit
                            },
                            "async": false,
                            "callback": function(response) {
                                var data = response.message;
                                $("#invoice_area").empty();
                                $(frappe.render_template('invoice_table', {'abos': data.abos, 'qty_one': data.qty_one, 'qty_multi': data.qty_multi, 'rm_log': data.rm_log})).appendTo($("#invoice_area"));
                                frappe.show_alert({message:__("Die Rechnungen wurden erstellt/versendet."), indicator:'green'});
                            }
                        });
                    },
                    'Erstellung Rechnungen',
                    'Erstellen'
                    )
                },
                function(){
                    show_alert('Rechnungserstellung abgebrochen');
                }
            )
        } else {
            frappe.throw(__("Bittte wählen Sie zuerst ein Datum aus"));
        }
    }
}
