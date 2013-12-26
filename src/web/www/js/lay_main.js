YUI().use('node',
          'yui2-utilities',
          'yui2-layout',
          'yui2-resize',
          'yui2-menu',
          function(Y) {

    Y.one('body').addClass('yui-skin-sam');

    //This will make your YUI 2 code run unmodified
    var YAHOO = Y.YUI2;


    var Event = YAHOO.util.Event;

    Event.onDOMReady(function() {
        var layout = new YAHOO.widget.Layout({
            units: [
                { position: 'top',    body: 'top1',    height: 34,  resize: false, scroll: true, gutter: '0px' },
                { position: 'center', body: 'edTabs',                            scroll: true, gutter: '5px' },
                { position: 'right',  body: 'fvTabs',  width: 300,  resize: true, scroll: true, gutter: '5px' },
                { position: 'bottom', body: 'resTabs', height: 300, resize: true, scroll: true, gutter: '5px' },
            ]
        });
        layout.on('render', function() {
        });
        layout.render();
        document['lay_main'] = layout;

        function cu_size_change(e) {
            var x = 25;
            var node = layout.getUnitByPosition('center');
            var h = node.get('height');
            var w = node.get('width');
            var ed_tv = document['ed_tv'];
            ed_tv.set('height', h - x);
            ed_tv.set('width',  w - x - 2);

        }
        function bu_size_change(e) {
            var x = 25;
            var h2 = layout.getUnitByPosition('bottom').get('height');
            //var w2 = layout.getUnitByPosition('bottom').get('width');
            //var w2 = document.documentElement.clientWidth;
            var w2 = YAHOO.util.Dom.getViewportWidth();
            var res_tv = document['res_tv'];
            res_tv.set('height', h2 - x);
            res_tv.set('width',  w2 - x - 2);
        }
        function ru_size_change(e) {
            var x = 25;
            var h2 = layout.getUnitByPosition('right').get('height');
            var w2 = layout.getUnitByPosition('right').get('width');
            //var w2 = document.documentElement.clientWidth;
            var fv_tv = document['fv_tv'];
            fv_tv.set('height', h2 - x);
            fv_tv.set('width',  w2 - x - 2);
        }

        var bu = layout.getUnitByPosition('bottom');
        var ru = layout.getUnitByPosition('right');
        bu.on('heightChange', function(e) {
            cu_size_change(e);
            ru_size_change(e);
            bu_size_change(e);
        }); 
        ru.on('widthChange',  function(e) {
            cu_size_change(e);
            ru_size_change(e);
        }); 

        var e = null;
        cu_size_change(e);
        ru_size_change(e);
        bu_size_change(e);


        plist_dlg_show(function(pargs) {
            document['project'] = pargs.project;
            Y.one('#project_name').setHTML(pargs.project);

            flist_query();

//             var qargs = {
//             qtype  : 'REF',
//             symbol : 'query',
//             opt    : [],
//             };
//             start_query(qargs);
        });

    });

    function g_do_resize(e) {
        confirm('g_do_resize');
        var e = null;
        cu_size_change(e);
        ru_size_change(e);
        bu_size_change(e);
    }
    Y.after('windowresize', g_do_resize);

});
