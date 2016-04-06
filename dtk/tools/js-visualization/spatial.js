/* 
 * A global object of leaflet maps accessible to everyone in this file;
 * reason: one cannot extract leaflet maps from html DOM and passing leaflet 
 * map objects across various d3js/js object might be tedious 
 * (the latter could still be the better design choice though... ?)
 * 
 * object structure:
 * 
 * maps = {
 * 			map_id:leaflet_map // map_id is user supplied; the leaflet map is created in load_map
 * 		  }
 * 
 * 
 * 
 */
var maps = {};



/*
 * global time index; 
 * 
 * given centralized time index, visualization of all spatial 
 * entities with temporal dimension can be synced;
 * 
 * to indicate that an entity has a temporal dimension, the entity should have an attribute 'time:true';
 * see function style_map(...) for examples of such entities
 */
var global_time_idx = 0; 

/*
 * global selection
 * 
 * indicates the set of selected entities by label
 * currently supported labels are "nodes" and "params"
 * only one entity per label can be selected
 * 
 * 
 * label logic is handled on entity selection 
 */




function load_map(map_id, map_json)
{
		
		var map_decorations_container = d3.select("body").append("div")
										.attr("id","map_decorations_container_"+map_id);
	
		var map_container = d3.select("#map_decorations_container_" + map_id).append("div")
							.attr("id","map_container_"+map_id)
							.style({height:"400px", width:"600px", float:"left"}); // expose width/height as parameters?
	
		var map = L.map("map_container_"+map_id).setView([-41.2858, 174.7868], 13);
	    
		
		mapLink = '<a href="http://openstreetmap.org">OpenStreetMap</a>'; 
		 
		tile_layer = L.tileLayer(
					'http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
					attribution: '&copy; ' + mapLink + ' Contributors',
					maxZoom: 18,
					}).addTo(map);
		
		
		/* Initialize the SVG layer */
		map._initPathRoot();
		
		var svg = d3.select("#map_container_"+map_id).select("svg")
		  .attr("id", map_id);
	
		maps[map_id] = {
				"map":map,
				"layers":[tile_layer]
				}
		
		d3.json(map_json, function(map_nodes){ 
		
			var markers = []
			var nodes = []
			map_nodes.forEach(function(d) {
				
				markers.push(new L.LatLng(d.Latitude, d.Longitude))
				nodes.push({
								coor:new L.LatLng(d.Latitude, d.Longitude), 
								node:d
								}); 	
			})
			
			var bounds = new L.LatLngBounds(markers);
			
			
			/* 
			 * Should nodes be displayed on load_map?
			 * Perhaps the most generic map should only contain 
			 * a base map layer and avoid rendering additional objects?
			 * 
			 * This behavior can easily be refactored.
			 */
			
			g = svg.append("g");
			
			var node = g.selectAll("circle")
			.data(nodes)
			.enter().append("circle")
			.attr("r", 10)  
			.attr("id", function(d) {return get_node_key(d.node.NodeLabel, map_id)})
			.attr("class", function(d) {return d.node.NodeLabel})
			
			map.on("viewreset", update);
			update();
		
			function update() {
				node.attr("transform", 
				function(d) { 
					return "translate("+ 
						map.latLngToLayerPoint(d.coor).x +","+ 
						map.latLngToLayerPoint(d.coor).y +")";
				})	
			}
			
			map.fitBounds(bounds);
		});// end d3.json(...)

	return
}


