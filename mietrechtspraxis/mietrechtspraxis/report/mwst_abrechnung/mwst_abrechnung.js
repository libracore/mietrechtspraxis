// Copyright (c) 2021, libracore AG and contributors
// For license information, please see license.txt
/* eslint-disable */


frappe.query_reports["MWST Abrechnung"] = {
	"filters": [
		{
			fieldname:"from_date",
			label: __("From date"),
			fieldtype: "Date",
			default: new Date(new Date().getFullYear(), 0, 1),
			reqd: 1,
		},
        {
			fieldname:"to_date",
			label: __("To date"),
			fieldtype: "Date",
			default: new Date(),
			reqd: 1,
		}
	]
};

