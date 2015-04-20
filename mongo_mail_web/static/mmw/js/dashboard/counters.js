/*
 * Requires:
 * - https://github.com/janl/mustache.js
 * - https://github.com/HubSpot/humanize
 * - jQuery
 */

(function(){
	
	"use strict";

	function Counters(options, settings){
		this.url = options.url;
		this.period = options.period || 'last-month';
		this.timer = options.timer;
		
		this.interval;
		
		if (!this.timer || this.timer === 0){
			this.timer = null;
		} else {
			this.start();
		}
		
    	this.settings = $.extend({}, Counters.defaults, settings || {});
    	Mustache.parse(this.settings.template);
		
		this.data;
		
		this.load();
		
		return this;
	}
	
	Counters.defaults = {
		enable_select_field: true,
		enable_html_table: true,
		fields: [
		    'mail_count',
		    'mail_in',
			'mail_out',
			'clean',
			'spam',
			'virus',
			'banned',
			'bounce',
			'total_size'
		],
		metric_label: {
			mail_count: "All",
			mail_in: "Incoming",
			mail_out: "Outgoing",
			clean: "Clean",
			spam: "Spam",
			virus: "Infected",
			banned: "Banned",
			bounce: "Bounced",
			total_size: "Size"
		},
    	periods: {
    		'today': "Today",
    		'yesterday': "Yesterday",
    		'last-24-hours': "Last 24 hours",
    		'last-week': "Last Week",
    		'last-month': "Last Month",
    		'last-year': "Last year"
    	},					
		'mail_count_label_id': 'label_all_messages',
		'total_size_label_id': 'label_size_messages',
		'spam_label_id': 'label_spam_messages',
		'virus_label_id': 'label_virus_messages',
		'banned_label_id': 'label_banned_messages',
		'bounce_label_id': 'label_bounce_messages',
		//TODO: 'template': '<tr><td>{{ metric }}</td><td>{{ current }}</td><td>{{ previous }}</td><td>{{ diff }} %</td></tr>',
		'template': '<tr><td>{{ metric }}</td><td>{{ current }}</td><td>{{ previous }}</td></tr>',
    	'label_table_placeholder': "#label_table",
    	'label_period_placeholder': "#label_period_choice",
	};
	
    Counters.prototype.get_url = function() {
		return this.url + '?period=' + this.period;
    };
    
    Counters.prototype.bytesToSize = function(bytes) {
        var sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        if (bytes == 0) return 'n/a';
        var i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
        if (i == 0) return bytes + ' ' + sizes[i]; 
        return (bytes / Math.pow(1024, i)).toFixed(1) + ' ' + sizes[i];
    };
    
    Counters.prototype.start = function() {
    	var that = this;
		var _timer = this.timer;
		//bug setInterval and this
		this.interval = setInterval(function() {
	    	that.load.call(that);
	    }, _timer);
    };
    
    Counters.prototype.stop = function() {
    	clearInterval(this.interval);
    };

    Counters.prototype.select_period_html = function(placeholder) {
    	//'#label_period_choice',
    	var _placeholder = placeholder || this.settings.label_period_placeholder;
    	var select_field = [];
    	var id = 'label_period_select';
    	select_field.push('<select id="' + id + '">');
        for(var period in this.settings.periods){
            var period_txt = this.settings.periods[period];
    		if(period == this.period){
    			select_field.push('<option selected="selected" value="'+ period +'">'+ period_txt +'</option>');    			
    		} else {
    			select_field.push('<option value="'+ period +'">'+ period_txt +'</option>');
    		}
        };
        
        $(_placeholder).html(select_field.join('\n'));
        
        var counter = this;
        
        // Change period with select field
        $('#' + id).on('change', function() {
            var value = $(this).val();
            counter.period = value;
            counter.load();
        });
    	
    };
    
    Counters.prototype.update_html_table = function(){
        var cumul_table = $(this.settings.label_table_placeholder);
        var data = this.data;
        var counter = this;
        var table = [];
        table.push('<table id="period_table" class="table table-hover table-condensed table-striped">');
        //table.push('<thead><th>Metric</th><th>Current</th><th>Previous</th><th>Variation</th></thead><tbody>');
        table.push('<thead><th>Metric</th><th>Current</th><th>Previous</th></thead><tbody>');
        $.each(this.settings.fields, function(i, key){
        	var values = {
                    metric: counter.settings.metric_label[key],
                    current: data.data[key],
                    previous: data.previous_data[key],
                    diff: Math.round(data.diff_data[key]),
            };
        	if (key == 'total_size'){
        		values.current = counter.bytesToSize(data.data[key]);
                values.previous = counter.bytesToSize(data.previous_data[key]);
        	} else {
        		values.current = Humanize.formatNumber(data.data[key]);
                values.previous = Humanize.formatNumber(data.previous_data[key]);
        	};
            var rendered = Mustache.render(counter.settings.template, values);
            table.push(rendered);

        });
        table.push('</tbody></table>');
        cumul_table.html(table.join('\n'));
    };

    Counters.prototype.update_counters = function(data) {
    	this.data = data;
    	// thousand : ','
    	// decimal : '.'
    	//Humanize.formatNumber(this.data.data.mail_count, ',', '.')
    	$('#'+this.settings.mail_count_label_id).text(Humanize.formatNumber(this.data.data.mail_count));
    	//$('#'+this.settings.total_size_label_id).text(this.bytesToSize(this.data.data.total_size));
    	$('#'+this.settings.total_size_label_id).text(Humanize.fileSize(this.data.data.total_size));
    	
    	$('#'+this.settings.spam_label_id).text(Humanize.formatNumber(this.data.data.spam));
    	$('#'+this.settings.virus_label_id).text(Humanize.formatNumber(this.data.data.virus));
    	$('#'+this.settings.banned_label_id).text(Humanize.formatNumber(this.data.data.banned));
    	$('#'+this.settings.bounce_label_id).text(Humanize.formatNumber(this.data.data.bounce));
    	
    	if (this.settings.enable_html_table)
    		this.update_html_table();
    	
    	if (this.settings.enable_select_field)
    		this.select_period_html();
    	
    };

    Counters.prototype.change_period = function(new_period) {
    	this.period = new_period;
    	this.load();
    };
    
    Counters.prototype.load = function(options) {
    	    	
    	var counter = this;
    		
	    $.ajax({
	        url: counter.get_url(),
	        cache: false,
	        dataType: "json",
	        complete: function(jqXHR, textStatus){
	        	if (textStatus == "success"){
	        		counter.update_counters(jqXHR.responseJSON);
	        	}
	        }
	    });
	    
    };
	   
	function counters(options, settings){
		return new Counters(options, settings);
	}
	
	window.CountersClass = Counters;
	window.Counters = counters;
    
})();
	
	