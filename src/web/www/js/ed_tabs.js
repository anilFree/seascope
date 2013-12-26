function ed_ct_resize(t, is_sel) {
    var cbox = t.get('panelNode');

    var ed_tv = document['ed_tv'];
    var w = ed_tv.get('width');
    w = Math.floor(w * 0.25);
    var lh = cbox.ancestor().ancestor().one('.yui3-tabview-list').get('clientHeight');
    var h = ed_tv.get('height') - lh;

    if (is_sel) {
        if (cbox['g_table_h'] == h && cbox['g_table_w'] == w) {
            return;
        }
    }
    cbox['g_table_h'] = h
    cbox['g_table_w'] = w

    var table = cbox['g_table'];
    var dv = cbox['g_dv'];
    table.draw(dv, {
        width: w,
        height: h,
        page : 'enable',
        pageSize : 200,
    });
}

function ed_ace_resize(t, is_sel) {
    var cbox = t.get('panelNode');
    var ed_tv = document['ed_tv'];

//     var w = ed_tv.get('width') - 15;
//     var lh = cbox.ancestor().ancestor().one('.yui3-tabview-list').get('clientHeight');
//     var h = ed_tv.get('height') - lh - 20;

    var editor = cbox['a_ed'];
    editor.resize();
}

function ed_tv_resize(e) {
    var ed_tv = document['ed_tv'];
    if (!ed_tv.size()) {
        return;
    }
    var t = ed_tv.get('selection');
    if (!t) {
        return;
    }

    ed_ct_resize(t);
    ed_ace_resize(t);
}

function ed_tv_resize_sel(e) {
    var ed_tv = document['ed_tv'];
    if (!ed_tv.size()) {
        return;
    }
    var t = ed_tv.get('selection');
    if (!t) {
        return;
    }

    ed_ct_resize(t, true);
    ed_ace_resize(t, true);
}

