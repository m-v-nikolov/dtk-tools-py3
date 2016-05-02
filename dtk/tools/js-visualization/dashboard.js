var gazeteer_select_model = "unselect";
var gazeteer_select = "unselect";
//var node_select = "80202_5";
var node_select = "unselect";
var time_idx_select = 6*365 + 160;
var params_select = []; //{className : "unselect", fill : [], "toggled":false};

function load_dashboard(gazetteer_file, gazetteer_header_file, map_data_file)
{
	this.svg_maps = d3.select(".resourcecontainer.maps");
	svg_maps.html("") // clear any existing content
	
	this.svg_charts = d3.select(".resourcecontainer.charts");
	svg_charts.html("") // clear any existing content 
	
	this.svg_timeseries = d3.select(".resourcecontainer.timeseries");
	svg_timeseries.html("") // clear any existing content 
	
	d3.json(gazetteer_header_file, function(error, gazetteer_header){
		load_gazeteer(gazetteer_file, gazetteer_header, map_data_file);
	});
}


function load_gazeteer(gazetteer_file, gazetteer_header, map_data_file)
{
	
	d3.select(".resourcecontainer.buttons").selectAll(".gazeteer").remove(); // clean up content
	
	this.svg_maps = d3.select(".resourcecontainer.maps");
	svg_maps.selectAll("*").remove() // clear any existing content
	
	this.svg_charts = d3.select(".resourcecontainer.charts");
	svg_charts.selectAll("*").remove() // clear any existing content 
	
	this.svg_timeseries = d3.select(".resourcecontainer.timeseries");
	svg_timeseries.selectAll("*").remove() // clear any existing content 
	
	// building dashboard options header
	// (e.g. parameter names)
	var gazeteer_selection =  d3.select(".resourcecontainer.buttons").append("ul").html("<li class = 'gazeteer_options_header'>" + gazetteer_header + "</li>")
			.attr("class", "gazeteer");
	
				/* the usual  d3js append function call (below) produces bad html in the context of additionally appended list items binded to data (further below) */
	
				/*
				.append("li")
				.attr("class", "gazeteer_options_header")
				.html(calib_params_names);
				*/
			
	// options of experiments/models and the respective models' parameters values
	// one of the models may be selected at a time 
	d3.json(gazetteer_file, function(error, gazeteer) {
		gazeteer_selection.selectAll("li.gazeteer_option")
			.data(gazeteer)
			.enter().append("li")
			 .attr("value", function (d) {
				 	return d.model; 
			 		})
			 .attr("class", function(d){if (d.model == gazeteer_select_model) return "gazeteer_model_selected"; else return "gazeteer_model";})
			 .on("click", function (d) { gazeteer_select_model = d.model;})
            .html(function(d){ return d.params })
            .append("select")
            .selectAll("option")
            .data(function(d) { return d.select; })
            .enter().append("option")
            	.attr("value", function(d){ return d.value })
            	.attr("id", function(d){ return "model_"+d.value; })
            	.text(function(d){ return d.name})
            	.attr("selected", function(d){ if (d.value == gazeteer_select) return true;})
				.on("click", function (d) {
					
						d3.select("#model_"+gazeteer_select).attr("class","gazeteer_model");
						d3.select("#model_"+d.value).attr("class","gazeteer_model_selected");
						
			            gazeteer_select = d.value;
			            load_maps(map_data_file);
			            if(node_select != "unselect")
			               load_node_charts({});
				}) 	
		});
	
	
	d3.select(".resourcecontainer.buttons").selectAll(".time_idxs").remove() // clear time idx/step buttons 
	
	var time_idxs_selection = d3.select(".resourcecontainer.buttons").append("ul")
						.attr("class", ".time_idxs"); // append time idx selection buttons container

	// time idxs (e.g. days) associated with buttons  
	var time_idxs = [6*365 + 160, 6*365 + 160 + 60, 6*365 + 160 + 60 + 60, 7*365 + 160, 7*365 + 160 + 60, 7*365 + 160 + 60 + 60];

	time_idxs_selection.selectAll("li")
		.data(time_idxs)
		.enter().append("li")
		 .attr("id", function(d){ return "time_idx_" + d; })
		 .attr("value", function (d) { return d; })
		 .text(function (d, i) { return "Round " + (i + 1); })
		 .attr("class", function(d){ if (d == time_idx_select) return "time_idx_selected"; else return "time_idx_option"; }) // set the selected time idx class for style
		 .on("click", function (d) {
			 
			d3.select("#time_idx_" + time_idx_select).attr("class", "time_idx_option"); 
			d3.select("#time_idx_" + d).attr("class", "time_idx_selected");
            time_idx_select = d;            
            load_maps(map_data_file); // load widgets with data state at the given time idx
            if(node_select != "unselect")
	               load_node_charts({});
        });
}


