frappe.provide('adaequare_gsp');

adaequare_gsp.gstin_info = {};

adaequare_gsp.autofill_gstin_fields = function (dia) {
	const gstin = dia.doc.gstin.toUpperCase();
	if (gstin.length != 15 || dia.doc.api_called_for == gstin) return;
	frappe.call({
		method: "adaequare_gsp.api.validate_gstin.validate_gstin",
		args: { gstin: gstin },
		callback: function (r) {
			if (!r.message) {
				frappe.msgprint('Please enter Valid GSTIN', 'Invalid GSTIN');
				return;
			}
			adaequare_gsp.get_gstin_details(dia, gstin);
		}
	});
};

adaequare_gsp.get_gstin_details = function (dia, gstin) {
	frappe.model.get_value('Adaequare Settings', {
		'name': 'Adaequare Settings'
	}, '', function (d) {
		if (!d.gstn_public_api) return;
		frappe.call({
			method: "adaequare_gsp.api.get_gstin_details.get_gstin_details",
			args: { gstin: gstin },
			callback: function (r) {
				adaequare_gsp.gstin_info = r.message;
				dia.doc.api_called_for = gstin;
				// Assign fields
				adaequare_gsp.map_gstin_details(dia);
			}
		});
	}
	);
};

adaequare_gsp.map_gstin_details = function (dia) {
	let gi = adaequare_gsp.gstin_info;
	if(!gi.pradr){
		adaequare_gsp.update_party_info(dia);
		dia.refresh();	
		return;
	}
	gi.all_address = [];
	gi.all_address.push(gi.pradr.addr);
	if(gi.adadr){
		for (let addr of gi.adadr) {
			gi.all_address.push(addr.addr);
		}
	}
	let address = adaequare_gsp.get_address(gi.all_address[0]);
	adaequare_gsp.update_party_info(dia);
	adaequare_gsp.update_address_info(dia, address);
	dia.refresh();

	const field = dia.fields_dict.pincode;
	$(field.input_area).addClass("ui-front");

	var input = field.$input.get(0);
	input.awesomplete = new Awesomplete(input, {
		minChars: 0,
		maxItems: 99,
		autoFirst: true,
		list: [],
	});
	input.field = field;

	field.$input
		.on('input', function (e) {
			var term = e.target.value;
			e.target.awesomplete.list = gi.all_address.map(a => a.pncd);
		})
		.on('focus', function (e) {
			// $(e.target).val('').trigger('input');
		})
		.on("awesomplete-open", () => {
			let modal = field.$input.parents('.modal-dialog')[0];
			if (modal) {
				$(modal).removeClass("modal-dialog-scrollable");
			}
		})
		.on("awesomplete-close", () => {
			let modal = field.$input.parents('.modal-dialog')[0];
			if (modal) {
				$(modal).addClass("modal-dialog-scrollable");
			}
		});
};

adaequare_gsp.update_party_info = function (dia) {
	dia.doc.gstin = dia.doc.gstin.toUpperCase();
	let party_name;
	if (adaequare_gsp.gstin_info.ctb == 'Proprietorship') {
		party_name = adaequare_gsp.gstin_info.tradeNam;
	} else {
		party_name = adaequare_gsp.gstin_info.lgnm;
	}
	dia.doc.customer_name = toTitleCase(party_name);
	dia.doc.supplier_name = toTitleCase(party_name);
	dia.doc.gstin_info = JSON.stringify(adaequare_gsp.gstin_info);
};

adaequare_gsp.update_address_info = function (dia, address) {
	if (dia.doc.address_line1 == address.address_line1) return;
	dia.doc.pincode = address.pincode;
	dia.doc.address_line1 = address.address_line1;
	dia.doc.address_line2 = address.address_line2;
	dia.doc.city = address.city;
	dia.doc.state = address.state;
	dia.doc.country = address.country;
};