function ed_get_cur_word() {
    var ed_tv = document['ed_tv'];
    if (!ed_tv.size()) {
        return '';
    }
    //var t = ed_tv.get('activeDescendant');
    var t = ed_tv.get('selection');
    var cbox = t.get('panelNode');
    var editor = cbox['a_ed'];
    var word = editor.getCopyText();
    //word = word.replace(/^\s+|\s+$/g, '');
    if (!word) {
        var pos = editor.getCursorPosition();
        word = editor.getSession().getLine(pos.row);
        function is_word_char(c) {
            if ((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
                (c >= '0' && c <= '9') || (c == '_')) {
                return true;
            }
            return false;
        }
        var linx = pos.column;
        while(linx > 0 && is_word_char(word.charAt(linx - 1))) {
            linx--;
        }
        var rinx = pos.column;
        while(rinx < word.length && is_word_char(word.charAt(rinx))) {
            rinx++;
        }
        word = word.slice(linx, rinx);
    }
    return (word);
}

function ed_get_cur_file() {
    var ed_tv = document['ed_tv'];
    if (!ed_tv.size()) {
        return '';
    }
    //var t = ed_tv.get('activeDescendant');
    var t = ed_tv.get('selection');
    if (!t) {
        return null;
    }
    return t['ed_file'];
}

function createCtTable(t) {
    var cbox = t.get('panelNode');
    var ctNode = cbox.one('#ctTbl');
    //confirm(ctNode);
    if (ctNode) {
        ctNode = ctNode.getDOMNode();
    }
    if (!ctNode) {
        return;
    }

    var dt = new google.visualization.DataTable();
    dt.addColumn('string', 'name');
    dt.addColumn('number', 'line');
    dt.addColumn('string', 'type');

    dt.addRows(1);
    dt.setCell(0, 0, 'fetching ctags...');

    var dv = new google.visualization.DataView(dt);
    var table = new google.visualization.Table(ctNode);

    cbox['g_dt']  = dt;
    cbox['g_dv']  = dv;
    cbox['g_table'] = table;

    var ed_tv = document['ed_tv'];
    ed_ct_resize(t);

    google.visualization.events.addListener(table, 'select', function() {
        var sel = table.getSelection()
        if (sel.length == 0) {
            return
        }
        var row = sel[0].row;
        var line = cbox['g_dv'].getValue(row, 1);

        var editor = cbox['a_ed'];
        editor.gotoLine(line);
        editor.focus();
    });
}

function populateCtTable(t, res) {
    var cbox = t.get('panelNode');
    var table = cbox['g_table'];
    var dt = cbox['g_dt'];

    dt.removeRow(0);
    for (var i = 0; i < res.length; i++) {
        var r = res[i];
        dt.addRow([r[0], parseInt(r[1]), r[2]]);
    }

//     var ed_tv = document['ed_tv'];
    ed_ct_resize(t);
}

function ed_ct_line_change(t, line) {
    var cbox = t.get('panelNode');
    var table = cbox['g_table'];
    var dv = cbox['g_dv'];

    function line_val(dv, inx) {
        return dv.getValue(inx, 1);
    }

//    confirm('ed_ct_line_change ' + line);
    var num_rows = dv.getNumberOfRows();
    if (num_rows == 0) {
        return;
    }

    var inx;

    var sel = table.getSelection();
    if (sel.length) {
        inx = sel[0].row;
    } else {
        inx = 0;
    }

    if (line_val(dv, inx) == line) {
        return;
    }
    if (line_val(dv, inx) < line) {
        while (inx + 1 < num_rows) {
            if (line_val(dv, inx + 1) > line) {
                break;
            }
            inx++;
        }
    } else {
        while (inx - 1 >= 0) {
            inx--;
            if (line_val(dv, inx) <= line) {
                break;
            }
        }
    }
    table.setSelection([{row:inx, col:null}]);
//    confirm('inx = ' + inx);
}

function focusAceEditor(cbox, res, line) {
    var editor = cbox['a_ed'];
    if (editor) {
        editor.focus();
    }
}

function setAceEditorText(t, res, line) {
    var cbox = t.get('panelNode');
    var editor = cbox['a_ed'];

    var file = t['ed_file'];
    var fp = file.split('.')
    if (fp.length > 1) {
        var sfx = fp[fp.length - 1];
        if (['c', 'cpp', 'c++', 'h'].indexOf(sfx) >= 0) {
            editor.getSession().setMode("ace/mode/c_cpp");
        } else if (['java'].indexOf(sfx) >= 0) {
            editor.getSession().setMode("ace/mode/java");
        } else if (['py'].indexOf(sfx) >= 0) {
            editor.getSession().setMode("ace/mode/python");
        } else if (['tin', 'tac', 'itin'].indexOf(sfx) >= 0) {
            editor.getSession().setMode("ace/mode/c_cpp");
        }
    } else {
        editor.getSession().setMode("ace/mode/c_cpp");
    }
    editor.getSession().setTabSize(8);

    editor.setValue(res);
    editor.getSession().selection.on('changeCursor', function(e, e2, e3) {
        var old_line = cbox['a_ed_last_line'];
        var new_line = editor.getCursorPosition().row + 1;
        if (new_line != old_line) {
            cbox['a_ed_last_line'] = new_line;
            ed_ct_line_change(t, new_line);
            //confirm('onCursorChage: ' + old_line + ' ' + new_line);
        }
    });
    editor.gotoLine(line);
    editor.scrollToLine(line, true);

    editor.focus();
    ed_ace_resize(t);
}

function createAceEditor(t) {
    var cbox = t.get('panelNode');
    var edNode = cbox.one('#aceEditor');
    //confirm(edNode);
    if (edNode) {
        edNode = edNode.getDOMNode();
    }
    if (!edNode) {
        return;
    }
    var editor = ace.edit(edNode);
    //var editor = ace.edit(cbox.getDOMNode());
    editor.getSession().setUseWorker(false);
    editor.setTheme("ace/theme/eclipse");

    editor.setReadOnly(true);
    //editor.setValue("Loading...");
    //editor.resize();
    editor.gotoLine("1");
    editor.focus();
    cbox['a_ed'] = editor;
    cbox['a_ed_last_line'] = 0;
}

function show_ctags_new(t, file) {
    if (!t) {
        return;
    }

    var Y = document['edy'];
    var src;
    src = new Y.DataSource.Get({
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
        cmd_str  : 'FCTAGS',
        req      : file,
    });
    src.sendRequest({
            request : request,
            callback : {
                    success: function (e) {
                            var res = e.response.results;
                            populateCtTable(t, res[0]);
                    },
                    failure: function (e) {
                            var cbox = t.get('panelNode');
                            cbox['g_dt'].setCell(0, 0, e.error.message);
                            cbox['g_table'].draw(cbox['g_dv']);
                            alert(e.error.message);
                    },
            },
    });
}

function show_ace_editor_new(t, file, line) {
    var Y = document['edy'];
    var src;
    src = new Y.DataSource.Get({
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
        cmd_str  : 'FDATA',
        req      : file,
    });
    src.sendRequest({
            request : request,
            callback : {
                    success: function (e) {
                            var res = e.response.results;
                            setAceEditorText(t, res[0], line);
                    },
                    failure: function (e) {
                            setAceEditorText(t, e.error.message, 1);
                            alert(e.error.message);
                    },
            },
    });
}

function ed_show_file_line_new(file, line) {
    var ed_tv = document['ed_tv'];
    var fp = file.split('/');
    var fname = fp[fp.length - 1];
    var content2 =
                 '<table style="position:relative; width: 100%; height: 85%;">' +
                 '<tr style="vertical-align: top;">' +
                 '<td style="position:relative; width: 10%;">' +
                 '              <div id="ctTbl" style="position:relative; width: 100%; "> </div>' +
                 '</td>' +
                 '<td style="position:relative; width: 80%; height: 100%;">' +
                 '      <div id="aceEditor" style="background-color: white; position:relative; width: 100%; height: 100%;"> </div>' +
                 '</td>' +
                 '</tr>' +
                 '</table>';
    var content =
                 '<table style="position:relative; width: 100%; height: 85%;">' +
                 '<tr style="vertical-align: top;">' +
                 '<td style="position:relative; width: 25%;">' +
                 '              <div id="ctTbl"> </div>' +
                 '</td>' +
                 '<td style="position:relative; width: 75%; height: 100%;">' +
                 '      <div id="aceEditor" style="background-color: white; position:relative; width: 100%; height: 100%;"> </div>' +
                 '</td>' +
                 '</tr>' +
                 '</table>';
    var input = {
        label: fname,
        content : content,
    }
    ed_tv.add(input);
    found = ed_tv.size() - 1;
    t = ed_tv.item(found);
    t['ed_file'] = file;
    t['ed_line'] = line;
    ed_tv.selectChild(found);

    show_ace_editor_new(t, file, line)
    show_ctags_new(t, file);
}

function ed_show_file_line(file, line) {
    //confirm('ed_show_file_line ' + file + ':' + line);
    var edf = document['edf'];
    //edf.sayHi();
    var ed_tv = document['ed_tv'];
    //confirm(ed_tv.size());
    var found = -1;
    for (i = 0; i < ed_tv.size(); i++) {
        t = ed_tv.item(i);
        if (t['ed_file'] == file) {
            found = i;
            break;
        }
    }
    if (found == -1) {
        ed_show_file_line_new(file, line);
    } else {
        ed_tv.selectChild(found);
        var cbox = t.get('panelNode');
        var editor = cbox['a_ed'];
        editor.gotoLine(line);
        editor.focus();
    }
}

YUI().use('datasource-get', 'datasource-jsonschema',
          'node-event-delegate', 'event-key',
          'tabview', 'escape', 'plugin', 'node', function(Y) {

    document['edy'] = Y;

    var EdAddable = function(config) {
        EdAddable.superclass.constructor.apply(this, arguments);
    };

    EdAddable.NAME = 'addableTabs';
    EdAddable.NS = 'addable';

    Y.extend(EdAddable, Y.Plugin.Base, {
//         ADD_TEMPLATE: '<li class="yui3-tab" title="add a tab">' +
//                     '<a class="yui3-tab-label yui3-tab-add">+</a></li>',

        initializer: function(config) {
            var tabview = this.get('host');
            tabview.after('render', this.afterRender, this);
            tabview.get('contentBox').delegate('click', this.onAddClick, '.yui3-tab-add', this);

            tabview.after('tab:render', this.afterTabRender, this);
            //tabview.after('tab:widget:contentUpdate', this.afterTabRender, this);
            tabview.after('selectionChange', function() {
                var t = tabview.get('activeDescendant');
                if (t) {
                    focusAceEditor(t.get('panelNode'));
                }
            });

            tabview.get('listNode').setStyle('border-width', '0 0 0px');
            tabview.get('panelNode').setStyle('padding', '0em');
        },

        afterRender: function(e) {
            var tabview = this.get('host');
            //tabview.get('contentBox').one('> ul').append(this.ADD_TEMPLATE);
        },

        onAddClick: function(e) {
        },

        afterTabRender: function(e) {
            //e.stopPropagation();
            var t = e.target;
            tv = this.get('host');

            createAceEditor(t);
            createCtTable(t);
        }
    });

    var EdRemoveable = function(config) {
        EdRemoveable.superclass.constructor.apply(this, arguments);
    };

    EdRemoveable.NAME = 'removeableTabs';
    EdRemoveable.NS = 'removeable';

    Y.extend(EdRemoveable, Y.Plugin.Base, {
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

    var ed_tv= new Y.TabView({
        children: [],
        plugins: [EdAddable, EdRemoveable]
    });

    ed_tab_list_pop_dlg_setup(function(cargs) {
        if (cargs.choice == 'close_all') {
            ed_tv.removeAll();
        }
    });
    ed_pop_dlg_setup(function(cargs) {
        qry_dlg_show(start_query, cargs.choice);
    });

    ed_tv.after('heightChange',    ed_tv_resize);
    ed_tv.after('widthChange',     ed_tv_resize);
    ed_tv.after("selectionChange", function(e) {
        Y.later(0, null, ed_tv_resize_sel, e);
    });

    document['ed_tv'] = ed_tv;
//     ed_tv.set('height', 400);
//     ed_tv.set('width',  400);
    ed_tv.render('#edTabs');

    function queryAction(e) {
        e.stopPropagation();
        confirm('queryAction');
        qry_dlg_show();
    }
    var key1 = 'm+ctrl';
    //confirm(key);
    Y.one('#edTabs').on('key', queryAction, key1);

    var key2 = ']+ctrl';
    function qdefAction(e) {
        confirm('qdefAction');
        var word = ed_get_cur_word();
        if (word) {
            if (word.length < 3) {
               qry_dlg_show();
            } else {
                start_query(word, 'DEF');
            }
        }
    }
    Y.one('#edTabs').on('key', qdefAction, key2);
});
