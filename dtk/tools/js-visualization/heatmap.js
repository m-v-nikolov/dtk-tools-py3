function load_heatmap(hm_id, color_scale, h, attr_2_x, attr_2_y, attr_2_z)
{
	
	axis_margin = 75; // margin left on the left and bottom of the heatmap, allowing for the display of y anx x -axis respectively 
	color_bar_margin = 50;
	
	var map_container = d3.select("body").append("div")
	.attr("id","hm_container_"+hm_id)
	.style({height:(h) + "px", width:(h + color_bar_margin) + "px"}); // assume a square heatmap for now
	
	var svg = d3.select("#hm_container_"+hm_id).append("svg")
	  .attr("class", hm_id)
	  .attr("width", (h + axis_margin + color_bar_margin))
	  .attr("height", (h + axis_margin))
	  .attr("id", "hm_" + hm_id);
	
	hm_data_file = "hm_" + hm_id + ".json";
	
	/*
	var colorbar_container = d3.select("body").append("div")
	.attr("id","colorbar_container_"+hm_id)
	.style({height:h + "px", width:h + "px"})
	*/
	
	/*
	var colorbar_svg = d3.select("#hm_container_"+hm_id).append("svg")
	.attr("class", hm_id)
	.attr("width", h)
	.attr("height", h)
	.attr("id", "colorbar_" + hm_id);
	*/

	var orientation = "vertical";
	colorbar = Colorbar()
		    .origin([h + 50,0])
		    .thickness(100)
		    .scale(color_scale).barlength(h - axis_margin).thickness(20)
		    .orient(orientation);
	
	bar =  d3.select("#hm_"+hm_id).append("g").attr("id","hm_colorbar_" + hm_id);
	pointer = d3.selectAll("#hm_colorbar_" + hm_id).call(colorbar);
	
	
	d3.json(hm_data_file, function(hm_data){
		y = Math.sqrt(hm_data["points"].length);
		tile_size = (h  - axis_margin)  / y;
		
	
		data_boundaries_x = d3.extent(hm_data["points"].map(function(d){return d[attr_2_x]}));
		data_boundaries_y = d3.extent(hm_data["points"].map(function(d){return d[attr_2_y]}));
		data_boundaries_z = d3.extent(hm_data["points"].map(function(d){return d[attr_2_z]}));
			
		dynamic_scale = d3.scale.log().domain(data_boundaries_z).range([0,1]);
		
		svg.selectAll("rect")
			.data(hm_data["points"])
			.enter().append("rect")
			.attr("width", tile_size)
			.attr("height", tile_size)
			.attr("y", function(d){ return h - tile_size*d.y_idx - axis_margin; })
			.attr("x", function(d){ return axis_margin + tile_size*d.x_idx; })
			.attr("data-toggle", "tooltip")
			.attr("data-placement", "top")
			.attr("html", true) // tooltip style can be further improved via bootstrap css options
			.attr("title", function(d){ return "(" + d[attr_2_x] + ", " + d[attr_2_y] + ", " + d[attr_2_z]+")"; })
			.attr("fill", function(d) {		
				
				return color_scale(dynamic_scale(d[attr_2_z]));
				//return color_scale(d.zi);
			})
			.on("mouseover",function(d) {pointer.pointTo(dynamic_scale(d[attr_2_z]))})
			.attr("id", function(d) { return d[attr_2_x] + "_" + d[attr_2_y]} )
			.style("stroke", function(d) { return color_scale(dynamic_scale(d[attr_2_z])); /*return color_scale(d.zi);*/ });
		

		var x_axis = d3.svg.axis().scale(d3.scale.linear().domain(data_boundaries_x).range([axis_margin,h])).orient("bottom");
		var y_axis = d3.svg.axis().scale(d3.scale.linear().domain(data_boundaries_y).range([h - axis_margin,0])).orient("left");

		//axis_box = svg.append("g").attr("transform", "translate(" + 0 + "," + 20 + ")");
		
		svg.append("g")
	      .attr("class", "x axis")
	      .attr("transform", "translate(0," + (h - axis_margin/2) + ")")
	      .call(x_axis)
	      .append("text")
	        .text(attr_2_x)
	        .attr("x", axis_margin)
	        .attr("y", -10)
	        .attr("dx", ".71em");
		
	    svg.append("g")
	      .attr("class", "y axis")
	      .attr("transform", "translate(35," + 0 + ")")
	      .call(y_axis)
	      .append("text")
	        .text(attr_2_y)
	        .attr("x",-h + 2*axis_margin + 15)
	        .attr("y",10)
	        .style("text-anchor", "end")
	        .attr("transform", "rotate(270)")
	        .attr("dy", ".71em");
	});
}
