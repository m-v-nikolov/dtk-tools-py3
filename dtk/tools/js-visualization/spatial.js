/* 
 * A global object of leaflet maps accessible to everyone in this file;
 * reason: one cannot extract leaflet maps from html DOM and passing leaflet 
 * map objects across various d3js/js objects might be tedious 
 * (the latter could still be the better design choice though... ?)
 * 
 * object structure:
 * 
 * maps = {
 * 			map_id:leaflet_map // map_id is user supplied; the leaflet map is created in load_map
 * 		  }

 */
var maps = {};



function load_map(map_id, map_json, target_container, params)
{	
		target_container = typeof target_container !== 'undefined' ? target_container : "body";
		
		var height = 400;
		var width = 500;
		var node_attrs_img_prop = false;
		var additional_layers = false;
		var base_tile_layer = false;
		
		if(params.hasOwnProperty("height"))
			height = params["height"];
		if(params.hasOwnProperty("width"))
			width = params["width"];
		if(params.hasOwnProperty("node_attrs_img"))
			node_attrs_img_prop = params["node_attrs_img"];
		if(params.hasOwnProperty("additional_layers"))
			additional_layers = params["additional_layers"];
		
		// base layer is always the first one in the layers array
		if(params.hasOwnProperty('base_tile_layer'))
			base_tile_layer = params.base_tile_layer;
	
		var map_decorations_container = d3.select(target_container).append("div")
										.attr("id","map_decorations_container_"+map_id)
										.attr("class", "map_decorations_container");
	
		var map_container = d3.select("#map_decorations_container_" + map_id).append("div")
							.attr("id","map_container_"+map_id)
							.style({height:height + "px", width:width + "px", float:"left"}); // expose width/height as parameters?
	
		//var map = L.map("map_container_"+map_id, { attributionControl:false, crs: L.CRS.EPSG4326 }).setView([47.5826601,-122.1533733], 13);
		var map = L.map("map_container_"+map_id, { attributionControl:false, crs: L.CRS.EPSG3857 }).setView([47.5826601,-122.1533733], 13);
		
		mapLink = '<a href="http://openstreetmap.org">OpenStreetMap</a>'; 
		



		/*
		tile_layer = L.tileLayer('http://{s}.tile.thunderforest.com/landscape/{z}/{x}/{y}.png', {
			attribution: '&copy; <a href="http://www.thunderforest.com/">Thunderforest</a>, &copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
	   	  }).addTo(map);
	   	  */
		var tile_layer;
		if(base_tile_layer)
			tile_layer = base_tile_layer;
		else
		{
			tile_layer = L.tileLayer('http://{s}.tile.thunderforest.com/landscape/{z}/{x}/{y}.png', {
				attribution: '&copy; <a href="http://www.thunderforest.com/">Thunderforest</a>, &copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
		   	  })
		}
		
		tile_layer.addTo(map);
		
		/* Initialize the SVG layer */
		map._initPathRoot();
		
		var svg = d3.select("#map_container_"+map_id).select("svg")
		  .attr("id", map_id);
	
		maps[map_id] = {
				"map":map,
				"layers":[tile_layer]
				}
		
		// add any additional layers specified (e.g. server side wms QGIS)
		if(additional_layers)
		{
			for(var i = 0; i < additional_layers.length; i++)
			{
				maps[map_id]["layers"].push(additional_layers[i]);
				additional_layers[i].addTo(map)
			}
		}
		
	
		d3.json(map_json, function(map_nodes){ 
		
			var markers = [];
			var nodes = [];
			
			// for now have a limit of three attribtues to image (i.e. three arrays of nodes) due to geometry limitations; might be able to go to up to 6 with current layout?
			var nodes_2_imgs = {};
			var nodes_2_img = [];
						
			map_nodes.forEach(function(d) {
				
				markers.push(new L.LatLng(d.Latitude, d.Longitude))
				nodes.push({
								coor:new L.LatLng(d.Latitude, d.Longitude), 
								node:d
								});
				
				/*
				 * 
				 * node_attrs_img_prop sample format:
				 * 
				 * var node_attrs_img_prop = [
                      {
                    	  'node_attr_img':"Received_ITN",
                    	  'img_scale':d3.scale.threshold().domain([0, 10]).range([0, 1, 2, 3]),
                    	  'img_src':['imgs/net.png', 'imgs/net.png', 'imgs/net.png', 'imgs/net.png']
                      },
				 * 
				 */
				if(node_attrs_img_prop)
				{
					nodes_2_img.push({
						coor:new L.LatLng(d.Latitude, d.Longitude), 
						node:d
					});
				}
			})
			
			for (var i = 0; i < node_attrs_img_prop.length; i ++)
			{		
				nodes_2_imgs[node_attrs_img_prop[i]['node_attr_img']] = {};
				nodes_2_imgs[node_attrs_img_prop[i]['node_attr_img']]['nodes'] = nodes_2_img;
			}	
			
			
			//maps[map_id]["nodes_2_imgs"] = nodes_2_imgs;
			//maps[map_id]["nodes"] = nodes;
			
			var bounds = new L.LatLngBounds(markers);
			
			
			/* 
			 * Should nodes be displayed on load_map?
			 * Perhaps the most generic map should only contain 
			 * a base map layer and avoid rendering additional objects?
			 * 
			 * This behavior can easily be refactored.
			 */
			
			g = svg.append("g")
				.attr("class","map")
				.attr("id","svgNodesContainer");
			
			var node = g.selectAll("[node-group="+map_id+"]")
			.data(nodes)
			.enter().append("circle")
			.attr("r", 10)  
			.attr("id", function(d) {return get_node_key(d.node.NodeLabel, map_id)})
			.attr("ttl",100)
			.attr("node-group", map_id)
			.attr("class", function(d) {return d.node.NodeLabel});
			
			for (var i = 0; i < node_attrs_img_prop.length; i ++)
			{	
				var node_attr_img = node_attrs_img_prop[i]['node_attr_img'];
				var nodes = nodes_2_imgs[node_attr_img]['nodes'];
				
				nodes_2_imgs[node_attr_img]['markers'] = g.selectAll("." + node_attr_img)
				.data(nodes)
				.enter().append("circle")
				.attr("r", 6.5)  // might expose that as a parameter
				.attr("id", function(d) {return "attr" + node_attr_img  + "_" + get_node_key(d.node.NodeLabel, map_id)})
				.attr("class", function(d) {return node_attr_img  })
				//.attr("opacity", 1.0)
				//.attr("fill", "red")
				.attr("opacity", 0.0)
				.attr("ttl", 0);
			}
				
			map.on("viewreset", update);
			update();
			
			
			function update() {
				node.attr("transform", 
				function(d) { 
					return get_node_map_position(d.node, map);
				})	
				
				for (var i = 0; i < node_attrs_img_prop.length; i ++)
				{
					var node_attr_img = node_attrs_img_prop[i]['node_attr_img'];
					var node_2_img = nodes_2_imgs[node_attr_img]['markers']
					
					// again, currently only up to four attributes would be displayed due to geometry
					var offset_x = 0;
					var offset_y = 0;
					
					if(i == 0)
					{
						offset_x = -5;
						offset_y = -5;
					}
					else
					if(i == 1)
					{
						offset_x = 5;
						offset_y = -5;
					}
					else
					if(i == 2)
					{
						offset_x = -5;
						offset_y = 5;
					}
					else
					if(i == 3)
					{
						offset_x = 5;
						offset_y = 5;
					}
					else
						continue;
					
					node_2_img.attr("transform", 
						function(d) { 
							return "translate("+ 
								(map.latLngToLayerPoint(d.coor).x + offset_x) +","+ 
								(map.latLngToLayerPoint(d.coor).y + offset_y) +")";
						})	
				}
			}
			
			map.fitBounds(bounds);
			
		});// end d3.json(...)
		
	return;
}


