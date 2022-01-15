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