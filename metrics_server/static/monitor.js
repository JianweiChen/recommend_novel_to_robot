var query_result_map = Object;
function render_chart(rsp_data) {
    var xAxis = {
        type: 'linear',
        min: 0,
        text: 'period',
        minRange: 20,
        maxRange: 20
     };
    var yAxis = {
        title: {
           text: 'Value'
        },
        min: 0
    };
    var legend = {
        enabled: true 
    };
    var series_data = [];
    var need_fresh = false;
    for (var query in rsp_data) {
        var xy_data = [];
        var query_data = rsp_data[query];
        var type = query_data['type']
        // console.log(query_result_map[query]);
        j1 = JSON.stringify(query_result_map[query])
        j2 = JSON.stringify(query_data)
        if (j1 != j2) {
            query_result_map[query] = query_data
            need_fresh = true;
        }
        for (var i=0; i<query_result_map[query]['x_data'].length; i++) {
            xy_data.push([
                query_result_map[query]['x_data'][i],
                query_result_map[query]['y_data'][i],
            ])
        }
        var query_series_data = {
            "name": query,
            "data": xy_data
        };
        series_data.push(query_series_data);
    }
    // draw
    if (need_fresh) {
        var json = {};
        json.title = 'ActionMachine';
        var chart = {
            animation: false
        }
        var plotOptions = {
            series: { animation: false }
        }
        json.legend = legend;
        json.xAxis = xAxis;
        json.yAxis = yAxis;  
        json.series = series_data;
        json.chart = chart;
        json.plotOptions = plotOptions;
        $('#container').highcharts(json);
    }
    
    
}


// 每500毫秒请求一次metrics_server时使用的函数
function check() {
    var use_query = $("#use_query").text().trim();
    var metrics_group_name = $("#metrics_group_name").text().trim();
    var auto_refresh = $("#switch_auto_refresh").text()=="Auto Refresh is ON"? true: false;
    if (!auto_refresh) return;
    $.ajax({
        url:"/query?metrics_group_name="+metrics_group_name + "&use_query="+use_query,
        success: function(message) {
            var rsp_data = JSON.parse(message);
            // debug:
            // console.log("/query?metrics_group_name="+metrics_group_name + "&use_query="+use_query);
            // console.log(message);
            render_chart(rsp_data);
        }
    })
}
$("#clear_button").click(function(e) {
    $.ajax({
        url:"/clear"
    })
})
// 设置定时器
$().ready(function(){
    var time = setInterval(function() {
        check();
    }, 500);
})

$("#switch_auto_refresh").click(function() {
    var text = $("#switch_auto_refresh").text();
    if (text == 'Auto Refresh is ON') {
        $("#switch_auto_refresh").text("Auto Refresh is OFF");
    } else {
        $("#switch_auto_refresh").text("Auto Refresh is ON");
    }
});