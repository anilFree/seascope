function res_t_resize(t, is_sel) {
    var res_tv = document['res_tv'];

    var cbox = t.get('panelNode');
    var table = cbox['g_table'];

    var lh = cbox.ancestor().ancestor().one('.yui3-tabview-list').get('clientHeight');
    var w = res_tv.get('width') - 2;
    var h = res_tv.get('height') - lh;

    if (is_sel) {
        if (cbox['g_table_h'] == h && cbox['g_table_w'] == w) {
            return;
        }
    }
    cbox['g_table_h'] = h
    cbox['g_table_w'] = w

    var dv = cbox['g_dv'];
    table.draw(dv, {
        height: h,
        width: w,
        page : 'enable',
        pageSize : 200,
    });
}

function res_tv_cur_tab() {
    var res_tv = document['res_tv'];
    if (!res_tv.size()) {
        return;
    }
    return res_tv.get('selection');
}

function res_tv_resize(e) {
    var t = res_tv_cur_tab();
    if (!t) {
        return;
    }
    res_t_resize(t);
}

function res_tv_resize_sel(e) {
    var t = res_tv_cur_tab();
    if (!t) {
        return;
    }
    res_t_resize(t, true);
}

function start_query(qargs) {
    var res_tv = document['res_tv'];

    var label = qargs.symbol;
    if (qargs.opt.indexOf('substring') >= 0) {
        if (qargs.qtype == 'FIL') {
            label = '*' + label + '*'
        } else {
            label = '.*' + label + '.*'
        }
    }
    label = qargs.qtype + ' ' + label;

    var targs = {
        label   : label,
        content :
//                   '<table>' +
//                     '<tr>' +
                        '<div id="errLbl" align="right" style="display:none; width=100%; color:black; background-color:Yellow;"></div>' +
//                     '</tr>' +
//                     '<tr>'  +
                        '<div id="resTbl"> </div>',
//                     '</tr>' +
//                   '</table>',
    };
    res_tv['qargs'] = qargs;
    res_tv.add(targs);
    var inx = res_tv.size() - 1;
    res_tv.selectChild(inx);

//    var t = res_tv.item(inx);
//     t['qargs'] = qargs;
}

function res_filter_cb(fargs) {
    var t = res_tv_cur_tab();
    var cbox = t.get('panelNode');
    var dt = cbox['g_dt'];
    var dv = cbox['g_dv'];

    var col_arr = ['tag', 'file', 'line', 'text'];
    fargs.col = col_arr.indexOf(fargs.col_name);
    var row_list = filter_table(dt, fargs);
    if (row_list.length) {
        dv.hideRows(row_list);
        res_tv_resize(null);
    }
}

function res_show_all_cb() {
    var t = res_tv_cur_tab();
    var cbox = t.get('panelNode');
    var dt = cbox['g_dt'];
    var dv = cbox['g_dv'];

    var num_rows = dt.getNumberOfRows();
    if (num_rows) {
        dv.setRows(0, num_rows -1);
    }
    res_tv_resize(null);
}

function res_remove_item_cb(row) {
    if (row == -1) {
        return;
    }
    var t = res_tv_cur_tab();
    var cbox = t.get('panelNode');
    var dt = cbox['g_dt'];
    var dv = cbox['g_dv'];

    dv.hideRow([row]);
    res_tv_resize(null);
}

function res_ctx_menu_cb(cargs) {
    //confirm('res_ctx_menu_cb: ' + choice);
    if (cargs.choice == 'filter') {
        var col_arr = ['tag', 'file', 'line', 'text'];
        var col_name = col_arr[cargs.col];
        res_filt_dlg_show(res_filter_cb, col_name);
    } else if(cargs.choice == 'show_all') {
        res_show_all_cb();
    } else if (cargs.choice == 'remove_item') {
        res_remove_item_cb(cargs.row);
    }
}


function createResTable(t) {
    var cbox = t.get('panelNode');
    var dt = new google.visualization.DataTable();
    dt.addColumn('string', 'tag');
    dt.addColumn('string', 'file');
    dt.addColumn('string', 'line');
    dt.addColumn('string', 'text');

    dt.addRows(1);
    dt.setCell(0, 0, 'running query...');

    var dv = new google.visualization.DataView(dt);
    var table = new google.visualization.Table(cbox.one('#resTbl').getDOMNode());

    cbox['g_dt']  = dt;
    cbox['g_dv']  = dv;
    cbox['g_table'] = table;

    res_t_resize(t);
}

function populateResTable(t, res) {
    var cbox = t.get('panelNode');
    var dt = cbox['g_dt'];
    dt.removeRow(0);
    //confirm(res.length);
    dt.addRows(res);

    cbox['g_table_h'] = 0;
    res_t_resize(t);

    if (res.length == 1) {
        var dv = cbox['g_dv'];
        var row = 0;
        var file = dv.getValue(row, 1);
        var line = dv.getValue(row, 2);
        ed_show_file_line(file, line);
    }

    var table = cbox['g_table'];
    google.visualization.events.addListener(table, 'select', function(e) {
        var sel = table.getSelection()
        if (sel.length == 0) {
            return
        }
        var row = sel[0].row;

        var dv = cbox['g_dv'];
        var file = dv.getValue(row, 1);
        var line = dv.getValue(row, 2);
        ed_show_file_line(file, line);
    });
}

