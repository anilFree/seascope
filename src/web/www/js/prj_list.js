function plist_dlg_show(cb_func) {
    var sym = ed_get_cur_word();

    var qpanel = document['dlg_plist_p'];
    qpanel['cb_func'] = cb_func;

    qpanel.show();
    qpanel['fetch_func']();
}

YUI().use('datasource-get', 'datasource-jsonschema',
          "panel", function (Y) {

    var body = '<table>' +
                    //'<tr>Choose a project</tr>' +
                    '<tr><div id="prjListTbl"></div><tr>' +
                '</table>';

    function prj_choice(prj) {
        var cb_func = qpanel['cb_func'];
        var p_args = {
            project  : prj,
        };
        if (!cb_func) {
            return;
        }
        cb_func(p_args);
    }

    var qpanel = new Y.Panel({
        bodyContent: body,
        width      : 250,
        zIndex     : 6,
        centered   : true,
        modal      : true,
        render     : '#plistPanel',
        buttons: [
            {
                value  : 'Refresh',
                section: Y.WidgetStdMod.FOOTER,
                action : function (e) {
                    fetch_prj_list();
                }
            },
        ]
    });

    function createPlistTable(cbox) {
        var dt = new google.visualization.DataTable();
        dt.addColumn('string', 'Choose a project');

        dt.addRows(1);
        dt.setCell(0, 0, 'fetching project list...');

        var dv = new google.visualization.DataView(dt);
        var table = new google.visualization.Table(cbox.one('#prjListTbl').getDOMNode());

        cbox['g_dt']  = dt;
        cbox['g_dv']  = dv;
        cbox['g_table'] = table;

        table.draw(dv);
    }

    function populatePlistTable(cbox, res) {
        var table = cbox['g_table'];
        var dt = new google.visualization.DataTable();

        dt.addColumn('string', 'Choose a project');

        for(var i = 0; i < res.length; i++) {
            dt.addRow([res[i]]);
        }
        var dv = new google.visualization.DataView(dt);
        table.draw(dv);

        cbox['g_dt']  = dt;
        cbox['g_dv']  = dv;

        if (res.length == 1) {
            qpanel.hide();
            //confirm(res[0]);
            prj_choice(res[0]);
            return;
        }
        google.visualization.events.addListener(table, 'select', function() {
            var sel = table.getSelection();
            if (sel.length == 0) {
                return
            }
            var row = sel[0].row;

            var dv = cbox['g_dv'];
            var prj = dv.getValue(row, 0);

            qpanel.hide();
            prj_choice(prj);
        });
    }

    function fetch_prj_list() {
        var cbox = qpanel.bodyNode;
        var url = document['server_info'].url;
        var src = new Y.DataSource.Get({
            source : url,
        });
        src.plug(Y.Plugin.DataSourceJSONSchema, {
                schema : {
                        resultListLocator : 'res',
                }
        });

        var rd = {
            cmd_type : 'project_list',
        }
        var request = '?' + to_query_string(rd);

        src.sendRequest({
                request : request,
                callback : {
                        success: function (e) {
                                var res = e.response.results;
                                populatePlistTable(cbox, res);
                        },
                        failure: function (e) {
                                alert(e.error.message);
                        },
                },
        });

    }

    qpanel.after('render', function(e) {
        var cbox = qpanel.bodyNode;
        var node = cbox.one('#prjListTbl');
        createPlistTable(cbox);
    });
    qpanel['fetch_func'] = fetch_prj_list;
    qpanel.hide();

    document['dlg_plist_y'] = Y;
    document['dlg_plist_p'] = qpanel;
});
