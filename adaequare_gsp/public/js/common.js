frappe.provide('adaequare_gsp');

adaequare_gsp.gstin_info = {};

adaequare_gsp.autofill_gstin_fields = function (dia) {
  let gstin = dia.is_dialog ? dia.doc.gstin_custom : dia.doc.gstin;
  if (!gstin || gstin.length != 15 || dia.doc.api_called_for == gstin) return;
  gstin = gstin.toUpperCase();
  frappe.call({
    method: 'adaequare_gsp.api.get_gstin_details.validate_gstin',
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
  frappe.model.get_value(
    'Adaequare Settings',
    {
      name: 'Adaequare Settings'
    },
    '',
    function (d) {
      if (d.gstn_public_api == 0) return;
      frappe.call({
        method: 'adaequare_gsp.api.get_gstin_details.get_gstin_details',
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
  if (!gi.pradr) {
    adaequare_gsp.update_party_info(dia);
    dia.refresh();
    return;
  }
  gi.all_address = [];
  gi.all_address.push(gi.pradr.addr);
  if (gi.adadr) {
    for (let addr of gi.adadr) {
      gi.all_address.push(addr.addr);
    }
  }
  let address = adaequare_gsp.get_address(gi.all_address[0]);
  adaequare_gsp.update_party_info(dia);
  adaequare_gsp.update_address_info(dia, address);
  dia.refresh();

  adaequare_gsp.pincode_awesomplete(dia);
};

adaequare_gsp.autofill_address = function (dia, pincode) {
  if (!pincode) {
    pincode = dia.is_dialog ? dia.doc.pincode_custom : dia.doc.pincode;
  }
  if (pincode.length != 6 || !adaequare_gsp.gstin_info.all_address) return;
  for (let addr of adaequare_gsp.gstin_info.all_address) {
    if (addr.pncd != pincode) continue;
    adaequare_gsp.update_address_info(dia, adaequare_gsp.get_address(addr));
    dia.refresh();
    break;
  }
};

adaequare_gsp.update_party_info = function (dia) {
  let gstin;
  let gst_category;
  if (dia.doc.gstin_custom) {
    gstin = dia.doc.gstin_custom.toUpperCase();
  }
  if (dia.doc.gstin) {
    gstin = dia.doc.gstin.toUpperCase();
  }
  dia.doc.gstin_custom = dia.doc.gstin = gstin;
  let party_name;
  if (adaequare_gsp.gstin_info.ctb == 'Proprietorship') {
    party_name = adaequare_gsp.gstin_info.tradeNam;
  } else {
    party_name = adaequare_gsp.gstin_info.lgnm;
  }
  dia.doc.customer_name = toTitleCase(party_name);
  dia.doc.supplier_name = toTitleCase(party_name);
  dia.doc.gstin_info = JSON.stringify(adaequare_gsp.gstin_info);
  if (gstin == 'URP' || gstin == 'NA') {
    gst_category = adaequare_gsp.gst_category_map.URP;
  } else {
    gst_category = adaequare_gsp.gst_category_map[adaequare_gsp.gstin_info.dty];
  }
  dia.doc.gst_category = gst_category;
};

adaequare_gsp.update_address_info = function (dia, address) {
  if (dia.doc.address_line1 == address.address_line1) return;
  dia.doc.pincode_custom = dia.doc.pincode = address.pincode;
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

adaequare_gsp.pincode_awesomplete = function (dia) {
  const field = dia.is_dialog
    ? dia.fields_dict.pincode_custom
    : dia.fields_dict.pincode;
  $(field.input_area).addClass('ui-front');

  var input = field.$input.get(0);
  input.awesomplete = new Awesomplete(input, {
    minChars: 0,
    maxItems: 99,
    autoFirst: true,
    list: []
  });
  input.field = field;

  field.$input
    .on('input', function (e) {
      e.target.awesomplete.list = adaequare_gsp.gstin_info.all_address.map(
        (a) => a.pncd
      );
    })
    .on('awesomplete-open', () => {
      let modal = field.$input.parents('.modal-dialog')[0];
      if (modal) {
        $(modal).removeClass('modal-dialog-scrollable');
      }
    })
    .on('awesomplete-select', (e) => {
      const pincode = e.originalEvent.text.value;
      adaequare_gsp.autofill_address(dia, pincode);
    })
    .on('awesomplete-close', () => {
      let modal = field.$input.parents('.modal-dialog')[0];
      if (modal) {
        $(modal).addClass('modal-dialog-scrollable');
      }
    });
};

adaequare_gsp.get_party_details = function (dia, customer, supplier) {
  if (customer) {
    dia.doc.supplier = '';
    dia.doc.address_title = dia.doc.customer;
    dia.refresh();
  }
  if (supplier) {
    dia.doc.customer = '';
    dia.doc.address_title = dia.doc.supplier;
    dia.refresh();
  }
  frappe.call({
    method: 'adaequare_gsp.api.get_gstin_details.get_party_gstin',
    args: {
      customer: dia.doc.customer,
      supplier: dia.doc.supplier
    },
    callback: function (r) {
      dia.fields_dict.gstin_custom.set_value(r.message);
      dia.fields_dict.gstin_custom.refresh();
    }
  });
};

adaequare_gsp.get_party_fields = function (dia) {
  let party_fields = [
    {
      fieldname: 'customer',
      fieldtype: 'Link',
      label: 'Customer',
      options: 'Customer',
      default: !cur_frm
        ? ''
        : cur_frm.doc.doctype == 'Customer'
        ? cur_frm.doc.name
        : cur_frm.doc.customer
        ? cur_frm.doc.customer
        : '',
      onchange: function () {
        adaequare_gsp.get_party_details(dia.dialog, true, false);
      }
    },
    {
      fieldtype: 'Column Break'
    },
    {
      fieldname: 'supplier',
      fieldtype: 'Link',
      label: 'Supplier',
      options: 'Supplier',
      default: !cur_frm
        ? ''
        : cur_frm.doc.doctype == 'Supplier'
        ? cur_frm.doc.name
        : cur_frm.doc.supplier
        ? cur_frm.doc.supplier
        : '',
      onchange: function (e) {
        adaequare_gsp.get_party_details(dia.dialog, false, true);
      }
    },
    {
      fieldtype: 'Section Break'
    }
  ];
  party_fields = party_fields.concat(adaequare_gsp.get_gstin_fields(dia));
  return party_fields;
};
adaequare_gsp.get_gstin_fields = function (dia) {
  let gstin_fields = [
    {
      label: 'GSTIN',
      fieldname: 'gstin_custom',
      fieldtype: 'Data',
      description: 'Autofill party information by entering correct GSTIN.',
      onchange() {
        adaequare_gsp.autofill_gstin_fields(dia.dialog);
      }
    },
    {
      label: 'GSTIN Info',
      fieldname: 'gstin_info',
      fieldtype: 'Code',
      hidden: 1
    }
  ];
  return gstin_fields;
};

adaequare_gsp.get_variant_fields = function (dia) {
  let variant_fields = [
    {
      fieldname: 'section_break1',
      fieldtype: 'Section Break',
      label: __('Primary Contact Details'),
      collapsible: 0
    },
    {
      label: __('Email Id'),
      fieldname: 'email_id',
      fieldtype: 'Data'
    },
    {
      fieldtype: 'Column Break'
    },
    {
      label: __('Mobile Number'),
      fieldname: 'mobile_no',
      fieldtype: 'Data'
    }
  ];
  variant_fields = variant_fields.concat(adaequare_gsp.get_address_fields(dia));
  return variant_fields;
};

adaequare_gsp.get_address_fields = function (dia) {
  let address_fields = [
    {
      fieldname: 'section_break2',
      fieldtype: 'Section Break',
      label: __('Primary Address Details'),
      description:
        'Permanent address is auto-filled. Change Pincode if you wish to autofill other address.',
      collapsible: 0
    },
    {
      label: __('Pincode'),
      fieldname: 'pincode_custom',
      fieldtype: 'Data',
      onchange: function () {
        adaequare_gsp.autofill_address(dia.dialog);
      }
    },
    {
      label: __('Address Line 1'),
      fieldname: 'address_line1',
      fieldtype: 'Data'
    },
    {
      label: __('Address Line 2'),
      fieldname: 'address_line2',
      fieldtype: 'Data'
    },
    {
      fieldtype: 'Column Break'
    },
    {
      label: __('City'),
      fieldname: 'city',
      fieldtype: 'Data'
    },
    {
      label: __('State'),
      fieldname: 'state',
      fieldtype: 'Data'
    },
    {
      label: __('Country'),
      fieldname: 'country',
      fieldtype: 'Link',
      options: 'Country'
    },
    {
      label: __('Customer POS Id'),
      fieldname: 'customer_pos_id',
      fieldtype: 'Data',
      hidden: 1
    }
  ];
  return address_fields;
};

function toTitleCase(text) {
  text = text.toLowerCase().split(' ');
  for (let i = 0; i < text.length; i++) {
    text[i] = text[i].charAt(0).toUpperCase() + text[i].slice(1);
  }
  return text.join(' ');
}

adaequare_gsp.gst_category_map = {
  Regular: 'Registered Regular',
  Composition: 'Registered Composition',
  'SEZ Unit': 'SEZ',
  'Non Resident Online Services Provider': 'UIN Holders',
  URP: 'Unregistered'
};
