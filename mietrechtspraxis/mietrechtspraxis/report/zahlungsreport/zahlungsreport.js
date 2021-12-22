// Copyright (c) 2016, libracore AG and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Zahlungsreport"] = {
    "filters": [
        {
            fieldname:"date",
            label: __("Erstellungs Datum"),
            fieldtype: "Date",
            default: new Date(),
            reqd: 1
        }
    ]
};