// this all can be done in a more generic, configurable, better styled way; 
// for now opt for proof of concept; this is an example of more complicated behavior than
// most people would likely want from a dashboard.
function style_selected_hm_param(params)
{	
	
	var selected_hm_param = ""
	if (params.hasOwnProperty("name"))
		selected_hm_param = params["name"];
	else
		return;
	
	var ts_color = ""
	if (params.hasOwnProperty("ts_color"))
	{
		ts_color = params["ts_color"];
	}
	
	
	// get array of param class names that have been selected
	var selected_params_class_names = params_select.map(function(s){ return s.className; });
	
	// if the newly selected param class name has not been selected before, add it to selection
	var selected_idx = selected_params_class_names.indexOf(selected_hm_param);
	
	if(selected_idx == -1)
	{
		// store the original fill color/style of the elements matching the selected param className so that it could be restored later when not selected
		var selected_param_elements = document.getElementsByClassName(selected_hm_param);
		
		var fill = [];
		for(var i = 0; i < selected_param_elements.length; i++)
			fill.push(selected_param_elements[i].style.fill);
		
		params_select.push({className : selected_hm_param, fill : fill, "toggled":true});
		selected_idx = params_select.length - 1; // update selected index to point to the index of the newly selected param class
	}
	else // toggle the corresponding selected param 
		params_select[selected_idx].toggled = !params_select[selected_idx].toggled; 
	
	// get the selected param 
	var param_select = params_select[selected_idx];
	
	// get all elements matching className
	var selected_param_elements = document.getElementsByClassName(param_select.className);
	
	// change the style of the elements matching the selected param className depending on whether param was toggled on or off
	if (param_select.toggled)
	{
		// if the selected param is toggled on, change style of all elements matching the selected parameter className to the toggled on style
		// here, we use the colors passed to the timeseries widget, and return by the callback but we do not need to
		for(var i = 0; i < selected_param_elements.length; i++)
			selected_param_elements[i].style.fill = ts_color;
	}
	else
	{
		// if the selected parameter is toggled off; restore the original style of all elements matching the selected parameter className
		for(var i = 0; i < param_select.fill.length; i++)
			selected_param_elements[i].style.fill = param_select.fill[i];
	}
}




function load_node_charts(params)
{
	
	// only need to do anything if selection changed
	if (params.hasOwnProperty("NodeLabel") && node_select == params["NodeLabel"])
		return;
	
	// restore style of nodes
	selected_nodes = document.getElementsByClassName(node_select);
	for (var i = 0; i < selected_nodes.length; i++)
	{
		var node = selected_nodes[i];
		node.style.stroke = "gray";
	}
	
	node_select = params["NodeLabel"];
	
	// re-initialize parameters to be selected relevant for this node
	params_select = []


	selected_nodes = document.getElementsByClassName(node_select);
	
	for (var i = 0; i < selected_nodes.length; i++)
	{
		var node = selected_nodes[i];
		node.style.stroke = "black";
		node.style.strokeWidth = "2px";
		
		// blacklist communication from this node, to avoid infinite "message" loops 
		comm_blacklist.push(node.id);
		
		// so many things can go wrong here that for now we'd foolishly ignore the complexity
		// then, we'll have to remove it
		trigger_event(node, "mouseover");
		
		comm_blacklist.pop(node.id);
	}

	
	//alert(" drawing heatmap for #hm_" + node_select)
	// clear the existing heatmap
	d3.select(".hm_container").remove()
	
	// draw the new heatmap
	heatmap(node_select);

	// clear the existing ts
	d3.select(".ts_container").remove()
	
	// draw the new timeseries
	timeseries(node_select);
}


