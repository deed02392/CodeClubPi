$(document).ready(function () {

    function updateTips(t) {
        $tips
            .text(t)
            .addClass("ui-state-highlight");
        setTimeout(function () {
            $tips.removeClass("ui-state-highlight", 1500);
        }, 500);
    }
    
    var $new_password = $("#new-password");
    var $confirm_new_password = $("#confirm-new-password");
    var $tips = $(".validateTips");

    $confirm_new_password.keypress(function(e) {
        if(e.which == 13) {
            $("#dialog-change-pass-btn").click();
            e.stopPropagation();
            return false;
        }
    });
    
    $('#change-password-dialog-form').dialog({
        autoOpen: true,
        modal: true,
        buttons: {
            "Cancel": {
                text: "Cancel",
                click: function() {
                    $(this).dialog('close');
                }
            },
            "Change": {
                text: "Change",
                id: "dialog-change-pass-btn",
                click: function() {
                    var bValid = true;
                    $new_password.removeClass("ui-state-error");
                    $confirm_new_password.removeClass("ui-state-error");
                    
                    $button = $("#dialog-change-pass-btn").find("span");
                    $button.text("Changing...");

                    $.post("/firstpass", {
                        "new-password": $new_password.val(),
                        "confirm-new-password": $confirm_new_password.val()
                    }, function (data) {
                        if (data == "OK") {
                            window.location.replace("/login.htm");
                        } else {
                            $new_password.addClass("ui-state-error");
                            $confirm_new_password.addClass("ui-state-error");
                            updateTips(data);
                            $button.text("Change");
                        }
                    });
                }
            }
        },
    });
    
    $('#change-password').click(function() {
        $("#change-password-dialog-form").dialog("open");
    });

});