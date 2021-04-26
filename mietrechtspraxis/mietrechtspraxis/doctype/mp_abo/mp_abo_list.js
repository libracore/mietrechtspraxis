// Copyright (c) 2021, libracore AG and contributors
// For license information, please see license.txt

frappe.listview_settings['mp Abo'] = {
	get_indicator: function(doc) {
		var status_color = {
			"Active": "green",
			"Actively terminated": "orange",
			"Inactive": "red"

		};
		return [__(doc.status), status_color[doc.status], "status,=,"+doc.status];
	}
};