function style_map(
						map_id,
						map_json,
						map_properties // object
				   )
{
	/*
	 *  can we pass optional parameters in arbitrary order and set their defaults if not passed (similarly to python kwargs)
	 *  in a better way than below??!!
	 *  
	 *  Perhaps an additional refactor might abstract some common map/node style properties away (there is some redundancy of code across 
	 *  style_map and load_2d_scatter related to node style). A node map is a type of node scatter (it is a node scatter w/ map layers and geo coordinates).
	 *  TODO?: This relationship can naturally be captured by object decoration.  
	 *   
	 */

	
	if(!maps.hasOwnProperty(map_id))
	{
		alert("Need to call load_map() first and create a map with id " + map_id);
		return;
	}
	
	// this would set a map-local time in lieu of the global time index, if provided; if not provided global time would be used
	if(!map_properties.hasOwnProperty('time_idx'))
		var time_idx = false;
	else
		var time_idx = map_properties.time_idx;
	 
	// base layer is always the first one in the layers array
	if(!map_properties.hasOwnProperty('base_tile_layer'))
		var base_tile_layer = maps[map_id]["layers"][0];
	else
		var base_tile_layer = map_properties.base_tile_layer;
	
	//map width
	if(!map_properties.hasOwnProperty('map_width'))
		var map_width = $('#map_container_' + map_id).width(); 
	else
		var map_width = $('#map_container_' + map_id).width(map_properties.map_width);
	
	//map height
	if(!map_properties.hasOwnProperty('map_height'))
		var map_height = $('#map_container_' + map_id).height(); 
	else
		var map_height = $('#map_container_' + map_id).height(map_properties.map_height);
	
	// layers to add to map
	if(!map_properties.hasOwnProperty('additional_layers'))
		var additional_layers = [];
	else
		var additional_layers = map_properties.additional_layers;
	
	// map the value of entity node's specific attribute to node marker color
	if(!map_properties.hasOwnProperty('node_attr_2_color'))
		var node_attr_2_color = ["RDT_obs", d3.scale.quantize().domain([0, 0.52]).range(colorbrewer.OrRd[9])];
	else
		var node_attr_2_color = map_properties.node_attr_2_color;
	
	// map the value of entity node's specific attribute to node marker radius
	if(!map_properties.hasOwnProperty('node_attr_2_radius'))
		var node_attr_2_radius = ["Population", d3.scale.sqrt().domain([0, 1e3]).range([0, 8])];
	else
		var node_attr_2_radius = map_properties.node_attr_2_radius;
	
	// node marker's opacity on map
	if(!map_properties.hasOwnProperty('node_opacity'))
		var node_opacity = 0.6;
	else
		var node_opacity = map_properties.node_opacity;
	
	//behavior of node marker's on mouse over is function onmouseover
	if(!map_properties.hasOwnProperty('onmouseover'))
		onmouseover = onmouseover_default;
	else
		var onmouseover = map_properties.onmouseover;
	
	// behavior of node marker's on mouse out is function onmouseout
	if(!map_properties.hasOwnProperty('onmouseout'))
		var onmouseout = onmouseout_default;
	else
		var onmouseout = map_properties.onmouseout; 
	
	
	var map = maps[map_id]["map"];
	var map_layers = maps[map_id]["layers"];

	// use a new base layer for the map; (by default use same base layer)
	map.removeLayer(map_layers[0]); 
	map_layers.unshift(base_tile_layer);
	base_tile_layer.addTo(map);	
	
	
	// add additional layers to the map (useful to add roads, etc.); by default no new additional layers are provided
	for(i = 0; i < additional_layers.length; i++)
		additional_layers[i].addTo(map);
	
	// set local map time if provided
	var time = 0;
	if(time_idx)
		time = time_idx;
	else
		time = global_time_idx;
	
	var node_attr_color = node_attr_2_color[0];
	var color_scale = node_attr_2_color[1];

	var node_attr_radius = node_attr_2_radius[0];
	var radius_scale = node_attr_2_radius[1];
	
	
	// add attribute node_attr_2_radius to map object
	maps[map_id]["node_attr_2_radius"] = node_attr_2_radius
	
	// add attribute node_attr_2_color to map object
	maps[map_id]["node_attr_2_color"] = node_attr_2_color
	
	// add attribute node_attr_2_color to map object
	maps[map_id]["node_opacity"] = node_opacity
	
	// add attribute time to map object
	maps[map_id]["time"] = time

	// add attribute onmouseover
	//maps[map_id]["onmouseover"] = onmouseover
	// add attribute onmouseover
	//maps[map_id]["onmouseout"] = onmouseout
	
	var color_bar_orientation = "vertical";
	
	var colorbar = Colorbar() // expose colorbar parameters? probably not needed...
		    .origin([35,-5])
		    .thickness(100)
		    .scale(color_scale).barlength(map_height).thickness(25)
		    .orient(color_bar_orientation)
		    .margin({top:20, left:30, right:55, bottom:10});
	
	var bar_container =  d3.select("#map_decorations_container_"+map_id)
						.append("div")
						.attr("id", "colorbar_container_"+map_id);
	
	var bar = d3.select("#colorbar_container_"+map_id)
						.append("svg")
						.attr("width", 100)
						.attr("height", map_height + 10)
						.append("g")
						.attr("id","colorbar_"+map_id);
	
	var pointer = d3.selectAll("#colorbar_" + map_id).call(colorbar)
	
	
	// traverse nodes and set respective map markers style
	d3.json(map_json, function(map_nodes){
		
		
		// if the attributes of any nodes on this map will be changed select the relevant nodes
		// for loops are more efficient than forEach... could switch later if optimization is premature
		for(j = 0; j < map_nodes.length; j ++)
		{
			
			var node = map_nodes[j];
			
			var node_key = get_node_key(node.NodeLabel, map_id);
			d3.select("#" + node_key)
			.attr("fill", function (d) {
                var c = 'white';
                var val = get_entity_value(d.node[node_attr_color], time);

            	if (val >= 0) { c = color_scale(val); }
            	else { c = 'gray'; }
            	
            	return c;
			})
			.attr("r", function (d) { 
				var val = get_entity_value(d.node[node_attr_radius], time);
				return radius_scale(val);
			})
			.attr("opacity", node_opacity)
			//all of the below options (e.g. tooltip attributes) can be exposed on per map basis as map styling properties)
			.attr("data-toggle", "tooltip")
			.attr("data-placement", "top")
			.attr("html", true) // tooltip style can be further improved via bootstrap css options
			.attr("title", function(d){
				
				var val = get_entity_value(d.node[node_attr_color], time);
				if (val < 0) { val = 'N/A'; }
			    else { val = val } // keep else as place holder; might want to expose formatting options as function arguments to get something along the lines of d3.format('%')(val);
				
				return  d.node.NodeLabel + ": " + node_attr_color + ": " + val;
			})
			
			.style("stroke", "black")
			.on("mouseover",function(d) { pointer.pointTo(get_entity_value(d.node[node_attr_color], time)); });
			//.on("mouseover", onmouseover())
            //.on("mouseout", onmouseout())
            //.each(function(d){if(d.node.NodeLabel == selected_entities.node){onmouseover()}})
		}

		
	}); // end d3.json(...)
}

