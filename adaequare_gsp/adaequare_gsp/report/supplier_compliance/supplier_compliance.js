// Copyright (c) 2016, Resilient Tech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports['Supplier Compliance'] = {
  filters: [
    {
      fieldname: 'fiscal_year',
      label: __('Fiscal Year'),
      fieldtype: 'Link',
      options: 'Fiscal Year',
      async on_change(report) {
        const { fiscal_year } = report.get_values();
        if (!fiscal_year) return;

        await set_return_period(
          report,
          report.report_settings.fiscal_years_map[fiscal_year]
        );
        report.refresh();
      }
    },
    {
      fieldname: 'return_period',
      label: __('Return Period'),
      fieldtype: 'Date Range',
      on_change(report) {
        const { fiscal_year, return_period } = report.get_values();
        const date_range = report.report_settings.fiscal_years_map[fiscal_year];

        if (
          date_range &&
          (return_period[0] < date_range[0] || return_period[1] > date_range[1])
        ) {
          frappe.throw(
            __(
              `Return Period should be withing the selected fiscal year ${fiscal_year.bold()}`
            )
          );
        }
      }
    },
    {
      fieldname: 'return_type',
      label: __('Return Type'),
      fieldtype: 'Select',
      default: 'GSTR1',
      options: ['GSTR1', 'GSTR3B', 'GSTR9', 'GSTR9A', 'GSTR9C'],
      reqd: true
    },
    {
      fieldname: 'only_from_purchase_invoice',
      label: __('Exclude Parties without Purchases'),
      fieldtype: 'Check',
      default: 1
    }
  ],

  async onload(report) {
    this.add_custom_button(report);
    await this.set_global_variables();
    this.set_defaults(report);
  },

  add_custom_button(report) {
    report.page.add_button(__('Fetch Latest Returns'), function (e) {
      if (!report.data) return frappe.throw('Please select filters first');

      fetch_latest_returns(report);
    });
  },
  async set_global_variables() {
    this.fiscal_years = await frappe.db.get_list('Fiscal Year', {
      fields: ['name', 'year_start_date', 'year_end_date'],
      as_list: true
    });

    this.fiscal_years_map = {};
    for (const fiscal_year of this.fiscal_years) {
      this.fiscal_years_map[fiscal_year.shift()] = fiscal_year;
    }

    this.default_fiscal_year = frappe.defaults.get_user_default('fiscal_year');
  },
  set_defaults(report) {
    report.set_filter_value('fiscal_year', this.default_fiscal_year);
    set_return_period(report, this.fiscal_years_map[this.default_fiscal_year]);
  }
};
async function fetch_latest_returns(report) {
  const { message } = await frappe.call({
    method:
      'adaequare_gsp.adaequare_gsp.report.supplier_compliance.supplier_compliance.fetch_latest_returns',
    args: {
      fy: report.get_filter_value('fiscal_year'),
      suppliers: report.data
    }
  });
}

function set_return_period(report, return_period) {
  const today = frappe.datetime.get_today();
  if (return_period[1] > today) return_period[1] = today;
  report.set_filter_value('return_period', return_period);
}
