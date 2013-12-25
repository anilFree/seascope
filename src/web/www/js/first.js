
var url = 'http://' + sinfo.host;
if (sinfo.port != 80) {
    url = url + ':' + sinfo.port
}
url = url + '/q';
sinfo.url = url;

// confirm(url);
document['server_info'] = sinfo;









function filter_table(dt, fargs)
{
    var col = fargs.col;
    var is_regex      = (fargs.opt.indexOf('regex') != -1);
    var is_negate     = (fargs.opt.indexOf('negate') != -1);
    var is_ignorecase = (fargs.opt.indexOf('ignorecase') != -1);

    var pat = fargs.symbol;
    if (is_regex) {
       pat = new RegExp(pat, is_ignorecase ? 'i' : '');
    }

    var row_list = [];
    var num_rows = dt.getNumberOfRows();
    for (var row = 0; row < num_rows; row++) {
        var val = dt.getValue(row, col);
        var found;
        if (is_regex) {
            found = pat.test(val);
        } else {
            if (is_ignorecase) {
                found = (val.toUpperCase().search(pat.toUpperCase()) != -1);
            } else {
                found = (val.search(pat) != -1);
            }
        }

        if (is_negate) {
            found = !found;
        }
        if (!found) {
            row_list.push(row);
        }
    }
    return row_list;
}


function to_query_string(obj) {
    var parts = [];
    for (var i in obj) {
        if (obj.hasOwnProperty(i)) {
            parts.push(encodeURIComponent(i) + "=" + encodeURIComponent(obj[i]));
        }
    }
    return parts.join("&");
}

function send_my_request(Y, resultListLocator, success_func, failure_func ) {
                var src = new Y.DataSource.Get({
                    source : document['server_info'].url,
                });
                src.plug(Y.Plugin.DataSourceJSONSchema, {
                        schema : {
                                resultListLocator : resultListLocator,
                        }
                });
                src.sendRequest({
                        request : request,
                        callback : {
                                success: success_func,
                                failure: failure_func,
                        },
                });
}