function load_2d_scatter(	
							scatter_id,
							scatter_json,
							scatter_properties // object
						 )
{
	// this would set a scatter-local time in lieu of the global time index, if provided; if not provided global time would be used
	if(!scatter_properties.hasOwnProperty('time_idx'))
		var time_idx = false;
	else
		var time_idx = scatter_properties.time_idx;
	
	//scatater width
	if(!scatter_properties.hasOwnProperty('scatter_width'))
		var scatter_width = 500; 
	else
		var scatter_width = scatter_properties.width;
	
	//scatter height
	if(!scatter_properties.hasOwnProperty('scatter_height'))
		var scatter_height = 600;  
	else
		var scatter_height = scatter_properties.height;
	
	
	// map the value of entity node's specific attribute to node marker color
	if(!scatter_properties.hasOwnProperty('node_attr_2_color'))
		var node_attr_2_color = ["RDT_obs", d3.scale.quantize().domain([0, 0.52]).range(colorbrewer.OrRd[9])];
	else
		var node_attr_2_color = scatter_properties.node_attr_2_color;
	
	// map the value of entity node's specific attribute to node marker radius
	if(!scatter_properties.hasOwnProperty('node_attr_2_radius'))
		var node_attr_2_radius = ["Population", d3.scale.sqrt().domain([0, 1e3]).range([0, 8])];
	else
		var node_attr_2_radius = scatter_properties.node_attr_2_radius;
	
	// map the value of entity node's specific attribute to x-axis
	if(!scatter_properties.hasOwnProperty('node_attr_2_x'))
		var node_attr_2_x = "x"; // this is just a default best-effor attempt; if the scatter node data does not contain attribute x the function would fail 
	else
		var node_attr_2_x = scatter_properties.node_attr_2_x;
	
	// map the value of entity node's specific attribute to y-axis
	if(!scatter_properties.hasOwnProperty('node_attr_2_y'))
		var node_attr_2_y = "y"; // this is just a default best-effor attempt; if the scatter node data does not contain attribute y the function would fail  
	else
		var node_attr_2_y = scatter_properties.node_attr_2_y;
	
	// map the value of entity node's specific attribute to node marker radius
	if(!scatter_properties.hasOwnProperty('node_attr_2_radius'))
		var node_attr_2_radius = ["Population", d3.scale.sqrt().domain([0, 1e3]).range([0, 8])];
	else
		var node_attr_2_radius = scatter_properties.node_attr_2_radius;
	
	// node marker's opacity on scatter
	if(!scatter_properties.hasOwnProperty('node_opacity'))
		var node_opacity = 0.6;
	else
		var node_opacity = scatter_properties.node_opacity;
	
	//behavior of node marker's on mouse over is function onmouseover
	if(!scatter_properties.hasOwnProperty('onmouseover'))
		onmouseover = onmouseover_default;
	else
		var onmouseover = scatter_properties.onmouseover;
	
	// behavior of node marker's on mouse out is function onmouseout
	if(!scatter_properties.hasOwnProperty('onmouseout'))
		var onmouseout = onmouseout_default;
	else
		var onmouseout = scatter_properties.onmouseout;
	
	
	// set local map time if provided
	var time = 0;
	if(time_idx)
		time = time_idx;
	else
		time = global_time_idx;
	
	var node_attr_color = node_attr_2_color[0];
	var color_scale = node_attr_2_color[1];

	var node_attr_radius = node_attr_2_radius[0];
	var radius_scale = node_attr_2_radius[1];
	
	
	var margin = {top: 50, right: 20, bottom: 50, left: 40}, // expose margins as parameters?
    width = scatter_width - margin.left - margin.right,
    height = scatter_height - margin.top - margin.bottom;
	
	var scatter_decorations_container = d3.select("body").append("div")
	.attr("id","scatter_decorations_container_"+scatter_id);

	var scatter_container = d3.select("#scatter_decorations_container_" + scatter_id).append("div")
	.attr("id","scatter_container_"+scatter_id)
	.style({height:height, width:width, float:"left"});
	
	
	var svg = d3.select("#scatter_container_" + scatter_id).append("svg")
				.attr("width", width + margin.left + margin.right)
			    .attr("height", height + margin.top + margin.bottom)
			    .attr("id", "scatter_" + scatter_id)
			   .append("g")
			    	.attr("transform", "translate(" + margin.left + "," + margin.top + ")");

	
	// Set the ranges
	var x = d3.scale.linear().range([0, width]);
	var y = d3.scale.linear().range([height, 0]);
    
	
	// draw colorbar
	var color_bar_orientation = "vertical";
	
	var colorbar = Colorbar() // expose colorbar parameters? probably not needed...
		    .origin([35,margin.top - 20])
		    .thickness(100)
		    .scale(color_scale).barlength(height).thickness(25)
		    .orient(color_bar_orientation)
		    .margin({top:20, left:30, right:55, bottom:10});
	
	var bar_container =  d3.select("#scatter_decorations_container_"+scatter_id)
						.append("div")
						.attr("id", "colorbar_container_"+scatter_id);
	
	var bar = d3.select("#colorbar_container_"+scatter_id)
						.append("svg")
						.attr("width", 100)
						.attr("height", height + 10)
						.append("g")
						.attr("id","colorbar_"+scatter_id);
	
	var pointer = d3.selectAll("#colorbar_" + scatter_id).call(colorbar)
	
	
	// traverse nodes and set respective scatter markers style
	d3.json(scatter_json, function(scatter_nodes){
		
		data_boundaries_x = d3.extent(scatter_nodes.map(function(d){return d[node_attr_2_x]})); //consider compiling a helper library containing functions of the sorts of map(function(d){return d[node_attr_2_x]}) 
		data_boundaries_y = d3.extent(scatter_nodes.map(function(d){return d[node_attr_2_y]}));
		
		x.domain(data_boundaries_x);
		y.domain(data_boundaries_y);
		
        var focus = svg.append("g")
                       .attr("transform", "translate(-100,-100)")
                       .attr("class", "focus");

        focus.append("text")
        		.attr("y", -10);

        svg.append("g")
        	.selectAll("circle")
        	.data(scatter_nodes)
        .enter().append("circle")
        	.attr("class", function(d){ return d.NodeLabel; })
        	.attr("id", function(d){ return get_node_key(d.NodeLabel, scatter_id);})
        	.attr("cx", function(d){ return x(d[node_attr_2_x]); })
        	.attr("cy", function(d){ return y(d[node_attr_2_y]); })
			.attr("fill", function (d) {
                var c = 'white';
                var val = get_entity_value(d[node_attr_color], time);

            	if (val >= 0) { c = color_scale(val); }
            	else { c = 'gray'; }
            	
            	return c;
			})
			.attr("r", function (d) { 
				var val = get_entity_value(d[node_attr_radius], time);
				return radius_scale(val);
			})
			.attr("opacity", node_opacity)
			//all of the below options (e.g. tooltip attributes) can be exposed on per scatter basis as scatter styling properties)
			.attr("data-toggle", "tooltip")
			.attr("data-placement", "top")
			.attr("html", true) // tooltip style can be further improved via bootstrap css options
			.attr("title", function(d){
				
				var val = get_entity_value(d[node_attr_color], time);
				if (val < 0) { val = 'N/A'; }
			    else { val = val } // keep else as place holder; might want to expose formatting options as function arguments to get something along the lines of d3.format('%')(val);
				
				return  d.NodeLabel + ": " + node_attr_color + ": " + val;
			})
			
			.style("stroke", "black")
			.on("mouseover",function(d) { pointer.pointTo(d3.min([d3.max(color_scale.domain()),get_entity_value(d[node_attr_color], time)])); }); // if value is greater than the maximum colorbar domain poin to the maximum of the colorbar domain 

			
			// Define the axes
			var x_axis = d3.svg.axis().scale(x)
			    .orient("bottom").ticks(10);

			var y_axis = d3.svg.axis().scale(y)
			    .orient("left").ticks(10);
			   
		    // Add the X Axis
		    svg.append("g")
		        .attr("class", "x axis")
		        .call(x_axis)
		        .attr("transform", "translate(0," + height + ")")
		      .append("text")
		        .text(node_attr_2_x)
		        .attr("x", 6)
		        .attr("dx", ".71em")
		        //.attr("class","axis_"+id);

		    // Add the Y Axis
		    svg.append("g")
		        .attr("class", "y axis")
		        .call(y_axis)
		       .append("text")
		    	.text(node_attr_2_y)
		        .attr("transform", "rotate(-90)")
		        .attr("y", 6)
		        .attr("dy", ".71em")
		        .style("text-anchor", "end");
	}); // end d3.json(...)
}

	
// helper function: given an entity check if it has temporal dimension and extract the proper value at
// the specified time (or just get the spatial scalar if the entity does not have temporal dimension)
function get_entity_value(entity, time)
{
	var val = 0;
	// check if entity has a temporal dimension; this approach to time handling might need to be re-thought
    if(entity.hasOwnProperty("time"))
    {
    	
    	// if the entity has a temporal dimension but does not have a state for the given time
    	// find the closest time for which the entity has a state
    	// note that this can and must be optimized if dealing with large time arrays
    	var closest_time = time;

    	if(!entity.hasOwnProperty(time+""))
    	{
    		times = [];
    		for(var key in entity)
    			if (Object.prototype.hasOwnProperty.call(entity, key) && key != "time") // avoiding screwiness in older IE versions 
    		        times.push(parseInt(key));
    		
    		closest_time = get_closest(times, time);
    	}

    	val = entity[closest_time + ""];
    }
    else
    	val = entity;
    
    return val;
}
	
	
// helper function: given 1D array a of numbers, find the element in a closest in abs value to x
// assuming the array is unsorted...
function get_closest(a, x)
{
	var closest = a[0];
    var diff = Math.abs (x - closest);
    for (i = 0; i < a.length; i++) 
    {
        if (Math.abs (x - a[i]) < diff) 
        {
            diff = (Math.abs (x - a[i]));
            closest = a[i];
        }
    }
    return closest;
}

// helper function: get node id 	
function get_node_key(node_label, map_id)
{
	return "n_" + node_label + "_" + map_id;
}


// this function would updates global time and moves all spatial entities with temporal dimension to the new time state 
// potentially useful for animations or other time transitions on demand
function update_global_time(time_idx)
{
	global_time_idx = time_idx 
	
	// TO DO: REDRAW ENTITIES AT NEW TIME
}


function update_global_maps(updated_maps)
{
	console.log(Object.keys(updated_maps).length);
	maps = updated_maps;
}


// default onmouseover behavior
// TODO: fill in the function
function onmouseover_default()
{
	return;
}


//default onmouseout behavior
//TODO: fill in the function
function onmouseout_default()
{
	return;
}