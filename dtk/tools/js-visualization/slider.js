var update_slider;

function load_slider(ts_input_file, slider_id, params, target_container, comm_msg)
{
	
	var target_container = typeof target_container !== 'undefined' ? target_container : "body";
	
	var time_idx;
	if(params.hasOwnProperty('time_idx'))
		time_idx = params.time_idx;
	else
		time_idx = false;
	
	// set local map time if provided
	var time = 0;
	if(time_idx)
		time = time_idx;
	else
	{
		// check if global_time_idx is defined by coms.js (e.g. comms.js was imported)
		if(typeof global_time_index !== 'undefined')
			time = global_time_idx;			
	}
	
	var margin = {top: 0, right: 50, bottom: 0, left: 50},
    width = 960 - margin.left - margin.right,
    height = 50 - margin.bottom - margin.top;

	var xScale = d3.time.scale()
    .range([0, width]);

	var xScaleOrdinal = d3.scale.linear()
					.range([0, width]);
	
	var parseDate = d3.time.format("%Y%m%d").parse;
	
	var slider_container = d3.select(target_container).append("div")
		.attr("id","slider_" + slider_id)
		.attr("class", "slider_container");

	var svg = slider_container.append("svg")
		.attr("width", width + margin.left + margin.right)
		.attr("height", height + margin.top + margin.bottom)
		.append("g")
			.attr("transform", "translate(" + margin.left + "," + margin.top + ")")
			.attr("id", slider_id);	

	var format = d3.time.format('%b %Y');
	
	var brush = d3.svg.brush()
    .x(xScaleOrdinal)
    .extent([0, 0])
	
	var slider = svg.append("g")
    .attr("class", "slider")
    .call(brush);
	
	var handle = slider.append("circle")
    .attr("class", "slider-handle")
    .attr("id", slider_id + "-slider-brush")
    .attr("transform", "translate(0," + height / 2 + ")")
    .attr("emitted","false")
    .attr("r", 9);
	
	d3.tsv(ts_input_file, function(error, data) {
				  
		  var current_date = 0;
		  var dates_idx  = [];
		  data.forEach(function(d,i) { // Make every date in the tsv data a javascript date object format
		    d.date = parseDate(d.date);
		    dates_idx.push(i);
		    if(i == time)
		    {
		    	current_date = d.date;
		    }
		  });
	
		  xScaleOrdinal.domain(d3.extent(dates_idx, function(d) { return d; }));
		  xScale.domain(d3.extent(data, function(d) { return d.date; }));
		  xScale.clamp(true);
		  
		  brush.x(xScaleOrdinal).on("brush", brushed);
		  
		  //alert(xScale.domain());
			svg.append("g")
			    .attr("class", "x slider-axis")
			    .attr("transform", "translate(0," + height / 2 + ")")
			    .call(d3.svg.axis()
			      .scale(xScale)
			      .orient("bottom")
			      .tickFormat(function(d){ return format(d); })
			      .tickSize(0)
			      .tickPadding(12))
			  .select(".slider-domain")
			  .select(function() { return this.parentNode.appendChild(this.cloneNode(true)); })
			    .attr("class", "slider-halo");
			
			
			
			slider.selectAll(".extent,.resize")
			    .remove();
			
			slider.select(".background")
			    .attr("height", height);
			
			
			
			slider
			    .call(brush.event)
			  .transition() 
			    .duration(750)
			    .call(brush.extent([time, time]))
			    .call(brush.event);
			
			function brushed() {
			  var value = brush.extent()[0];
			
			  if (d3.event.sourceEvent) { // not a programmatic event
			    value = xScaleOrdinal.invert(d3.mouse(this)[0]);
			    //alert(value);
			    brush.extent([value, value]);
			  }
			  
			  handle.attr("cx", xScaleOrdinal(value));
			  
			  comm_msg = typeof comm_msg !== 'undefined' ? comm_msg : false;
				
			  if (typeof(trigger_emit) == "function" && typeof(parse_comm_msg) == "function" && comm_msg !== false && comm_blacklist.indexOf(d3.select(slider_id + "-slider-brush")) == -1)
			  {
				  
				// parse comm_msg and, if requested, bind data attributes from d to comm_msg
				var d = {"time":value};
				
				comm_msg = parse_comm_msg(comm_msg, d);
				
				// emit comm_msg
				trigger_emit(d3.select("#" + slider_id + "-slider-brush").node(), comm_msg);
			  }
			}
	
	});

	update_slider = function(slider_id, date_idx)
	{
		handle.attr("cx", xScaleOrdinal(date_idx));
	}
}