function style_map(
						map_id,
						map_json,
						map_properties, // object
						comm_msg // see comms.js for documentation on communication message
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
	 
	/* for now do not allow swapping the base layer; if not transparent it would cover any pther layers added before it upon map load
	// base layer is always the first one in the layers array
	if(!map_properties.hasOwnProperty('base_tile_layer'))
		var base_tile_layer = false;
	else
		var base_tile_layer = map_properties.base_tile_layer;
		*/
	
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
		var additional_layers = false;
	else
		var additional_layers = map_properties.additional_layers;
	
	// map the value of entity node's specific attribute to node marker color
	if(!map_properties.hasOwnProperty('node_attr_2_color'))
	{
		var node_color = "gray";
		var node_attr_2_color = false;
	}
	else
	{
		var node_attr_2_color = map_properties.node_attr_2_color;
		var node_attr_color = node_attr_2_color[0];
		var color_scale = node_attr_2_color[1];
		
		// add attribute node_attr_2_color to map object
		maps[map_id]["node_attr_2_color"] = node_attr_2_color
	}
	
	// map the value of entity node's specific attribute to node marker radius
	if(!map_properties.hasOwnProperty('node_attr_2_radius'))
	{
		var node_radius = 500;
		var node_attr_2_radius = false;
	}
	else
	{
		var node_attr_2_radius = map_properties.node_attr_2_radius;
		var node_attr_radius = node_attr_2_radius[0];
		var radius_scale = node_attr_2_radius[1];
		
		// add attribute node_attr_2_radius to map object
		maps[map_id]["node_attr_2_radius"] = node_attr_2_radius
	}
	
	if(!map_properties.hasOwnProperty('node_attr_2_stroke'))
	{
		var node_stroke = "gray";
		var node_attr_2_stroke = false;
	}
	else
	{
		var node_attr_2_stroke = map_properties.node_attr_2_stroke;
		var node_attr_stroke = node_attr_2_stroke[0];
		var stroke_scale = node_attr_2_stroke[1];
		
		// add attribute node_attr_2_radius to map object
		maps[map_id]["node_attr_2_stroke"] = node_attr_2_stroke
	}
	
	// node marker's opacity on map
	var node_opacity;
	if(!map_properties.hasOwnProperty('node_attr_2_opacity'))
	{
		node_opacity = 0.6;
		var node_attr_2_opacity = false;
	}
	else
	{
		var node_attr_2_opacity = map_properties.node_attr_2_opacity;
		
		var node_attr_opacity = node_attr_2_opacity[0];
		var opacity_scale = node_attr_2_opacity[1];
		
		// add attribute node_attr_2_opacity to map object
		maps[map_id]["node_attr_2_opacity"] = node_attr_2_opacity
	}
	
	if(!map_properties.hasOwnProperty('node_opacity'))
	{
		node_opacity = 0.6;
		node_attr_2_opacity = false; // override node_attr_2_opacity
	}
	else
	{
		node_opacity = map_properties['node_opacity'];
		maps[map_id]["node_opacity"] = map_properties['node_opacity'];
	}

	// node marker's background image map to attributes
	if(!map_properties.hasOwnProperty('node_attrs_2_img'))
	{
		var node_attrs_img_prop = false;
	}
	else
	{
		var node_attrs_img_prop = map_properties.node_attrs_2_img;

		// add attribute node_attr_2_img to map object
		maps[map_id]["node_attrs_2_img"] = node_attrs_img_prop;
	}

	
	// node marker's background image map to events
	if(!map_properties.hasOwnProperty('node_events_2_img'))
	{
		var node_events_img_prop = false;
	}
	else
	{
		var node_events_img_prop = map_properties.node_events_2_img;

		// add attribute node_attr_2_img to map object
		maps[map_id]["node_events_2_img"] = node_events_img_prop;
	}
	
	// if node attribute has a temporal dimension, pick how to fill in missing values
	// currently available options are
	// "closest_time": pick the value for the closest available time to the missing one (default)
	// "zero": fill in the missing values with zeros
	if(!map_properties.hasOwnProperty('missing_values'))
	{
		var missing_values = "closest_time";
	}
	else
	{
		var missing_values = map_properties.missing_values;
	}
	
	/*
	//behavior of node marker's on mouse over is function onmouseover
	if(!map_properties.hasOwnProperty('onmouseover'))
		onmouseover = onmouseover_default;
	else
		var onmouseover = map_properties.onmouseover;
	*/
	// behavior of node marker's on mouse out is function onmouseout
	if(!map_properties.hasOwnProperty('onmouseout'))
		var onmouseout = onmouseout_default;
	else
		var onmouseout = map_properties.onmouseout; 
	
	
	var map = maps[map_id]["map"];
	var map_layers = maps[map_id]["layers"];
	
	
	// add additional layers to the map (useful to add roads, etc.); by default no new additional layers are provided
	if(additional_layers)
	{
		for(i = 0; i < additional_layers.length; i++)
		{
			additional_layers[i].addTo(map);
			map_layers.push(additional_layers[i]);
		}
	}
	
	
	// set local map time if provided
	var local_time = 0;
	if(time_idx)
		local_time = time_idx;
	else
	{
		// check if global_time_idx is defined by coms.js (e.g. comms.js was imported)
		if(typeof global_time_index !== 'undefined')
			local_time = global_time_idx;	
		
	}
	//alert("in style_map with time " + local_time);

	// add attribute time to map object
	maps[map_id]["time"] = local_time;

	// add attribute onmouseover
	//maps[map_id]["onmouseover"] = onmouseover
	// add attribute onmouseover
	//maps[map_id]["onmouseout"] = onmouseout
	
	var color_bar_orientation = "vertical";
	
	if(node_attr_2_color && d3.select("#colorbar_container_"+map_id).empty())
	{
		var colorbar = Colorbar() // expose colorbar parameters? probably not needed...
			    .origin([35,-5])
			    .thickness(100)
			    .scale(color_scale).barlength(map_height).thickness(20)
			    .orient(color_bar_orientation)
			    .margin({top:20, left:30, right:55, bottom:10});
		
		var bar_container =  d3.select("#map_decorations_container_"+map_id)
							.append("div")
							.attr("id", "colorbar_container_"+map_id)
							.attr("class", "colorbar_container");
		
		var bar = d3.select("#colorbar_container_"+map_id)
							.append("svg")
							.attr("width", 100)
							.attr("height", map_height + 10)
							.append("g")
							.attr("id","colorbar_"+map_id);
		
		var pointer = d3.selectAll("#colorbar_" + map_id).call(colorbar)
	}
	
	
	// traverse nodes and set respective map markers style
	//d3.json(map_json, function(map_nodes){
	map_nodes = d3.selectAll("[node-group="+map_id+"]").data();	
	
	map_nodes.forEach(function(d){	

			var node = d.node;
			//var node = d;
						
		    var node_key = get_node_key(node.NodeLabel, map_id);

			/*
			 * set the style of each node's marker
			 */
			
			d3.select("#" + node_key)
			.attr("fill", function (d) {
                var c = 'white';    
                                
               // if an attribute to image has not been specified assign fill to color, given attribute to color has been specified
                if(node_attr_2_color)
                {
                	if(d.node.hasOwnProperty(node_attr_color))
                	{
                		var val = fill_missing_values(d.node[node_attr_color], local_time, missing_values);
                		
                	}
                	else
                		return d3.select(this).attr("fill"); // keep the current attribute value if no new one is available
                }
                else
                {
                	return node_color;
                }
                
            	if (val >= 0) { c = color_scale(val); }
            	else { c = 'gray'; }
            	
            	return c;
			})
			.attr("stroke", function (d) {
                var c = 'white';
                if(node_attr_2_stroke)
                	if(d.node.hasOwnProperty(node_attr_stroke))
                		var val = fill_missing_values(d.node[node_attr_stroke], local_time, missing_values);
                	else
                		return d3.select(this).attr("stroke"); // keep the current attribute value if no new one is available
                else
                	return node_stroke;

            	if (val >= 0) { c = stroke_scale(val); }
            	else { c = 'gray'; }
            	
            	return c;
			})
			.attr("r", function (d) { 
				if(node_attr_2_radius)
					if(d.node.hasOwnProperty(node_attr_radius))
						var val = fill_missing_values(d.node[node_attr_radius], local_time, missing_values);
					else
						return d3.select(this).attr("r"); // keep the current attribute value if no new one is available
				else
					radius_scale(node_radius);
				return radius_scale(val);
			})
			.attr("opacity", function(d){
				if(node_attr_2_opacity)
					if (d.node.hasOwnProperty(node_attr_opacity))
						var val = fill_missing_values(d.node[node_attr_opacity], local_time, missing_values);
					else
						return d3.select(this).attr("opacity"); // keep the current attribute value if no new one is available
				else
				{
					return node_opacity;
				}
					
				return opacity_scale(val);
			})
			//all of the below options (e.g. tooltip attributes) can be exposed on per map basis as map styling properties)
			.attr("data-toggle", "tooltip")
			.attr("data-placement", "top")
			.attr("emitted", false)
			.attr("html", true) // tooltip style can be further improved via bootstrap css options
			/*
			.attr("title", function(d){
				
				var val = get_entity_value(d.node[node_attr_color], local_time);
				
				if (val < 0) { val = 'N/A'; }
			    else { val = val } // keep else as place holder; might want to expose formatting options as function arguments to get something along the lines of d3.format('%')(val);
				
				return  d.node.NodeLabel + ": " + node_attr_color + ": " + val;
			})
			.style("stroke", "gray")
			*/
			.on("mouseover",function(d) { 
											if(node_attr_2_color)
											{
												pointer.pointTo(get_entity_value(d.node[node_attr_color], local_time));
											}
											comm_msg = typeof comm_msg !== 'undefined' ? comm_msg : false;

											if (typeof(trigger_emit) == "function" && typeof(parse_comm_msg) == "function" && comm_msg !== false && comm_blacklist.indexOf(d3.select(this).attr("id")) == -1)
											{
												// parse comm_msg and, if requested, bind data attributes from d to comm_msg
												//comm_msg = parse_comm_msg(comm_msg, {"NodeLabel":"80202_5"});
												comm_msg = parse_comm_msg(comm_msg, d.node);
												
												// emit comm_msg
												trigger_emit(this, comm_msg);
											}
			}); // end setting node styles
			//alert(node.NodeLabel);
			
			
			/*
			 * if a map from node attributes to images is given,
			 *  style the corresponding node images 
			 */
			if(node_attrs_img_prop)
			{
				
				for (var i = 0; i < node_attrs_img_prop.length; i ++)
				{
					var node_attr_img = node_attrs_img_prop[i]['node_attr_img'];
					var img_scale = node_attrs_img_prop[i]['img_scale'];
					var img_src = node_attrs_img_prop[i]['img_src'];
				
					var node_attr_img_marker = d3.select("#attr" + node_attr_img + "_" + node_key)
						.attr("fill", function (d) {
							if(d.node.hasOwnProperty(node_attr_img))
							{
								var val = fill_missing_values(d.node[node_attr_img], local_time, false);
								
								if (val) // if a val is provided reset ttl
								{
									d3.select(this).attr("ttl", 20);
									//if(node_attr_img == "Received_Treatment")
									//	alert(img_scale(val));
									return "url(#attr" + node_attr_img + "_" + img_scale(val) +")";
								}
								else // if no value is returned (i.e. val is false) decrement ttl
								{
									var ttl = d3.select(this).attr("ttl");
									
									if(ttl > 0)
										d3.select(this).attr("ttl", ttl - 1);
									return d3.select(this).attr("fill");
								}
							}
							else
							{
								// if the node does not have the requested image attribute; set its ttl to 0; this would render it infvisible )opacity would be 0.0
								d3.select(this).attr("ttl", 0);
								
							}
						})
						.attr("opacity", function(){
								var ttl = d3.select(this).attr("ttl");
								return ttl/20.0; // might want to expose decay function
						});
				}
			}
			
			
			
			/*
			 * if a map from node events to images is given,
			 *  create the corresponding event node images (if event is available at the current time)
			 *  and/or style them  
			*/
			if(node_events_img_prop)
			{
				for (var i = 0; i < node_events_img_prop.length; i ++)
				{
					var node_event_img = node_events_img_prop[i]['node_event_img'];
					var img_scale = node_events_img_prop[i]['img_scale'];
					var img_src = node_events_img_prop[i]['img_src'];
					

					if(node.hasOwnProperty(node_event_img))
					{
						var val = fill_missing_values(node[node_event_img], local_time, false);
						
						//select event node
						var event_node = d3.select("#" + node_key);
						
						// select event node image
						var event_node_image = d3.select("#event" + node_key);
					
						if (val) // there is an event at this time
						{	
							// check if event node image for this event node has already been added
							if(event_node_image.empty()) // if event node image for this event node has not been added, add event node image
							{
								
								// copy the event node and add it to the container (it will appear on top of the original event node, with fill equal to the corresponding event image, and opacity 1.0)
								// ttl will be set to the maximum value; currently hard coded to 10; might want to expose as a parameter
								copy_d3_object(event_node, {"node-group":"clone"+map_id, "ttl":20, "opacity":1.0, "fill":function(d){return "url(#event" + node_event_img + "_" + img_scale(val) +")";}}, "event" + node_key)
								
								// at this point the event image is the fill of the event node and is visible
								// the original event node is below and invisible) 
							}
							else // event node image for this node has already been added 
							{
								// adjust attributes of event node image as needed
								event_node_image.attr("fill", function(d){return "url(#event" + node_event_img + "_" + img_scale(val) +")";})
												.attr("ttl", 20) //set time to live attribute to max (i.e. 10; this can be exposed as a parameter?)
												.attr("opacity", 1.0) // set opacity to 0.0
							}
						}
						else // there is no event; decrement ttl of currently present event node image (if any)
						{
							if(!event_node_image.empty())
							{
								// if the time to live of the event image is 0 remove the event image and restore the original fill;
								// else fade out the event node's copy and decrement its time to live value
								var ttl = event_node_image.attr("ttl");
								
								if(ttl > 0)
								{
									event_node_image.attr("ttl", ttl - 1);
									event_node_image.attr("opacity", function(){
										// might want to expose decay/fadeout function
										return ((ttl-1)/20.0); // decrease (opacity w/ decreasing ttl) of event node copy
									});
								}
								else //ttl = 0
								{
									// remove event node image;
									event_node_image.remove()
								}				
							}
							// if there is no event node image do nothing
						}
					} // end the case where node has the event type
				} // end node event types for loop 	
			} // end case where events images are provided 
		}); // end looping over nodes
	//}); // end d3.json(...)
} // end function style_map(...)