// this function can be made more generic but for now suffices
// the user-programmed dashboard "knows" about the specific parameters the user is designing it for
function emit_param_key_by_params(params)
{
	var event = "click"
	if (params.hasOwnProperty("funestus_sc"))
		funestus_sc = params["funestus_sc"];
	else
		return;
	if (params.hasOwnProperty("arabiensis_sc"))
		arabiensis_sc = params["arabiensis_sc"];
	else
		return;
	if (params.hasOwnProperty("event"))
		event = params["event"];
	
	// generic emit is implemented in comms.js
	emit(
			{
				"event":event,
				"selector":{"param":"funestus_sc_30_arabiensis_sc_117"}
			}
	);
}

function emit_param_key_by_header(params)
{
	var event = "click"
	if (params.hasOwnProperty("name"))
		header = params["name"];
	else
		return;
	
	if (params.hasOwnProperty("event"))
		event = params["event"];
	
	header = header.replace(" ", "").replace("/", "");
	
	// generic emit is implemented in comms.js
	emit(
			{
				"event":event,
				"selector":{"param":header}
			}
	);
}


function heatmap(node_label)
{	
    var colors = ['#000000','#52170b','#a51b0b','#ff0000','#c1003c','#80005f','#000080','#233381','#265a81','#008080','#46a386','#6dc88c','#90ee90','#b8f4ab','#dcfac5','#ffffe0'];   
    var color_scale = d3.scale.sqrt()
   					.domain(d3.range(0, 1, 1.0 / (15)))
   					.range(colors);
    
	load_heatmap(
		   			node_label,
		   			//d3.scale.quantize().domain([0, 1]).range(colorbrewer.PuRd[9]),
		   			color_scale,
					600, // height
					'funestus_sc', // what attribute of the heatmap json objects corresponds to the x axis values
					'arabiensis_sc', // what attribute of the heatmap json objects corresponds to the y axis values
					'zi', // what attribute of the heatmap json objects corresponds to colors (i.e. z axis values)
					'.resourcecontainer.charts', // where to load the heatmap; default is <body>
		   			{
   			   			"selector":{"function": {"func":emit_param_key_by_params, "params":{"event":"click"}}},
   			   			"attributes_req":["funestus_sc", "arabiensis_sc"]
					}
	);
}


function timeseries(node_label)
{
	
	if(!d3.select('.resourcecontainer.timeseries').select(".ts_container").empty()) // make sure there is one timeseries chart w/ a given id displayed at a time
		return;
	
	load_timeseries(
			node_label, 
			'prevalence', 
			['#a6cee3','#1f78b4','#b2df8a','#33a02c','#fb9a99','#e31a1c','#fdbf6f','#ff7f00','#cab2d6','#6a3d9a','#ffff99','#b15928'],
			'observed',
			".resourcecontainer.timeseries",
			{
	   			//"selector":{"function": {"func":emit_param_key_by_header, "params":{"event":"mouseover"}}},
				"selector":{"function": {"func":style_selected_hm_param, "params":{}}},
	   			"attributes_req":["name", "ts_color"] // request the header name
			}
	);		

}

