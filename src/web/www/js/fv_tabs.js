function fv_t_resize(t, is_sel) {
    var cbox = t.get('panelNode');
    var fv_tv = document['fv_tv'];

    var w = fv_tv.get('width') - 2;
    var lh = cbox.ancestor().ancestor().one('.yui3-tabview-list').get('clientHeight');
    var h = fv_tv.get('height') - lh;

    if (is_sel) {
        if (cbox['g_table_h'] == h && cbox['g_table_w'] == w) {
            return;
        }
    }
    cbox['g_table_h'] = h
    cbox['g_table_w'] = w

    var table = cbox['g_table'];
    var dv = cbox['g_dv'];
    if (!table) {
        return;
    }
    table.draw(dv, {
        height: h,
        width: w,
        page : 'enable',
        pageSize : 200,
    });
}

function fv_tv_cur_tab() {
    var fv_tv = document['fv_tv'];
    if (!fv_tv.size()) {
        return null;
    }
    return fv_tv.get('selection');
}

function fv_tv_resize(e) {
    var t = fv_tv_cur_tab();
    if (!t) {
        return;
    }
    fv_t_resize(t);
}

function fv_tv_resize_sel(e) {
    var t = fv_tv_cur_tab();
    if (!t) {
        return;
    }
    fv_t_resize(t, true);
}

function flist_query() {
    var fv_tv = document['fv_tv'];
    var targs = {
        label   : 'files',
        content : '<div id="fvTbl"> </div>',
    };
    fv_tv.add(targs);
    var inx = fv_tv.size() - 1;
    fv_tv.selectChild(inx);
}

function flist_filter_cb(fargs) {
    var t = fv_tv_cur_tab();
    var cbox = t.get('panelNode');
    var dt = cbox['g_dt'];
    var dv = cbox['g_dv'];

    var col_arr = ['file', 'path'];
    fargs.col = col_arr.indexOf(fargs.col_name);
    var row_list = filter_table(dt, fargs);
    if (row_list.length) {
        dv.hideRows(row_list);
        fv_tv_resize(null);
    }
}

function flist_show_all_cb() {
    var t = fv_tv_cur_tab();
    var cbox = t.get('panelNode');
    var dt = cbox['g_dt'];
    var dv = cbox['g_dv'];

    var num_rows = dt.getNumberOfRows();
    if (num_rows) {
        dv.setRows(0, num_rows -1);
    }
    fv_tv_resize(null);
}

function flist_remove_item_cb(row) {
    if (row == -1) {
        return;
    }
    var t = fv_tv_cur_tab();
    var cbox = t.get('panelNode');
    var dt = cbox['g_dt'];
    var dv = cbox['g_dv'];

    dv.hideRows([row]);
    fv_tv_resize(null);
}

function flist_ctx_menu_cb(cargs) {
    //confirm('flist_ctx_menu_cb: ' + choice);
    if (cargs.choice == 'filter') {
        var col_arr = ['file', 'path'];
        var col_name = col_arr[cargs.col];
        flist_filt_dlg_show(flist_filter_cb, col_name);
    } else if(cargs.choice == 'show_all') {
        flist_show_all_cb();
    } else if (cargs.choice == 'remove_item') {
        flist_remove_item_cb(cargs.row);
    }
}

function createFvTable(t) {
    var cbox = t.get('panelNode');
    var dt = new google.visualization.DataTable();
    dt.addColumn('string', 'file');
    dt.addColumn('string', 'path');

    dt.addRows(1);
    dt.setCell(0, 0, 'fetching file list...');

    var dv = new google.visualization.DataView(dt);
    var table = new google.visualization.Table(cbox.getDOMNode());

    cbox['g_dt']  = dt;
    cbox['g_dv']  = dv;
    cbox['g_table'] = table;

    fv_t_resize(t);
}

function populateFvTable(t, res) {
    var cbox = t.get('panelNode');
    var dt = google.visualization.arrayToDataTable(res);
    var dv = new google.visualization.DataView(dt);
    cbox['g_dt'] = dt;
    cbox['g_dv'] = dv;

    fv_t_resize(t);

    var table = cbox['g_table'];
    google.visualization.events.addListener(table, 'select', function() {
        var sel = table.getSelection();
        if (sel.length == 0) {
            return
        }
        var row = sel[0].row;

        var dv = cbox['g_dv'];
        var file = dv.getValue(row, 1);
        var line = 1
        ed_show_file_line(file, line);
    });
}

YUI().use('datasource-get', 'datasource-jsonschema',
          'tabview', 'escape', 'plugin', 'node', function(Y) {

    var ResAddable = function(config) {
        ResAddable.superclass.constructor.apply(this, arguments);
    };

    ResAddable.NAME = 'addableTabs';
    ResAddable.NS = 'addable';

    Y.extend(ResAddable, Y.Plugin.Base, {
//         ADD_TEMPLATE: '<li class="yui3-tab" title="add a tab">' +
//                     '<a class="yui3-tab-label yui3-tab-add">+</a></li>',

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
            var tabview = this.get('host');
            //tabview.get('contentBox').one('> ul').append(this.ADD_TEMPLATE);
        },

        onAddClick: function(e) {
            e.stopPropagation();
            var tabview = this.get('host'),
                input = this.getTabInput();
            tabview.add(input);
            tabview.selectChild(tabview.size() - 1);
        },

        afterTabRender: function(e) {
            var t = e.target;
            var cbox = t.get('panelNode');

            var fvTblNode = cbox.one('#fvTbl');
//             confirm(fvTblNode);
//             if (fvTblNode) {
//               fvTblNode = fvTblNode.getDOMNode();
//             }
            if (fvTblNode) {
                createFvTable(t);

                var src = new Y.DataSource.Get({
                    source : document['server_info'].url,
                });
                src.plug(Y.Plugin.DataSourceJSONSchema, {
                        schema : {
                                resultListLocator : 'res',
                        }
                });

                var request = '?' + to_query_string({
                    project  : document['project'],
                    cmd_type : 'query',
                    cmd_str  : 'FLIST',
                });

                src.sendRequest({
                        request : request,
                        callback : {
                                success: function (e) {
                                        var res = e.response.results;
                                        populateFvTable(t, res);
                                },
                                failure: function (e) {
                                        cbox['g_dt'].setCell(0, 0, e.error.message);
                                        cbox['g_table'].draw(cbox['g_dv']);
                                        alert(e.error.message);
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

    var fv_tv = new Y.TabView({
        children: [],
        plugins: [ResAddable, Removeable]
    });

    flist_tbl_pop_dlg_setup(flist_ctx_menu_cb);

    fv_tv.after('heightChange',    fv_tv_resize);
    fv_tv.after('widthChange',     fv_tv_resize);
    fv_tv.after("selectionChange", function(e) {
        Y.later(0, null, fv_tv_resize_sel, e);
    });

    fv_tv.after('removeChild', function(e) {
        flist_query();
    });

    document['fv_tv'] = fv_tv;
    fv_tv.render('#fvTabs');
});