function load_2d_scatter(	
							scatter_id,
							scatter_json,
							scatter_properties, // object
							target_container, 
							comm_msg
						 )
{
	
	
	target_container = typeof target_container !== 'undefined' ? target_container : "body";
	
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
	
	// behavior of node marker's on mouse out is function onmouseout
	if(!scatter_properties.hasOwnProperty('onmouseout'))
		var onmouseout = onmouseout_default;
	else
		var onmouseout = scatter_properties.onmouseout;
	
	
	// set local map time if provided
	var local_time = 0;
	if(time_idx)
		local_time = time_idx;
	else
	{
		// check if global_time_idx is defined by coms.js (e.g. comms.js was imported)
		if(typeof global_time_index !== 'undefined')
			local_time = global_time_idx;	
		
	}
	
	var node_attr_color = node_attr_2_color[0];
	var color_scale = node_attr_2_color[1];

	var node_attr_radius = node_attr_2_radius[0];
	var radius_scale = node_attr_2_radius[1];
	
	
	var margin = {top: 50, right: 20, bottom: 50, left: 40}, // expose margins as parameters?
    width = scatter_width - margin.left - margin.right,
    height = scatter_height - margin.top - margin.bottom;
	
	var scatter_decorations_container = d3.select(target_container).append("div")
											.attr("id","scatter_decorations_container_"+scatter_id)
											.attr("class","scatter_decorations_container");

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
		    .origin([35, margin.top - 20])
		    .thickness(100)
		    .scale(color_scale).barlength(height).thickness(20)
		    .orient(color_bar_orientation)
		    .margin({top:20, left:30, right:55, bottom:10});
	
	
	var bar_container =  d3.select("#scatter_decorations_container_"+scatter_id)
						.append("div")
						.attr("id", "colorbar_container_"+scatter_id)
						.attr("class", "colorbar_container");
	
	var bar = d3.select("#colorbar_container_"+scatter_id)
						.append("svg")
						.attr("width", 100)
						.attr("height", height + 10)
						.append("g")
						.attr("id","colorbar_"+scatter_id);
	
	var pointer = d3.selectAll("#colorbar_" + scatter_id).call(colorbar)
	
	
	// traverse nodes and set respective scatter markers style
	// TODO: optimize as in style_map so that we don't need to re-load nodes
	// this would automatically fall in place once style_map/load_map are just extensions of load_2d_scatter;
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
                var val = get_entity_value(d[node_attr_color], local_time);

            	if (val >= 0) { c = color_scale(val); }
            	else { c = 'gray'; }
            	
            	return c;
			})
			.attr("r", function (d) { 
				var val = get_entity_value(d[node_attr_radius], local_time);
				return radius_scale(val);
			})
			.attr("opacity", node_opacity)
			//all of the below options (e.g. tooltip attributes) can be exposed on per scatter basis as scatter styling properties)
			.attr("data-toggle", "tooltip")
			.attr("data-placement", "top")
			.attr("emitted", false)
			.attr("html", true) // tooltip style can be further improved via bootstrap css options
			.attr("title", function(d){
				
				var val = get_entity_value(d[node_attr_color], local_time);
				if (val < 0) { val = 'N/A'; }
			    else { val = val } // keep else as place holder; might want to expose formatting options as function arguments to get something along the lines of d3.format('%')(val);
				
				return  d.NodeLabel + ": " + node_attr_color + ": " + val;
			})
			.style("stroke", "gray")
			.on("mouseover", function(d) { 
								// if value is greater than the maximum colorbar domain point to the maximum of the colorbar domain
								pointer.pointTo(d3.min([d3.max(color_scale.domain()),get_entity_value(d[node_attr_color], local_time)]));
								
								comm_msg = typeof comm_msg !== 'undefined' ? comm_msg : false;
								// if this element has not emitted a message for this mouseover event, then emit
								
								if (typeof(trigger_emit) == "function" && typeof(parse_comm_msg) == "function" && comm_msg !== false && comm_blacklist.indexOf(d3.select(this).attr("id")) == -1)
								{
									// parse comm_msg and, if requested, bind data attributes from d to comm_msg
									// use {"NodeLabel":"80202_5"} as a test substitute for d; will remove when the rest of nodes ' data is generated 
									//comm_msg = parse_comm_msg(comm_msg, {"NodeLabel":"80202_5"});
									comm_msg = parse_comm_msg(comm_msg, d);
									
									// emit comm_msg
									trigger_emit(this, comm_msg);
								}
			});  

			
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


