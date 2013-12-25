function qry_dlg_show(cb_func, qtype) {
    var sym = ed_get_cur_word();

    var qpanel = document['dlg_qry_p'];
    qpanel['cb_func'] = cb_func;

    var bnode = qpanel.bodyNode;

    if (!qtype) {
        qtype = 'REF';
    }
    var qtype_node = bnode.one('#qtype')
    qtype_node.set('value', qtype);

    var sym_node = bnode.one('#symbol')
    sym_node.set('value', sym);

    var substring_node  = bnode.one('#substring')
    substring_node.set('checked', false);

    var ignorecase_node = bnode.one('#ignorecase')
    ignorecase_node.set('checked', false);

    sym_node.select();
    qpanel.show();
    sym_node.focus();
}

YUI().use("panel", function (Y) {

    var qry_arr = [
        ['REF',      'References to'],
        ['DEF',      'Definition of'],
        //['<--',      'Called Functions'],
        ['-->',      'Calling Functions'],
        //['TXT',      'Find Text'],
        ['GREP',     'Find Egrep'],
        ['FIL',      'Find File'],
        ['INC',      'Include/Import'],
        ['CTREE',    'Call Tree'],
        ['CLGRAPH',  'Class Graph'],
        ['CLGRAPHD', 'Class Graph Dir'],
        ['FFGRAPH',  'File Func Graph'],
    ];
    var qtype = '<select id="qtype"">';
    var is_disabled = false;
    for (var i = 0; i < qry_arr.length; i++) {
        v = qry_arr[i];
        if (v[0] == 'CTREE') {
            is_disabled = true;
        }
        if (is_disabled) {
            qtype += '<option value="' + v[0] + '"  disabled>' + v[1] + '</option>';
        } else {
            qtype += '<option value="' + v[0] + '"          >' + v[1] + '</option>';
        }
    }
    qtype += '</select>';
    var body = '<table>' +
               '<tr> <td>Type</td>    <td>' + qtype + '</td> </tr>' +
               '<tr> <td>Symbol</td>  <td><input type="text"     id="symbol"></td> </tr>' +
               '<tr> <td></td>        <td><input type="checkbox" id="substring">Substring</td> </tr>' +
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
        if (bnode.one('#substring').get('checked')) {
            opt.push('substring');
        }
        if (bnode.one('#ignorecase').get('checked')) {
            opt.push('ignorecase');
        }

        var cb_func = qpanel['cb_func'];
        var q_args = {
            qtype  : qtype,
            symbol : symbol,
            opt    : opt,
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
        render     : '#qryPanel',
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
                //isDefault: true,
                action : okAction,
            }
        ]
    });

    qpanel.bodyNode.on('key', okAction, 'enter');

    qpanel.hide();

    document['dlg_qry_y'] = Y;
    document['dlg_qry_p'] = qpanel;
});