adaequare_gsp.get_address = function (addr) {
	let address_format = ['bno', 'bnm', 'flno', 'st', 'loc', 'city'];
	let string = [];
	for (let key of address_format) {
		string.push(addr[key]);
	}
	string = string.filter(Boolean).join(', ').replace(',,', ',');
	let address = adaequare_gsp.split_address(string);
	address.city = addr.dst;
	address.state = addr.stcd;
	address.pincode = addr.pncd;
	address.country = 'India';

	return address;
};

adaequare_gsp.autofill_address = function (dia) {
	if (dia.doc.pincode.length != 6 || !adaequare_gsp.gstin_info.all_address) return;
	for (let addr of adaequare_gsp.gstin_info.all_address) {
		if (addr.pncd != dia.doc.pincode) continue;
		adaequare_gsp.update_address_info(dia, adaequare_gsp.get_address(addr));
		dia.refresh();
		break;
	}
};

adaequare_gsp.split_address = function (s) {
	let middle = Math.floor(s.length / 2);
	let before = s.lastIndexOf(',', middle);
	let after = s.indexOf(',', middle + 1);

	if (before == -1 || (after != -1 && middle - before >= after - middle)) {
		middle = after;
	} else {
		middle = before;
	}

	let address_line1 = toTitleCase(s.substr(0, middle)).trim();
	let address_line2 = toTitleCase(s.substr(middle + 1)).trim();

	return { address_line1, address_line2 };
};


adaequare_gsp.get_gstin_fields = function (dia) {
	let gstin_fields = [
		{
			label: "GSTIN",
			fieldname: "gstin",
			fieldtype: "Data",
			description: "Autofill party information by entering correct GSTIN.",
			onchange() {
				adaequare_gsp.autofill_gstin_fields(dia.dialog);
			}
		},
		{
			label: "GSTIN Info",
			fieldname: "gstin_info",
			fieldtype: "Code",
			hidden: 1
		}
	];
	return gstin_fields;
};


adaequare_gsp.get_variant_fields = function (dia) {
	let variant_fields = [{
		fieldname: "section_break1",
		fieldtype: "Section Break",
		label: __("Primary Contact Details"),
		collapsible: 0
	},
	{
		label: __("Email Id"),
		fieldname: "email_id",
		fieldtype: "Data"
	},
	{
		fieldtype: "Column Break"
	},
	{
		label: __("Mobile Number"),
		fieldname: "mobile_no",
		fieldtype: "Data"
	},
	{
		fieldname: "section_break2",
		fieldtype: "Section Break",
		label: __("Primary Address Details"),
		description: "Permanent address is auto-filled. Change Pincode if you wish to autofill other address.",
		collapsible: 0
	},
	{
		label: __("Pincode"),
		fieldname: "pincode",
		fieldtype: "Data",
		onchange: function () {
			adaequare_gsp.autofill_address(dia.dialog);
		}
	},
	{
		label: __("Address Line 1"),
		fieldname: "address_line1",
		fieldtype: "Data"
	},
	{
		label: __("Address Line 2"),
		fieldname: "address_line2",
		fieldtype: "Data"
	},
	{
		fieldtype: "Column Break"
	},
	{
		label: __("City"),
		fieldname: "city",
		fieldtype: "Data"
	},
	{
		label: __("State"),
		fieldname: "state",
		fieldtype: "Data"
	},
	{
		label: __("Country"),
		fieldname: "country",
		fieldtype: "Link",
		options: "Country"
	},
	{
		label: __("Customer POS Id"),
		fieldname: "customer_pos_id",
		fieldtype: "Data",
		hidden: 1
	}];
	return variant_fields;
};


function toTitleCase(text) {
	text = text.toLowerCase().split(' ');
	for (let i = 0; i < text.length; i++) {
		text[i] = text[i].charAt(0).toUpperCase() + text[i].slice(1);
	}
	return text.join(' ');
};