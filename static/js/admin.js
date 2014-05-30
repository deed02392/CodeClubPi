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
});