/*
 * helper function: given a d3 selection object, copy it and add the element to DOM
 * attrs: specify a set of attributes and their values that
 * would be skipped during cloning and will be changed; format
 * attrs = {
 * 			"fill":fill_val,
 * 			"opacity": opacity_val,
 * 			...
 * }
 * 
 * id: the new element id
 * 
 */
function copy_d3_object(d3obj, attrs_spec, id) 
{	    
	var attrs = d3obj.node().attributes;
	var node_name = d3obj.property("nodeName");
	var parent = d3.select(d3obj.node().parentNode);
	var copy_obj = parent.append(node_name)
	         .attr("id", id);
	for (var j = 0; j < attrs.length; j++) 
	{ 
		var attr = attrs[j];
		var attr_name = attr.name;
		var attr_val =  attr.value;
		//var d3obj_id =  attr.nodeName;
		
		if (attr_name == "id") continue;
		if(attrs_spec.hasOwnProperty(attr_name))
			copy_obj.attr(attr_name, attrs_spec[attr_name]);
		else
			copy_obj.attr(attr_name, attr_val);
	}
	
	return copy_obj;
}


/*
 * helper function: given node entry return node transform so that the node is properly position on a leaflet map
 */
function get_node_map_position(node, map)
{
	var coor = new L.LatLng(node.Latitude, node.Longitude);
	
	return "translate("+ 
		map.latLngToLayerPoint(coor).x +","+ 
		map.latLngToLayerPoint(coor).y +")";
}
	
