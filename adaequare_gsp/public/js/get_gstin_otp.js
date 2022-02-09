frappe.provide("adaequare_gsp")

adaequare_gsp.get_gstin_otp = function(call) {
    frappe.prompt({
        fieldtype: 'Data',
        label: 'One Time Password',
        fieldname: 'otp',
        reqd: 1,
        description: "An OTP has been sent to your registered mobile/email for further authentication. Please provide OTP."
    },
        function (_data) {
            call.args.otp = _data.otp
            frappe.call(call);
    }, 'Enter OTP')
}

frappe.provide("reco_tool")
reco_tool.get_gstin_otp = function (func, frm, d, method) {
    frappe.prompt({
        fieldtype: 'Data',
        label: 'One Time Password',
        fieldname: 'otp',
        reqd: 1,
        description: "An OTP has been sent to your registered mobile/email for further authentication. Please provide OTP."
    },
        function (_data) {
            func(frm, d, method, _data.otp);
    }, 'Enter OTP')
}