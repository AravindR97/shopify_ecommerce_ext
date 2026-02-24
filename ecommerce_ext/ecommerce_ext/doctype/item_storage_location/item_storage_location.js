// Copyright (c) 2026, Aravind R and contributors
// For license information, please see license.txt

frappe.ui.form.on("Item Storage Location", {
    setup: function(frm) {
        frm.set_query("warehouse", function() {
            return {
                filters: {
                    is_group: 0
                }
            };
        });
    }
});
