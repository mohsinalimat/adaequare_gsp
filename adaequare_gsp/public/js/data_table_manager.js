adaequare_gsp.DataTableManager = class DataTableManager {
    constructor(opts) {
        Object.assign(this, opts);
        this.make();
    }

    async make() {
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

adaequare_gsp.TabView = class TabView {
    constructor(options) {
        // Options: frm, $wrapper, tabs
        Object.assign(this, options);
        this.make();
    }

    make() {
        const me = this;
        this.$wrapper.html(
            `${frappe.render_template("data_table_tab_view", {
                tabs: Object.entries(this.tabs).map(([name, { label }]) =>
                    Object({ name, label })
                ),
            })}`
        );

        const $tabs = this.$wrapper.find(".form-tabs .tab-item");
        $tabs.click(function () {
            const $this = $(this);
            $tabs.removeClass("active");
            $this.addClass("active");
        });

        for (let [name, tab] of Object.entries(this.tabs)) {
            tab.$tab = this.$wrapper.find(`#${name}-tab`);
            tab.$tab.click(() => {
                if (tab.onclick) tab.onclick(me);
                if (tab.datatable_options) {
                    this.render_data_table(tab.datatable_options);
                }
            });
            if (tab.default) tab.$tab.click();
        }
    }

    render_data_table(options) {
        this.frm.$data_table_manager = new adaequare_gsp.DataTableManager({
            frm: this.frm,
            $reconciliation_tool_dt: this.$wrapper.find(".tab-content"),
            $no_data: $(
                '<div class="text-muted text-center">No Matching Data Found</div>'
            ),
            ...options,
        });
    }
};
