function res_filt_dlg_show(cb_func, col_name) {
    var qpanel = document['dlg_res_filt_p'];
    qpanel['cb_func'] = cb_func;

    var bnode = qpanel.bodyNode;

    var qtype_node = bnode.one('#qtype');
    qtype_node.set('value', col_name);

    var sym_node = bnode.one('#symbol')
    sym_node.set('value', '');

    var arr = ['regex', 'negate', 'ignorecase'];
    for (var inx = 0; inx < arr.length; inx++) {
        var node  = bnode.one('#' + arr[inx])
        node.set('checked', false);
    }

    sym_node.select();
    qpanel.show();
    sym_node.focus();
}

YUI().use("panel", function (Y) {

    var qtype = '<select id="qtype">' +
                '<option value="tag">   Tag   </option>' +
                '<option value="file">  File  </option>' +
                '<option value="line">  Line  </option>' +
                '<option value="text">  Text  </option>' +
                '</select>';
    var body = '<table>' +
               '<tr> <td>Filter in </td>  <td>' + qtype + '</td> </tr>' +
               '<tr> <td>Filter for</td>  <td><input type="text" id="symbol"></td> </tr>' +
               '<tr> <td></td>        <td><input type="checkbox" id="regex">Regex</td> </tr>' +
               '<tr> <td></td>        <td><input type="checkbox" id="negate">Negate search</td> </tr>' +
               '<tr> <td></td>        <td><input type="checkbox" id="ignorecase">Case Insensitive</td> </tr>' +
               '</table>';

    function okAction(e) {
        e.preventDefault();
        qpanel.hide();
        var bnode = qpanel.bodyNode;

        var qtype = bnode.one('#qtype').get('value');
        if (!qtype) {
            return;
        }

        var symbol = bnode.one('#symbol').get('value');
        if (!symbol) {
            return;
        }

        var opt = [];
        var arr = ['regex', 'negate', 'ignorecase'];
        for (var inx = 0; inx < arr.length; inx++) {
            if (bnode.one('#' + arr[inx]).get('checked')) {
                opt.push(arr[inx]);
            }
        }

        var col_name = bnode.one('#qtype').get('value');

        var cb_func = qpanel['cb_func'];
        var q_args = {
            qtype  : qtype,
            symbol : symbol,
            opt    : opt,
            col_name    : col_name,
        };
        if (!cb_func) {
            return;
        }
        cb_func(q_args);
    }

    var qpanel = new Y.Panel({
        bodyContent: body,
//         width      : 250,
        zIndex     : 6,
        centered   : true,
        modal      : true,
        render     : '#resFiltPanel',
        buttons: [
            {
                value  : 'Cancel',
                section: Y.WidgetStdMod.FOOTER,
                action : function (e) {
                    e.preventDefault();
                    qpanel.hide();
                }
            },
            {
                value  : 'Ok',
                section: Y.WidgetStdMod.FOOTER,
                action : okAction,
            }
        ]
    });

    qpanel.bodyNode.on('key', okAction, 'enter');

    qpanel.hide();

    document['dlg_res_filt_y'] = Y;
    document['dlg_res_filt_p'] = qpanel;
});
