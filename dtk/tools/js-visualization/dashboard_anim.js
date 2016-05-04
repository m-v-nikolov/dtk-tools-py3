var timesteps = ["14235", "14236", "14237", "14238", "14239", "14240", "14241", "14242", "14243", "14244", "14245", "14246", "14247", "14248", "14249", "14250", "14251", "14252", "14253", "14254", "14255", "14256", "14257", "14258", "14259", "14260", "14261", "14262", "14263", "14264", "14265", "14266", "14267", "14268", "14269", "14270", "14271", "14272", "14273", "14274", "14275", "14276", "14277", "14278", "14279", "14280", "14281", "14282", "14283", "14284", "14285", "14286", "14287", "14288", "14289", "14290", "14291", "14292", "14293", "14294", "14295", "14296", "14297", "14298", "14299", "14300", "14301", "14302", "14303", "14304", "14305", "14306", "14307", "14308", "14309", "14310", "14311", "14312", "14313", "14314", "14315", "14316", "14317", "14318", "14319", "14320", "14321", "14322", "14323", "14324", "14325", "14326", "14327", "14328", "14329", "14330", "14331", "14332", "14333", "14334", "14335", "14336", "14337", "14338", "14339", "14340", "14341", "14342", "14343", "14344", "14345", "14346", "14347", "14348", "14349", "14350", "14351", "14352", "14353", "14354", "14355", "14356", "14357", "14358", "14359", "14360", "14361", "14362", "14363", "14364", "14365", "14366", "14367", "14368", "14369", "14370", "14371", "14372", "14373", "14374", "14375", "14376", "14377", "14378", "14379", "14380", "14381", "14382", "14383", "14384", "14385", "14386", "14387", "14388", "14389", "14390", "14391", "14392", "14393", "14394", "14395", "14396", "14397", "14398", "14399", "14400", "14401", "14402", "14403", "14404", "14405", "14406", "14407", "14408", "14409", "14410", "14411", "14412", "14413", "14414", "14415", "14416", "14417", "14418", "14419", "14420", "14421", "14422", "14423", "14424", "14425", "14426", "14427", "14428", "14429", "14430", "14431", "14432", "14433", "14434", "14435", "14436", "14437", "14438", "14439", "14440", "14441", "14442", "14443", "14444", "14445", "14446", "14447", "14448", "14449", "14450", "14451", "14452", "14453", "14454", "14455", "14456", "14457", "14458", "14459", "14460", "14461", "14462", "14463", "14464", "14465", "14466", "14467", "14468", "14469", "14470", "14471", "14472", "14473", "14474", "14475", "14476", "14477", "14478", "14479", "14480", "14481", "14482", "14483", "14484", "14485", "14486", "14487", "14488", "14489", "14490", "14491", "14492", "14493", "14494", "14495", "14496", "14497", "14498", "14499", "14500", "14501", "14502", "14503", "14504", "14505", "14506", "14507", "14508", "14509", "14510", "14511", "14512", "14513", "14514", "14515", "14516", "14517", "14518", "14519", "14520", "14521", "14522", "14523", "14524", "14525", "14526", "14527", "14528", "14529", "14530", "14531", "14532", "14533", "14534", "14535", "14536", "14537", "14538", "14539", "14540", "14541", "14542", "14543", "14544", "14545", "14546", "14547", "14548", "14549", "14550", "14551", "14552", "14553", "14554", "14555", "14556", "14557", "14558", "14559", "14560", "14561", "14562", "14563", "14564", "14565", "14566", "14567", "14568", "14569", "14570", "14571", "14572", "14573", "14574", "14575", "14576", "14577", "14578", "14579", "14580", "14581", "14582", "14583", "14584", "14585", "14586", "14587", "14588", "14589", "14590", "14591", "14592", "14593", "14594", "14595", "14596", "14597", "14598", "14599"];
var int_id;
var time = 0;
var last_paused_time = time; 
var map;

