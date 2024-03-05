window.login = {};

window.verify = {};

login.bind_events = function() {
    $(window).on("hashchange", function() {
        login.route();
    });

    $(".form-forgot").on("submit", function(event) {
        console.log($("#forgot_email").val())
        event.preventDefault();
        var args = {};
        args.cmd = "mietrechtspraxis.api.check_reset_password";
        args.user = ($("#forgot_email").val() || "").trim();
        if(!args.user) {
            login.set_indicator('{{ _("Valid Login id required.") }}', 'red');
            return false;
        }
        login.call(args);
        return false;
    });

    $(".toggle-password").click(function() {
        $(this).toggleClass("fa-eye fa-eye-slash");
        var input = $($(this).attr("toggle"));
        if (input.attr("type") == "password") {
            input.attr("type", "text");
        } else {
            input.attr("type", "password");
        }
    });
}


login.route = function() {
    var route = window.location.hash.slice(1);
    route = "forgot";
    login[route]();
}

login.reset_sections = function(hide) {
    if(hide || hide===undefined) {
        $("section.for-forgot").toggle(false);
    }
    $('section .indicator').each(function() {
        $(this).removeClass().addClass('indicator').addClass('blue')
            .text($(this).attr('data-text'));
    });
}

login.forgot = function() {
    login.reset_sections();
    $(".for-forgot").toggle(true);
}


// Login
login.call = function(args, callback) {
    login.set_indicator('{{ _("Verifying...") }}', 'blue');

    return frappe.call({
        type: "POST",
        args: args,
        callback: callback,
        freeze: true,
        statusCode: login.login_handlers
    });
}

login.set_indicator = function(message, color) {
    $('section:visible .indicator')
        .removeClass().addClass('indicator').addClass(color).text(message)
}

login.login_handlers = (function() {
    var get_error_handler = function(default_message) {
        return function(xhr, data) {
            if(xhr.responseJSON) {
                data = xhr.responseJSON;
            }

            var message = default_message;
            if (data._server_messages) {
                message = ($.map(JSON.parse(data._server_messages || '[]'), function(v) {
                    // temp fix for messages sent as dict
                    try {
                        return JSON.parse(v).message;
                    } catch (e) {
                        return v;
                    }
                }) || []).join('<br>') || default_message;
            }

            if(message===default_message) {
                login.set_indicator(message, 'red');
            } else {
                login.reset_sections(false);
            }

        };
    }

    var login_handlers = {
        200: function(data) {
            if(data.message == 'Password Reset'){
                window.location.href = data.redirect_to;
            } else if(window.location.hash === '#forgot') {
                if(data.message==='not found') {
                    login.set_indicator('{{ _("Not a valid user") }}', 'red');
                } else if (data.message=='not allowed') {
                    login.set_indicator('{{ _("Not Allowed") }}', 'red');
                } else if (data.message=='disabled') {
                    login.set_indicator('{{ _("Not Allowed: Disabled User") }}', 'red');
                } else {
                    login.set_indicator('{{ _("Instructions Emailed") }}', 'green');
                }
            }
        },
        401: get_error_handler('{{ _("Invalid Login. Try again.") }}'),
        417: get_error_handler('{{ _("Oops! Something went wrong") }}')
    };

    return login_handlers;
} )();

frappe.ready(function() {

    login.bind_events();

    if (!window.location.hash) {
        window.location.hash = "#forgot";
    } else {
        $(window).trigger("hashchange");
    }

    $(".form-signup, .form-forgot").removeClass("hide");
    $(document).trigger('login_rendered');
});
