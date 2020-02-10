function about_dlg_show() {
    var sym = ed_get_cur_word();

    var Y = document['dlg_about_y'];
    var qpanel = document['dlg_about_p'];

    qpanel.show();
}

YUI().use("panel", function (Y) {

    var body = '<table>' +
                    '<tr>' +
                        '<td align="center">' +
                            '<object height="100" width="100" data="images/seascope.svg" type="image/svg+xml"></object>' +
                        '</td>' +
                        '<td>' +
                            '<strong> Seascope 0.9+ </strong>' +
                            '<p> A graphical user interface for idutils, cscope and gtags. </p>' +
                            '<p> Copyright � 2010-2020 Anil Kumar </p>' +
                            '<p><a href="https://github.com/anilFree/seascope"  target="_blank">https://github.com/anilFree/seascope</a></p>' +
                        '</td>' +
                    '</tr>' +
                '</table>';

    var qpanel = new Y.Panel({
        bodyContent: body,
        zIndex     : 6,
        centered   : true,
        modal      : true,
        render     : '#aboutPanel',
        buttons: [
            {
                value  : 'Ok',
                section: Y.WidgetStdMod.FOOTER,
                isDefault: true,
                action : function (e) {
                    qpanel.hide();
                }
            },
        ]
    });

    qpanel.hide();

    document['dlg_about_y'] = Y;
    document['dlg_about_p'] = qpanel;
});