YUI().use('datasource-get', 'datasource-jsonschema',
          'node-event-delegate', 'event-key',
          'tabview', 'escape', 'plugin', 'node', function(Y) {

    var ResAddable = function(config) {
        ResAddable.superclass.constructor.apply(this, arguments);
    };

    ResAddable.NAME = 'addableTabs';
    ResAddable.NS = 'addable';

    Y.extend(ResAddable, Y.Plugin.Base, {
        ADD_TEMPLATE: '<li class="yui3-tab" title="add a tab">' +
                    '<a class="yui3-tab-label yui3-tab-add">+</a></li>',

        initializer: function(config) {
            var tabview = this.get('host');
            tabview.after('render', this.afterRender, this);
            tabview.get('contentBox').delegate('click', this.onAddClick, '.yui3-tab-add', this);

            tabview.after('tab:render', this.afterTabRender, this);
            //tabview.after('tab:widget:contentUpdate', this.afterTabRender, this);

            tabview.get('listNode').setStyle('border-width', '0 0 0px');
            tabview.get('panelNode').setStyle('padding', '0em');
        },

        afterRender: function(e) {
            var tv = this.get('host');
            tv.get('contentBox').one('> ul').append(this.ADD_TEMPLATE);
        },

        onAddClick: function(e) {
            e.stopPropagation();
            qry_dlg_show(start_query);
        },

        afterTabRender: function(e) {
            var t = e.target;
            var cbox = t.get('panelNode');
            var resTblNode = cbox.one('#resTbl');
//             confirm(resTblNode);
//             if (resTblNode) {
//               resTblNode = resTblNode.getDOMNode();
//             }
            if (resTblNode) {
                createResTable(t);

                var url = document['server_info'].url;
                var src = new Y.DataSource.Get({
                    source : url,
                });
                src.plug(Y.Plugin.DataSourceJSONSchema, {
                        schema : {
                                //resultListLocator : 'res',
                                resultFields : ['res', 'err_data'],
                        }
                });

                var tv = this.get('host');

                var qargs = tv['qargs'];
                tv['qargs'] = null;

                var rd = {
                    project  : document['project'],
                    cmd_type : 'query',
                    cmd_str  : qargs.qtype,
                    req      : qargs.symbol,
                    opt      : qargs.opt.join(','),
                }
                var hint_file = ed_get_cur_file();
                if (hint_file) {
                    rd.hint_file = hint_file;
                }
                var request = '?' + to_query_string(rd);

                src.sendRequest({
                        request : request,
                        callback : {
                                success: function (e) {
                                        var err_data = e.data.err_data;
                                        if (err_data) {
                                            var node = cbox.one('#errLbl');
                                            node.setHTML(err_data);
                                            node.show();
                                            node.after('click', function(e) {
                                                node.hide();
                                            });
                                        }

                                        var res = e.data.res;
                                        populateResTable(t, res);
                                },
                                failure: function (e) {
                                        cbox['g_dt'].setCell(0, 0, e.error.message);
                                        cbox['g_table'].draw(cbox['g_dv']);
                                },
                        },
                });
           }
        }
    });

    var Removeable = function(config) {
        Removeable.superclass.constructor.apply(this, arguments);
    };

    Removeable.NAME = 'removeableTabs';
    Removeable.NS = 'removeable';

    Y.extend(Removeable, Y.Plugin.Base, {
        REMOVE_TEMPLATE: '<a class="yui3-tab-remove" title="remove tab">x</a>',

        initializer: function(config) {
            var tabview = this.get('host'),
                cb = tabview.get('contentBox');

            cb.addClass('yui3-tabview-removeable');
            cb.delegate('click', this.onRemoveClick, '.yui3-tab-remove', this);

            // Tab events bubble to TabView
            tabview.after('tab:render', this.afterTabRender, this);
        },

        afterTabRender: function(e) {
            // boundingBox is the Tab's LI
            e.target.get('boundingBox').append(this.REMOVE_TEMPLATE);
        },

        onRemoveClick: function(e) {
            e.stopPropagation();
            var tab = Y.Widget.getByNode(e.target);
            tab.remove();
        }
    });

    var res_tv = new Y.TabView({
        children: [],
        plugins: [ResAddable, Removeable]
    });

    res_tab_list_pop_dlg_setup(function(cargs) {
        if (cargs.choice == 'close_all') {
            res_tv.removeAll();
        }
    });
    res_tbl_pop_dlg_setup(res_ctx_menu_cb);

    res_tv.after('heightChange',    res_tv_resize);
    res_tv.after('widthChange',     res_tv_resize);
    res_tv.after("selectionChange", function(e) {
        Y.later(0, null, res_tv_resize_sel, e);
    });

    document['res_tv'] = res_tv;
    res_tv.render('#resTabs');
});
