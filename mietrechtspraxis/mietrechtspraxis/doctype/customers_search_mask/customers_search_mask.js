// Copyright (c) 2021, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Customers Search Mask', {
	refresh: function(frm) {
        $('[data-label="' + __("Save") + '"]')[0].innerHTML = __('Search');
	}
});
