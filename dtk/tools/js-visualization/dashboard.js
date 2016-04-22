var gazeteer_select_model = "unselect";
var gazeteer_select = "unselect";
var node_select = "80202_5";
var time_idx_select = 6*365 + 160;

function load_dashboard(gazetteer_file, gazetteer_header_file, map_data_file)
{
	this.svg_maps = d3.select(".resourcecontainer.maps");
	svg_maps.html("") // clear any existing content
	
	this.svg_charts = d3.select(".resourcecontainer.charts");
	svg_charts.html("") // clear any existing content 
	
	this.svg_timeseries = d3.select(".resourcecontainer.timeseries");
	svg_timeseries.html("") // clear any existing content 
	
	d3.json(gazetteer_header_file, function(error, gazetteer_header){
		load_gazeteer(gazetteer_file, map_data_file, gazetteer_header);
	});
}


function load_gazeteer(gazetteer_file, map_data_file, gazetteer_header)
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
            	.text(function(d){ return d.name})
            	.attr("selected", function(d){ if (d.value == gazeteer_select) return true;})
				.on("click", function (d) {
			            gazeteer_select = d.value;
			            load_maps(map_data_file);
			            load_node_charts({})
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
		 .attr("value", function (d) { return d; })
		 .text(function (d, i) { return "Round " + (i + 1); })
		 .attr("class", function(d){ if (d == time_idx_select) return "time_idx_selected"; else return "time_idx_option"; }) // set the selected time idx class for style
		 .on("click", function (d) {
            time_idx_select = d;
            load_maps(map_data_file); // load widgets with data state at the given time idx
            load_node_charts({})
        });
}

function load_node_charts(params)
{
	if (params.hasOwnProperty("NodeLabel"))		
		node_select = params["NodeLabel"];
	
	heatmap(node_select);
	timeseries(node_select);
}


// this function can be made more generic but for no sufficies
// the user-programmed dashboard "knows" about the specific parameters the user is designing it for
function emit_param_key(params)
{
	if (params.hasOwnProperty("funestus_sc"))
		funestus_sc = params["funestus_sc"]
	if (params.hasOwnProperty("arabiensis_sc"))
		arabiensis_sc = params["arabiensis_sc"]
	
	// generic emit is implemented in comms.js
	//emit("click", {"param":"funestus_sc" + "_" + funestus_sc + "_arabiensis_sc_" + arabiensis_sc});
	emit(
			{
				"event":"click",
				"selector":{"param":"funestus_sc_30_arabiensis_sc_117"}
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
   			   			"selector":{"function": {"func":emit_param_key, "params":{}}},
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
			//trigger_emit(this, "mouseover", {"param": d.name.replace(" ", "").replace("/", "")});
			{
	 			"event":"mouseover",
	 			"selector":{"param": "funestus_sc_30_arabiensis_sc_117"}
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
	 		   ".resourcecontainer.maps" //target container
	);

	style_map(
	 		   'rdt_obs', 
	 		   gazetteer_map,
	 		   {
					   time_idx : time_idx_select,
					   base_tile_layer : L.tileLayer('http://korona.geog.uni-heidelberg.de/tiles/roads/x={x}&y={y}&z={z}', {
											maxZoom: 20,
											attribution: 'Imagery from <a href="http://giscience.uni-hd.de/">GIScience Research Group @ University of Heidelberg</a> &mdash; Map data &copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
										}),
			   		   node_opacity : 0.6,
			   		   comm_msg: {
   			   			"selector":{"function": {"func":load_node_charts, "params":{}}},
   			   			"attributes_req":["NodeLabel"]
			   		   }
			   	}
	);
	
	
	
	load_map(
			   'rdt_sim', 
			   gazetteer_map,
			   ".resourcecontainer.maps" //target container
	);
	
	style_map(
		    'rdt_sim', 
		    gazetteer_map,
		    {
			   time_idx : time_idx_select,
			   base_tile_layer : L.tileLayer('http://korona.geog.uni-heidelberg.de/tiles/roads/x={x}&y={y}&z={z}', {
									maxZoom: 20,
									attribution: 'Imagery from <a href="http://giscience.uni-hd.de/">GIScience Research Group @ University of Heidelberg</a> &mdash; Map data &copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
								}),
			   node_attr_2_color : ["RDT_sn_sim", d3.scale.quantize().domain([0, 0.52]).range(colorbrewer.OrRd[9])],
	   		   node_opacity : 0.6,
	   		   comm_msg: {
	   			   			"selector":{"function": {"func":load_node_charts, "params":{}}},
	   			   			"attributes_req":["NodeLabel"]
	   		   }
		    }	   
	);
	
	

   load_map(
			   'funestus', 
			   gazetteer_map,
			   ".resourcecontainer.maps" //target container
   );
	
   style_map(
		    'funestus', 
		    gazetteer_map,
		    {
			   time_idx : time_idx_select,
			   base_tile_layer : L.tileLayer('http://{s}.tile.thunderforest.com/landscape/{z}/{x}/{y}.png', {
									attribution: '&copy; <a href="http://www.thunderforest.com/">Thunderforest</a>, &copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
							   	  }),
	   		   node_opacity : 0.6,
	   		   node_attr_2_color : ["funestus_sc", d3.scale.quantize().domain([0.01, 120]).range(colorbrewer.RdPu[9])],
		       comm_msg: {
		   			"selector":{"function": {"func":load_node_charts, "params":{}}},
		   			"attributes_req":["NodeLabel"]
		       }
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
		   		   node_attr_2_y : "arabiensis_sc",
		   		   comm_msg: {
		   			   			"selector":{"function": {"func":load_node_charts, "params":{}}},
   		   						"attributes_req":["NodeLabel"]
		   		   }
		   		
   		    },
   		    ".resourcecontainer.charts"
	);
}