// support up to 2 attributes to image due to geometry hardcoded details in spatial; might be able to do up to 6....
var node_attrs_img = [
                      {
                    	  'node_attr_img':"Received_ITN",
                    	  'img_scale':d3.scale.threshold().domain([0, 10]).range([0, 1, 2, 3]),
                    	  'img_src':['imgs/net.png', 'imgs/net.png', 'imgs/net.png', 'imgs/net.png']
                      },
                      {
                    	  'node_attr_img':"Received_Campaign_Drugs",
                    	  'img_scale':d3.scale.threshold().domain([0, 10]).range([0, 1, 2, 3]),
                    	  'img_src':['imgs/drugs.png', 'imgs/drugs.png', 'imgs/drugs.png', 'imgs/drugs.png']
                      }
                     ]

function load_dashboard(map_data_file)
{	
			
	var playing = false;
	d3.select(".resourcecontainer.buttons")
				.append("button")
				.attr("id","control")
				.attr("type", "button")
				.html("Play")
				.on("click", function(){ 
										
					if(!playing)
					{
						int_id = setInterval(load_snapshot, 125); 
						time = last_paused_time;
						d3.select(this).html("Pause")
						playing = true;
					}
					else
					{
						clearInterval(int_id);
						last_paused_time = time;
						time += timesteps.length+1;
						d3.select(this).html("Play")
						playing = false;
						return;
					}
										
				});
							
	
	for (var i = 0; i < node_attrs_img.length; i ++)
	{
		var node_attr_img = node_attrs_img[i]['node_attr_img'];
		var img_scale = node_attrs_img[i]['img_scale'];
		var img_src = node_attrs_img[i]['img_src'];
  	  	
		// setup an image pattern if node attribute to image map has been specified and patterns have not been created before
		var pattern_svg = d3.select("body").append("svg").attr("id", "pattern_" + node_attr_img);
		var pattern_defs = pattern_svg.append("defs").attr("id", "defs_" + node_attr_img);
		pattern_defs.selectAll("pattern")
		.data(img_scale.range())
		.enter().append("pattern")
			.attr("id", function(d) { return node_attr_img + "_" + d; })
			.attr("x", 0)
			.attr("y", 0)
			.attr("height", 17)
			.attr("width", 17)
			.insert("image")
			  .attr("x", 0)
			  .attr("y", 0)
			  .attr("height", 17)
			  .attr("width", 17)
			  .attr("xlink:href", function(d) { return img_src[d]; });
	}
	
	map = map_data_file;
	load_map(
	 		   'anim_drugs', // map id 
	 		   map, 
	 		   ".resourcecontainer.maps", //target container,
	 		   {
	 			   width:window.innerWidth-170,
	 			   height:window.innerHeight - 110,
	 			   node_attrs_img:node_attrs_img
	 		   }
	);		
	load_snapshot();
}

function load_snapshot()
{	
	
	if(time < timesteps.length - 1)
	{
		//alert(timesteps[time["idx"]]);
		style_map(
			    'anim_drugs', 
			    map,
			    {
				   time_idx : timesteps[time],
				   node_attr_2_color : ["New_Diagnostic_Prevalence", d3.scale.quantize().domain([0, 0.52]).range(colorbrewer.OrRd[9])],
				   //node_attr_2_stroke : ["Received_ITN", d3.scale.threshold().domain([0, 10]).range(['#000000','#281005','#471609','#691a0c','#8c1b0c','#b11a0a','#d71306','#ff0000'])],
				   node_attrs_2_img : node_attrs_img,
				   //node_attr_2_opacity : ["Received_Campaign_Drugs", d3.scale.threshold().domain([0, 10]).range(['0.1','0.2','0.3','0.4','0.5','0.6','0.7','0.8'])],
				   node_attr_2_radius : ["Population", d3.scale.quantize().domain([0, 10]).range([0, 12])]
			    }
		);	
		
		time ++;
		
	}
	else
	{
		clearInterval(int_id); 
		return;
	}
}