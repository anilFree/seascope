function res_tbl_pop_dlg_setup(cb_func) {
    YUI().use("panel", "gallery-contextmenu-view", function (Y) {

        var pmenu = new Y.ContextMenuView({
            // Set what Node should accept the right clicks, and the target on that node ...
            trigger: {
                node:   Y.one('#resTabs'),
                target:  'td'
            },
            // Define the pop-up menu contents
            menuItems: [
                { label: 'Filter',      value: 'filter'      },
                { label: 'Show All',    value: 'show_all'    },
                //{ label: '<hr/>',       value: null          },
                //{ label: 'Remove Item', value: 'remove_item' },
            ],
        });
        pmenu['cb_func'] = cb_func;

        function menu_choice(e) {
//             e.stopPropagation();
//            e.preventDefault();
            var td    = this.get('contextTarget');
            var row    = td.ancestor().get('sectionRowIndex') - 1;
            var col    = td.get('cellIndex');
            var choice = e.newVal.menuItem.value;

            var cb_func = pmenu['cb_func'];
            if (!cb_func) {
                return;
            }
            var cargs = {
                choice : choice,
                row    : row,
                col    : col,
            };
            cb_func(cargs);
        }

        pmenu.after('selectedMenuChange', menu_choice);
    });
}

function flist_tbl_pop_dlg_setup(cb_func) {
    YUI().use("panel", "gallery-contextmenu-view", function (Y) {

        var pmenu = new Y.ContextMenuView({
            // Set what Node should accept the right clicks, and the target on that node ...
            trigger: {
                node:   Y.one('#fvTabs'),
                target:  'td'
            },
            // Define the pop-up menu contents
            menuItems: [
                { label: 'Filter',      value: 'filter'      },
                { label: 'Show All',    value: 'show_all'    },
                //{ label: '<hr/>',       value: null          },
                //{ label: 'Remove Item', value: 'remove_item' },
            ],
        });
        pmenu['cb_func'] = cb_func;

        function menu_choice(e) {
            var td    = this.get('contextTarget');
            var row    = td.ancestor().get('sectionRowIndex') - 1;
            var col    = td.get('cellIndex');
            var choice = e.newVal.menuItem.value;

            var cb_func = pmenu['cb_func'];
            if (!cb_func) {
                return;
            }
            var cargs = {
                choice : choice,
                row    : row,
                col    : col,
            };
            cb_func(cargs);
        }

        pmenu.after('selectedMenuChange', menu_choice);
    });
}

function ed_pop_dlg_setup(cb_func) {
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
    var menu_items = [];
    var is_disabled = false;
    for (var i = 0; i < qry_arr.length; i++) {
        v = qry_arr[i];
        if (v[0] == 'CTREE') {
            is_disabled = true;
        }
        if (is_disabled) {
//             menu_items.push({
//                 class : "disabled",
//                 label : v[1],
//                 value : null,
//             })
        } else {
            menu_items.push({
                label : v[1],
                value : v[0],
            })
        }
    }

    YUI().use("panel", "gallery-contextmenu-view", function (Y) {

        var pmenu = new Y.ContextMenuView({
            // Set what Node should accept the right clicks, and the target on that node ...
            trigger: {
                node:   Y.one('#edTabs'),
                target:  '#aceEditor'
            },
            // Define the pop-up menu contents
            menuItems: menu_items,
        });
        pmenu['cb_func'] = cb_func;

        function menu_choice(e) {
            var choice = e.newVal.menuItem.value;

            var cb_func = pmenu['cb_func'];
            if (!cb_func) {
                return;
            }
            var cargs = {
                choice : choice,
            };
            cb_func(cargs);
        }

        pmenu.after('selectedMenuChange', menu_choice);
    });
}

function res_tab_list_pop_dlg_setup(cb_func) {
    YUI().use("panel", "gallery-contextmenu-view", function (Y) {

        var pmenu = new Y.ContextMenuView({
            // Set what Node should accept the right clicks, and the target on that node ...
            trigger: {
                node:   Y.one('#resTabs'),
                target:  '.yui3-tabview-list '
            },
            // Define the pop-up menu contents
            menuItems: [
                { label: 'Close All',   value: 'close_all', confirm: true   },
            ],
        });
        pmenu['cb_func'] = cb_func;

        function menu_choice(e) {
            var choice = e.newVal.menuItem.value;
            if (e.newVal.menuItem.confirm && !confirm('Close all tabs?')) {
                return;
            }
            var cb_func = pmenu['cb_func'];
            if (!cb_func) {
                return;
            }
            var cargs = {
                choice : choice,
            };
            cb_func(cargs);
        }

        pmenu.after('selectedMenuChange', menu_choice);
    });
}

function ed_tab_list_pop_dlg_setup(cb_func) {
    YUI().use("panel", "gallery-contextmenu-view", function (Y) {

        var pmenu = new Y.ContextMenuView({
            // Set what Node should accept the right clicks, and the target on that node ...
            trigger: {
                node:   Y.one('#edTabs'),
                target:  '.yui3-tabview-list '
            },
            // Define the pop-up menu contents
            menuItems: [
                { label: 'Close All',   value: 'close_all', confirm: true   },
            ],
        });
        pmenu['cb_func'] = cb_func;

        function menu_choice(e) {
            var choice = e.newVal.menuItem.value;
            if (e.newVal.menuItem.confirm && !confirm('Close all tabs?')) {
                return;
            }
            var cb_func = pmenu['cb_func'];
            if (!cb_func) {
                return;
            }
            var cargs = {
                choice : choice,
            };
            cb_func(cargs);
        }

        pmenu.after('selectedMenuChange', menu_choice);
    });
}

