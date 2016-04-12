var gazeteer_select_model = "unselect";
var gazeteer_select = "unselect";
var time_idx_select = 6*365 + 160;

function load_dashboard(gazetteer_file, gazetteer_header_file, map_data_file)
{
	this.svg_maps = d3.select(".resourcecontainer.maps");
	svg_maps.html("") // clear any existing content 
	
	d3.json(gazetteer_header_file, function(error, gazetteer_header){
		load_gazeteer(gazeteer_file, map_data_file, gazetteer_header);
	});
}


function load_gazeteer(gazeteer_file, map_data_file, calib_params_names)
{
	
	d3.select(".resourcecontainer.buttons").selectAll(".gazeteer").remove(); // clean up content
	
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
	d3.json(gazeteer_file, function(error, gazeteer) {
		gazeteer_selection.selectAll("li.gazeteer_option")
			.data(gazeteer)
			.enter().append("li")
			 .attr("value", function (d) {
				 	return d.model; 
			 		})
			 .attr("class", function(d){if (d.model == gazeteer_select_model) return "gazeteer_model_selected"; else return "gazeteer_model";})
			 .on("click", function (d) { gazeteer_select_model = this.d.model;})
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
			            load_widgets(map_data_file);
				}) 	
		});
	
	
	d3.select(".resourcecontainer.buttons").selectAll(".time_idxs").remove() // clear time idx/step buttons 
	
	var time_idxs_selection = d3.select(".resourcecontainer.buttons").append("ul")
						.attr("class", ".time_idxs"); // append time idx selection buttons container

	// time idxs (e.g. days) associated with buttons  
	var time_dxs = [6*365 + 160, 6*365 + 160 + 60, 6*365 + 160 + 60 + 60, 7*365 + 160, 7*365 + 160 + 60, 7*365 + 160 + 60 + 60];

	time_idxs_selection.selectAll("li")
		.data(time_idxs)
		.enter().append("li")
		 .attr("value", function (d) { return d; })
		 .text(function (d, i) { return "Round " + (i + 1); })
		 .attr("class", function(d){ if (d == time_idx_select) return "time_idx_selected"; else return "time_idx_option"; }) // set the selected time idx class for style
		 .on("click", function (d) {
            time_idx_select = d;
            load_widgets(map_data_file); // load widgets with data state at the given time idx
        });
}


function load_widgets(map_data_file)
{
	d3.select(".resourcecontainer.maps").selectAll("*").remove(); // clear all maps

	load_map(
	 		   'rdt_obs', // map id 
	 		   map_data_file, 
	 		   ".resourcecontainer.maps" //target container
	);

	style_map(
	 		   'rdt_obs', 
	 		    map_data_file,
	 		    {
					   time_idx : time_idx_select,
					   base_tile_layer : L.tileLayer('http://korona.geog.uni-heidelberg.de/tiles/roads/x={x}&y={y}&z={z}', {
											maxZoom: 20,
											attribution: 'Imagery from <a href="http://giscience.uni-hd.de/">GIScience Research Group @ University of Heidelberg</a> &mdash; Map data &copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
										}),
			   		   node_opacity : 0.6}
	);
	
	
	
	load_map(
			   'rdt_sim', 
			   map_data_file,
			   ".resourcecontainer.maps" //target container
		  	);
	
	style_map(
		   'rdt_obs_rnd_2', 
		   'map.json',
		    {
			   time_idx : time_idx_select,
			   base_tile_layer : L.tileLayer('http://korona.geog.uni-heidelberg.de/tiles/roads/x={x}&y={y}&z={z}', {
									maxZoom: 20,
									attribution: 'Imagery from <a href="http://giscience.uni-hd.de/">GIScience Research Group @ University of Heidelberg</a> &mdash; Map data &copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
								}),
	   		   node_opacity : 0.6
		    }	   
	);
	
	
	
	load_map(
			   'funestus', 
			   'map.json'
		  	);
	
	   style_map(
			   'funestus', 
			   'map.json',
			    {
				   time_idx : 0,
				   base_tile_layer : L.tileLayer('http://{s}.tile.thunderforest.com/landscape/{z}/{x}/{y}.png', {
										attribution: '&copy; <a href="http://www.thunderforest.com/">Thunderforest</a>, &copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
								   	  }),
		   		   node_opacity : 0.6,
		   		   node_attr_2_color : ["funestus_sc", d3.scale.quantize().domain([0.01, 120]).range(colorbrewer.RdPu[9])]
			    }	   
			);
	
	
	
	

}