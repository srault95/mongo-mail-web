/**
 * Requires:
 * - http://www.highcharts.com/
 * - jQuery
 */

(function () {	
	
	"use strict";
    
	function MessageChart(options, settings){
		this.url = options.url;
		this.placeholder = $(options.placeholder);
		this.period = options.period || 'last-month';
		this.step = options.step || 'ymd';
		this.height = options.height || 450;
		this.width = options.width || 900;
		this.timer = options.timer;
		
		this.interval;
		
		if (!this.timer || this.timer === 0){
			this.timer = null;
		} else {
			this.start();
		}
		
		this.plot = null;

		this.settings = $.extend({}, MessageChart.defaults, settings);
		this.load();
		
		return this;
	}

	MessageChart.defaults = {
		series: {
		   mail_count: {
		       name: 'Messages',
		       data: []
		   }, 
		   mail_in: {
		       name: 'Incoming Messages',
		       data: []
		   }, 
		   mail_out: {
		       name: 'Outgoing Messages',
		       data: []
		   }, 
		   clean: {
		       name: 'Clean',
		       data: []
		   }, 
		   spam: {
		       name: 'Spam',
		       data: []
		   },
		   virus: {
		       name: 'Virus',
		       data: []
		   },
		   banned: {
		       name: 'Banned',
		       data: []
		   },
		   bounce: {
		       name: 'Bounced',
		       data: []
		   }
		},
    	periods: {
    		'today': "Today",
    		'yesterday': "Yesterday",
    		'last-24-hours': "Last 24 hours",
    		'last-week': "Last Week",
    		'last-month': "Last Month",
    		'last-year': "Last year"
    	},
    	tickInterval: {
            y: 24 * 3600 * 1000 * 30,  //30 days
            ym: 24 * 3600 * 1000 * 30, //30 days
            ymd: 24 * 3600 * 1000 * 2, // 2 days
            ymdh: 2 * 3600 * 1000 // 2 hours
        },
    	highstock_options: {
    		legend: {
    			enabled: true
    		},
            rangeSelector : {
                buttons: [{
                    type: 'hour',
                    count: 1,
                    text: '1h'
                }, {
                    type: 'day',
                    count: 1,
                    text: '1d'
                }, {
                    type: 'month',
                    count: 1,
                    text: '1m'
                }, {
                    type: 'year',
                    count: 1,
                    text: '1y'
                }, {
                    type: 'all',
                    text: 'All'
                }],
                //inputEnabled: false, // it supports only days
                selected : 4 // all
            },
            xAxis : {
            	//minRange: 3600 * 1000 // one hour
            },
            yAxis: {            	
                labels: {
                    formatter: function () {
                        return (this.value > 0 ? ' + ' : '') + this.value;// + '%';
                    }
                },
                //floor: 0,
                plotLines: [{
                    value: 0,
                    width: 2,
                    color: 'silver'
                }]
            },
            plotOptions: {
                series: {
                    compare: 'value' //percent
                }
            },
            tooltip: {
                //pointFormat: '<span style="color:{series.color}">{series.name}</span>: <b>{point.y}</b> ({point.change}%)<br/>',
                pointFormat: '<span style="color:{series.color}">{series.name}</span>: <b>{point.y}</b> ({point.change})<br/>',
                valueDecimals: 0
            },
            
            series: []
        },
    	highcharts_options: {
            xAxis: {
                type: 'datetime',
                //minRange: 24 * 3600 * 1000, // 1 days
                //min: data.first_time_timestamp,
                //minRange: chart.settings.tickInterval[chart.step],
                //max: data.last_time_timestamp,
                //minTickInterval: chart.settings.tickInterval[chart.step],
                //endOnTick: true,
                //minTickInterval: 0,
                /*
                dateTimeLabelFormats: {
                    month: '%e. %b',
                    year: '%b'
                },*/
                //pointStart: Date.UTC(2010, 0, 1),
                //pointInterval: 24 * 3600 * 1000 // one day                
                title: {
                    text: 'Date'
                }                
            },
            yAxis: {
                title: {
                    text: 'Count'
                }
            },            
            title: {
                text: 'Statistics of Messages'
            }            
        },
    	label_period_placeholder: "#metric_per_period_field",
    	label_period_title: "#metric_per_period_title"
    };

    // Generate html select field for period choice
    // TODO: to settings and class
    MessageChart.prototype.select_period_html = function() {
    	var select_field = [];
    	var id = 'metric_per_period_period';
    	select_field.push('<select id="' + id + '">');
    	
        for(var period in this.settings.periods){
            var period_txt = this.settings.periods[period];
    		if (period == this.period){
    			select_field.push('<option selected="selected" value="'+ period +'">'+ period_txt +'</option>');    			
    		} else {
    			select_field.push('<option value="'+ period +'">'+ period_txt +'</option>');
    		}
        }
        
        $(this.settings.label_period_placeholder).html(select_field.join('\n'));
        
        var chart = this;
        
        // Change period with select field
        $('#' + id).on('change', function() {
            var value = $(this).val();
            chart.change_period(value);
        });
    	
    };

    MessageChart.prototype.start = function() {
    	var that = this;
		var _timer = this.timer;
		//bug setInterval and this
		this.interval = setInterval(function() {
	    	that.load.call(that);
	    }, _timer);
    };
    
    MessageChart.prototype.stop = function() {
    	/*
    	    $("#metric_per_period_stop").on('click', function(e){
    	    	e.preventDefault();
    	    	chart1.stop();
    	    });

    	    $("#metric_per_period_start").on('click', function(e){
    	        e.preventDefault();
    	        chart1.start();
    	    });

    	*/    	
    	clearInterval(this.interval);
    };

    MessageChart.prototype.set_period = function(new_period) {
    	
    	this.period = new_period;
    	
    	switch (new_period) {
        	case 'today':
        		this.step = "ymdh";
        		break;
        	case 'last-24-hours':
        		this.step = "ymdh";
        		break;
        	case 'last-week':
        		this.step = "ymd";
        		break;
        	case 'last-month':
        		this.step = "ymd";
        		break;
        	case 'last-year':
        		this.step = "ym";
        		break;
    	}
    };
    
    MessageChart.prototype.change_period = function(new_period) {
    	this.set_period(new_period);
    	this.load(null, true);
    };
    
    MessageChart.prototype.update = function(data, force) {

    	var series = [];
    	
    	var chart = this;
    	
    	this.settings.series.mail_count.data = [];
    	this.settings.series.mail_in.data = [];
    	this.settings.series.mail_out.data = [];
    	
    	this.settings.series.clean.data = [];
    	this.settings.series.spam.data = [];
    	this.settings.series.virus.data = [];
    	this.settings.series.banned.data = [];
    	this.settings.series.bounce.data = [];

    	$.each(data.data, function(i,item) {
    		//chart.settings.series.mail_count.data.push([item.date, item.mail_in]);
    		//console.log(moment(item.date).utc().format('LLL'));
    		chart.settings.series.mail_count.data.push([item.date, item.mail_count]);
    		chart.settings.series.mail_in.data.push([item.date, item.mail_in]);
    		chart.settings.series.mail_out.data.push([item.date, item.mail_out]);

    		chart.settings.series.clean.data.push([item.date, item.clean]);
    		chart.settings.series.spam.data.push([item.date, item.spam]);
    		chart.settings.series.virus.data.push([item.date, item.virus]);
    		chart.settings.series.banned.data.push([item.date, item.banned]);
    		chart.settings.series.bounce.data.push([item.date, item.bounce]);
        });
    	
    	series.push(this.settings.series.mail_count);
    	series.push(this.settings.series.mail_in);
    	series.push(this.settings.series.mail_out);
    	/*
    	series.push(this.settings.series.clean);
    	series.push(this.settings.series.spam);
    	series.push(this.settings.series.virus);
    	series.push(this.settings.series.banned);
    	series.push(this.settings.series.bounce);
    	*/
    	
    	/*
    	//Highchart
    	this.settings.highcharts_options.series = series;
    	this.settings.highcharts_options.xAxis.tickInterval = chart.settings.tickInterval[chart.step];
		this.plot = this.placeholder.highcharts(this.settings.highcharts_options);
		*/    	

    	//HighStock
    	this.settings.highstock_options.series = series;
    	this.plot = this.placeholder.highcharts('StockChart', this.settings.highstock_options);    	
    	
    	var title = "<span>From " + moment(data.first_time).utc().format('LLL') + " To " + moment(data.last_time).utc().format('LLL') + "</span>";
    	//console.log(data.first_time);
    	//2015-03-17T01:36:29.233000+00:00
    	//From 2015-03-17T02:36:39+01:00 : temps corriger selon le browser
    	$(this.settings.label_period_title).empty();
    	$(this.settings.label_period_title).html(title);
    	
        //TODO: settings: this.select_period_html();
    	
    };
    
    MessageChart.prototype.load = function(options, force) {
    	
    	var chart = this;
    	chart.set_period(this.period);
    		
	    $.ajax({
	        url: chart.get_url(),
	        cache: false,
	        dataType: "json",
	        complete: function(jqXHR, textStatus){
	        	if (textStatus == "success"){
	        		chart.update(jqXHR.responseJSON, force);
	        	}
	        }
	    });
    };

    MessageChart.prototype.get_url = function() {
		return this.url + '?period=' + this.period + '&step=' + this.step;
    };
    
	function messageChart(options, settings){
		return new MessageChart(options, settings);
	}
	
	window.MessageChartClass = MessageChart;
	window.MessageChart = messageChart;

})();