function load_maps(map_data_file)
{
	
	// load the map file relevant for the gazetteer selection
	gazetteer_map = gazeteer_select + "_" + map_data_file;
	
	d3.select(".resourcecontainer.maps").selectAll("*").remove(); // clear all maps
	d3.select(".resourcecontainer.charts").selectAll("*").remove(); // clear all charts

	load_map(
	 		   'rdt_obs', // map id 
	 		   gazetteer_map, 
	 		   ".resourcecontainer.maps", //target container
	 		   {}
	);

	style_map(
	 		   'rdt_obs', 
	 		   gazetteer_map,
	 		   {
					   time_idx : time_idx_select,
					   base_tile_layer : L.tileLayer('http://{s}.tile.thunderforest.com/landscape/{z}/{x}/{y}.png', {
							attribution: '&copy; <a href="http://www.thunderforest.com/">Thunderforest</a>, &copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
					   	  }),
					   /*
					   base_tile_layer : L.tileLayer('http://korona.geog.uni-heidelberg.de/tiles/roads/x={x}&y={y}&z={z}', {
											maxZoom: 20,
											attribution: 'Imagery from <a href="http://giscience.uni-hd.de/">GIScience Research Group @ University of Heidelberg</a> &mdash; Map data &copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
										}),
					   */
			   		   node_attr_2_color : ["RDT_obs", d3.scale.quantize().domain([0, 0.52]).range(colorbrewer.OrRd[9])],
			   		   node_attr_2_radius : ["Population", d3.scale.sqrt().domain([0, 1e3]).range([0, 8])]
					   //node_attr_2_stroke : ["Received_Campaign_Drugs", d3.scale.threshold().domain([0, 10]).range(['#000000','#281005','#471609','#691a0c','#8c1b0c','#b11a0a','#d71306','#ff0000'])],
					   //node_attr_2_opacity : ["Received_ITN", d3.scale.threshold().domain([0, 10]).range(['0.1','0.2','0.3','0.4','0.5','0.6','0.7','0.8'])]
			   	},
			   	{
			   			"selector":{"function": {"func":load_node_charts, "params":{}}},
			   			"attributes_req":["NodeLabel"]
		   		}
	);
	
	
	
	load_map(
			   'rdt_sim', 
			   gazetteer_map,
			   ".resourcecontainer.maps", //target container
			   {}
	);

	style_map(
		    'rdt_sim', 
		    gazetteer_map,
		    {
			   time_idx : time_idx_select,
			   base_tile_layer : L.tileLayer('http://{s}.tile.thunderforest.com/landscape/{z}/{x}/{y}.png', {
					attribution: '&copy; <a href="http://www.thunderforest.com/">Thunderforest</a>, &copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
			   	  }),
			   /*
			   base_tile_layer : L.tileLayer('http://korona.geog.uni-heidelberg.de/tiles/roads/x={x}&y={y}&z={z}', {
									maxZoom: 20,
									attribution: 'Imagery from <a href="http://giscience.uni-hd.de/">GIScience Research Group @ University of Heidelberg</a> &mdash; Map data &copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
								}),
			   */
			   node_attr_2_color : ["RDT_sn_sim", d3.scale.quantize().domain([0, 0.52]).range(colorbrewer.OrRd[9])],
			   node_attr_2_radius : ["Population", d3.scale.sqrt().domain([0, 1e3]).range([0, 8])]
		    },
	   		{
			   			"selector":{"function": {"func":load_node_charts, "params":{}}},
			   			"attributes_req":["NodeLabel"]
		    }
	);

	
	
   load_map(
			   'funestus', 
			   gazetteer_map,
			   ".resourcecontainer.maps", //target container
			   {}
   );
	
   style_map(
		    'funestus', 
		    gazetteer_map,
		    {
			   time_idx : time_idx_select,
			   base_tile_layer : L.tileLayer('http://{s}.tile.thunderforest.com/landscape/{z}/{x}/{y}.png', {
									attribution: '&copy; <a href="http://www.thunderforest.com/">Thunderforest</a>, &copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
							   	  }),
	   		   node_attr_2_color : ["funestus_sc", d3.scale.quantize().domain([0.01, 120]).range(colorbrewer.RdPu[9])],
		       node_attr_2_radius : ["Population", d3.scale.sqrt().domain([0, 1e3]).range([0, 8])]
		    },
		    {
		   			"selector":{"function": {"func":load_node_charts, "params":{}}},
		   			"attributes_req":["NodeLabel"]
		    }
	);
   
   
   load_2d_scatter(
   		   'hsb_scales_rdt_pos', 
   		    gazetteer_map,
   		    {
				   time_idx : time_idx_select,
		   		   node_opacity : 0.6,
		   		   node_attr_2_color : ["RDT_obs", d3.scale.quantize().domain([0, 0.52]).range(colorbrewer.OrRd[9])],
		   		   node_attr_2_radius : ["Population", d3.scale.sqrt().domain([0, 1e3]).range([0, 8])],
		   		   node_attr_2_x : "funestus_sc",
		   		   node_attr_2_y : "arabiensis_sc"
		   		
   		    },
   		    ".resourcecontainer.charts",
   		    {
	   			"selector":{"function": {"func":load_node_charts, "params":{}}},
					"attributes_req":["NodeLabel"]
   		 	}
	);
}