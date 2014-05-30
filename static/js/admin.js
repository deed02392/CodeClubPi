$(document).ready(function () {
    $('#students-jtable').jtable({
        title: "&nbsp;",
        jqueryuiTheme: true,
        sorting: true,
        defaultSorting: 'fullname ASC',
        actions: {
            listAction: '/ajax/students-list',
            createAction: '/ajax/students-add',
            updateAction: '/ajax/students-update',
            deleteAction: '/ajax/students-delete'
        },
        fields: {
            fullname: {
                title: 'Full Name',
                width: '30%',
                sorting: true
            },
            username: {
                title: 'Username',
                width: '20%',
                create: true,
                key: true,
                sorting: false
            },
            password: {
                title: 'Password',
                width: '20%',
                sorting: false,
                display: function(data) {
                    var data = data.record.password;
                    return '<span class="hide-password">' + data + '</span>';
                }
            },
            url: {
                title: 'URL',
                width: '20%',
                sorting: false,
                create: false,
                edit: false,
                display: function(data) {
                    var data = data.record.url;
                    return '<a href="' + data + '">' + data + '</a>';
                }
            },
            isindexed: {
                title: 'Show?',
                width: '5%',
                type: 'checkbox',
                values: { '0': 'No', '1': 'Yes' },
                defaultValue: '1',
                sorting: false
            },
        }
    }).jtable('load');
    
    function updateTips(t) {
        $tips
            .text(t)
            .addClass("ui-state-highlight");
        setTimeout(function () {
            $tips.removeClass("ui-state-highlight", 1500);
        }, 500);
    }
    
    var $current_password = $("#current-password");
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
        autoOpen: false,
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
                    $current_password.removeClass("ui-state-error");
                    $new_password.removeClass("ui-state-error");
                    $confirm_new_password.removeClass("ui-state-error");
                    
                    $button = $("#dialog-change-pass-btn").find("span");
                    $button.text("Changing...");

                    $.post("/pass", {
                        "current-password": $current_password.val(),
                        "new-password": $new_password.val(),
                        "confirm-new-password": $confirm_new_password.val()
                    }, function (data) {
                        if (data == "OK") {
                            window.location.replace("/login.htm");
                        } else {
                            $current_password.addClass("ui-state-error");
                            $new_password.addClass("ui-state-error");
                            $confirm_new_password.addClass("ui-state-error");
                            updateTips(data);
                            $current_password.select();
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