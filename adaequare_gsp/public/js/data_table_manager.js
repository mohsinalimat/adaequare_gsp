adaequare_gsp.DataTableManager = class DataTableManager {
    constructor(opts) {
        Object.assign(this, opts);
        this.make_dt();
    }

    async make_dt() {
        if (this.frm) {
            const { message } = await this.frm.call(
                this.method,
                this.args,
                this.callback
            );
            this.format_data(message);
            this.get_datatable();
        }
    }

    get_dt_columns() {
        if (!this.columns) return [];

        // making editable false by default
        return this.columns.map((col) => {
            if (col.editable === undefined) {
                col.editable = false;
            }
            return col;
        });
    }

    format_data(data) {
        if (!Array.isArray(data)) {
            data = Object.values(data);
        }

        if (!this.format_row) {
            this.data = data;
            return;
        }

        this.data = data.map(this.format_row);
    }

    get_datatable() {
        const datatable_options = {
            columns: this.get_dt_columns(),
            data: this.data,
            dynamicRowHeight: true,
            checkboxColumn: false,
            inlineFilters: true,
        };
        this.datatable = new frappe.DataTable(
            this.$reconciliation_tool_dt.get(0),
            datatable_options
        );
        $(`.${this.datatable.style.scopeClass} .dt-scrollable`).css(
            "max-height",
            "calc(100vh - 400px)"
        );

        if (this.data.length > 0) {
            this.$reconciliation_tool_dt.show();
            this.$no_data.hide();
        } else {
            this.$reconciliation_tool_dt.hide();
            this.$no_data.show();
        }
    }
};