// helper function resolving missing values method
function fill_missing_values(entity, local_time, interp_type)
{
		return get_entity_value(entity, local_time, interp_type);
}


//helper function setting missing values to provided default value
function default_missing_values(default_val)
{
	return default_val;
}

// helper function: given an entity check if it has temporal dimension and extract the proper value at
// the specified time (or just get the spatial scalar if the entity does not have temporal dimension)
// if the entity does not have associated value at the specified time, interpolate as specified by interp_type
function get_entity_value(entity, local_time, interp_type)
{
	var val = 0;
	
	// check if entity has a temporal dimension; this approach to time handling might need to be re-thought
    if(entity.hasOwnProperty("time"))
    {
    	if(!entity.hasOwnProperty(local_time+""))
    	{
    		if(interp_type != false)
    		{
    	
    			times = [];
	    		for(var key in entity)
	    			if (Object.prototype.hasOwnProperty.call(entity, key) && key != "time") // avoiding screwiness in older IE versions 
	    		        times.push(parseInt(key));
	        	
	    		// if the entity has a temporal dimension but does not have a state for the given time
	        	// find the closest time for which the entity has a state, where "closest" is determined by the interp_type attribute 
	        	// note that this can and must be optimized if dealing with large time arrays
	        	var closest_time = local_time;
	    		if(interp_type == "closest_time")
	    		{
		    		closest_time = get_closest(times, local_time);
		    		val = entity[closest_time + ""];
	    		}
	    		else
	    		if(interp_type == "closest_time_lower")
	    		{
	    			closest_time = get_closest_lower(times, local_time);
	    			val = entity[closest_time + ""];
	    		}
	    		if(interp_type == "from_window")
	    		{
	    			val = get_window_avg(entity, local_time);
	    		}
	    		else
	    		if(interp_type == "default")
	    			val = 0.0;
    		}
    		else // if interp_type is false; do not interpolate, and return false
    			val = false;
    	}
    	else
    	{
    		val = entity[local_time]; // if entity has value at the given time, do not interpolate and just return the value
    	}
    }
    else
    	val = entity;  // else entity is scalar

    return val;
}
	

// helper function: given an key,value map find the average of the values within a window key-neighborhood/window from the provided key x

function get_window_avg(entity, local_time)
{
	var time_window = [];

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

//helper function: given 1D array a of numbers, find the element y in a closest in value to x such that y < x
//assuming the array is unsorted...
function get_closest_lower(a, x)
{
 var closest = a[0];
 var diff = Math.abs(x - closest);
 for (i = 0; i < a.length; i++) 
 {
     if (Math.abs(x - a[i]) < diff && x - a[i] >= 0) 
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
	
	// TODO: REDRAW ENTITIES AT NEW TIME
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