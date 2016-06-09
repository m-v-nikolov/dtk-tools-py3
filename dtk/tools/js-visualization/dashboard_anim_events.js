var timesteps = ["14235", "14236", "14237", "14238", "14239", "14240", "14241", "14242", "14243", "14244", "14245", "14246", "14247", "14248", "14249", "14250", "14251", "14252", "14253", "14254", "14255", "14256", "14257", "14258", "14259", "14260", "14261", "14262", "14263", "14264", "14265", "14266", "14267", "14268", "14269", "14270", "14271", "14272", "14273", "14274", "14275", "14276", "14277", "14278", "14279", "14280", "14281", "14282", "14283", "14284", "14285", "14286", "14287", "14288", "14289", "14290", "14291", "14292", "14293", "14294", "14295", "14296", "14297", "14298", "14299", "14300", "14301", "14302", "14303", "14304", "14305", "14306", "14307", "14308", "14309", "14310", "14311", "14312", "14313", "14314", "14315", "14316", "14317", "14318", "14319", "14320", "14321", "14322", "14323", "14324", "14325", "14326", "14327", "14328", "14329", "14330", "14331", "14332", "14333", "14334", "14335", "14336", "14337", "14338", "14339", "14340", "14341", "14342", "14343", "14344", "14345", "14346", "14347", "14348", "14349", "14350", "14351", "14352", "14353", "14354", "14355", "14356", "14357", "14358", "14359", "14360", "14361", "14362", "14363", "14364", "14365", "14366", "14367", "14368", "14369", "14370", "14371", "14372", "14373", "14374", "14375", "14376", "14377", "14378", "14379", "14380", "14381", "14382", "14383", "14384", "14385", "14386", "14387", "14388", "14389", "14390", "14391", "14392", "14393", "14394", "14395", "14396", "14397", "14398", "14399", "14400", "14401", "14402", "14403", "14404", "14405", "14406", "14407", "14408", "14409", "14410", "14411", "14412", "14413", "14414", "14415", "14416", "14417", "14418", "14419", "14420", "14421", "14422", "14423", "14424", "14425", "14426", "14427", "14428", "14429", "14430", "14431", "14432", "14433", "14434", "14435", "14436", "14437", "14438", "14439", "14440", "14441", "14442", "14443", "14444", "14445", "14446", "14447", "14448", "14449", "14450", "14451", "14452", "14453", "14454", "14455", "14456", "14457", "14458", "14459", "14460", "14461", "14462", "14463", "14464", "14465", "14466", "14467", "14468", "14469", "14470", "14471", "14472", "14473", "14474", "14475", "14476", "14477", "14478", "14479", "14480", "14481", "14482", "14483", "14484", "14485", "14486", "14487", "14488", "14489", "14490", "14491", "14492", "14493", "14494", "14495", "14496", "14497", "14498", "14499", "14500", "14501", "14502", "14503", "14504", "14505", "14506", "14507", "14508", "14509", "14510", "14511", "14512", "14513", "14514", "14515", "14516", "14517", "14518", "14519", "14520", "14521", "14522", "14523", "14524", "14525", "14526", "14527", "14528", "14529", "14530", "14531", "14532", "14533", "14534", "14535", "14536", "14537", "14538", "14539", "14540", "14541", "14542", "14543", "14544", "14545", "14546", "14547", "14548", "14549", "14550", "14551", "14552", "14553", "14554", "14555", "14556", "14557", "14558", "14559", "14560", "14561", "14562", "14563", "14564", "14565", "14566", "14567", "14568", "14569", "14570", "14571", "14572", "14573", "14574", "14575", "14576", "14577", "14578", "14579", "14580", "14581", "14582", "14583", "14584", "14585", "14586", "14587", "14588", "14589", "14590", "14591", "14592", "14593", "14594", "14595", "14596", "14597", "14598", "14599"];
//var timesteps = ["14476", "14477", "14478", "14479", "14480", "14481", "14482", "14483", "14484", "14485"];
var int_id;
var time = 0;
var last_paused_time = time; 
var map;

// support up to 4 attributes to image due to geometry hardcoded details in spatial; might be able to do up to 6....

var node_attrs_img = [
                      {
                    	  'node_attr_img':"Received_ITN",
                    	  'img_scale':d3.scale.threshold().domain([0, 1]).range([0, 1, 2, 3]),
                    	  'img_src':['imgs/net.png', 'imgs/net.png', 'imgs/net.png', 'imgs/net.png']
                      },
                      {
                    	  'node_attr_img':"Received_Campaign_Drugs",
                    	  'img_scale':d3.scale.threshold().domain([0, 1]).range([0, 1, 2, 3]),
                    	  'img_src':['imgs/drugs.png', 'imgs/drugs.png', 'imgs/drugs.png', 'imgs/drugs.png']
                      },
                      {
                    	  'node_attr_img':"Received_Treatment",
                    	  'img_scale': d3.scale.threshold().domain([-0.1,1.1]).range([0,1]),
                    	  'img_src': ['imgs/treatment_jaline.png', 'imgs/treatment_jaline.png']
                      },
                      {
                          'node_attr_img': "NewClinicalCase",
                          'img_scale': d3.scale.threshold().domain([-0.1,1.1]).range([0,1]),
                          'img_src': ['imgs/case_jaline.png', 'imgs/case_jaline.png']
                      }
                     ]


//map events, over the node time horizon, to images

var node_events_img = [
                      {
                    	  'node_event_img':"Received_ITN",
                    	  'img_scale':d3.scale.quantize().domain([0, 1]).range([0, 1, 2, 3]),
                    	  'img_src':['imgs/net.png', 'imgs/net.png', 'imgs/net.png', 'imgs/net.png']
                      },
                      
                      {
                    	  'node_event_img':"Received_Campaign_Drugs",
                    	  'img_scale':d3.scale.quantize().domain([0, 1]).range([0, 1, 2, 3]),
                    	  'img_src':['imgs/drugs.png', 'imgs/drugs.png', 'imgs/drugs.png', 'imgs/drugs.png']
                      },
                      
                      {
                    	  'node_event_img':"Received_Treatment",
                    	  'img_scale': d3.scale.threshold().domain([-0.1,1.1]).range([0,1]),
                    	  'img_src': ['imgs/treatment_jaline.png', 'imgs/treatment_jaline.png']
                      },
                      
                      {
                          'node_event_img': "NewClinicalCase",
                          'img_scale': d3.scale.threshold().domain([-0.1,1.1]).range([0,1]),
                          'img_src': ['imgs/case_jaline.png', 'imgs/case_jaline.png']
                      }
                      
                     ]

/*
var node_events_img = [
                      {
                          'node_event_img': "NewClinicalCase",
                          'img_scale': d3.scale.threshold().domain([-0.1,1.1]).range([0,1]),
                          'img_src': ['imgs/case_jaline.png', 'imgs/case_jaline.png']
                      },
                      {
                          'node_event_img': "Received_Treatment",
                          'img_scale': d3.scale.threshold().domain([-0.1,1.1]).range([0,1]),
                          'img_src': ['imgs/treatment_jaline.png', 'imgs/treatment_jaline.png']
                      },
                      {
                          'node_event_img': "Received_ITN",
                          'img_scale': d3.scale.quantize().domain([0,1]).range([0, 1, 2, 3, 4]),
                          'img_src': ['imgs/net_jaline0.png', 'imgs/net_jaline1.png', 'imgs/net_jaline2.png', 'imgs/net_jaline3.png', 'imgs/net_jaline4.png']
                      },
                      {
                          'node_event_img': "Importation",
                          'img_scale': d3.scale.threshold().domain([-0.1, 1.1]).range([0, 1]),
                          'img_src': ['imgs/importation_jaline.png', 'imgs/importation_jaline.png']
                      },
                      {
                          'node_event_img': "Received_RCD_Drugs",
                          'img_scale': d3.scale.quantize().domain([0, 1]).range([0, 1]),
                          'img_src': ['imgs/rcd_drugs_jaline0.png', 'imgs/rcd_drugs_jaline0.png']
                      },
                      {
                          'node_event_img': "Received_Campaign_Drugs",
                          'img_scale': d3.scale.quantize().domain([0, 1]).range([0, 1, 2]),
                          'img_src': ['imgs/camp_drugs_jaline0.png', 'imgs/camp_drugs_jaline1.png', 'imgs/camp_drugs_jaline2.png']
                      }
]
*/


function update_widgets(params)
{
	time = Math.round(params["time"]);
	last_paused_time = time;
	//alert(time);
	if(time <= timesteps.length - 1)
	{
		//alert(timesteps[time["idx"]]);
		style_map(
			    'anim_drugs', 
			    map,
			    {
				   time_idx : timesteps[time],
				   //node_attr_2_color : ["New_Diagnostic_Prevalence", d3.scale.quantize().domain([0, 0.52]).range(colorbrewer.OrRd[9])],
				   node_attr_2_color: ["New_Diagnostic_Prevalence", d3.scale.quantize().domain([0, 1]).range(colorbrewer.Greys[9])],
				   //node_attr_2_color : ["Prevalence", d3.scale.quantize().domain([0, 0.7]).range(colorbrewer.OrRd[9])],
				   //node_attr_2_stroke : ["Received_ITN", d3.scale.threshold().domain([0, 10]).range(['#000000','#281005','#471609','#691a0c','#8c1b0c','#b11a0a','#d71306','#ff0000'])],
				   //node_attrs_2_img : node_attrs_img,
				   node_events_2_img:node_events_img,
				   //node_attr_2_opacity : ["Received_Campaign_Drugs", d3.scale.threshold().domain([0, 10]).range(['0.1','0.2','0.3','0.4','0.5','0.6','0.7','0.8'])],
				   node_attr_2_radius : ["Population", d3.scale.sqrt().domain([0, 15]).range([2, 10])]
			    }
		);	
		
		update_slider("prevalence_dates_slider", time);
		update_date("prevalence_hhs", d3.select("#prevalence_hhs"), time); // function in timeseries.js
	}

}




function load_dashboard(map_data_file)
{	
			
	var playing = false;
	d3.select(".resourcecontainer.buttons")
				.append("button")
				.attr("id","control")
				.attr("type", "button")
				.html("Play")
				.on("click", function(){ 
				//alert(time);
					if(!playing)
					{
						if(last_paused_time < timesteps.length - 1)
							time = last_paused_time;
						else
						{
							time = 0;
							last_paused_time = 0;
						}
						d3.select(this).html("Pause")						
						
						playing = true;
						
						int_id = setInterval(load_snapshot, 125);
					}
					else
					{
						clearInterval(int_id);
						last_paused_time = time;
						//time = timesteps.length+1;
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
		var pattern_svg = d3.select("body").append("svg").attr("id", "attr_pattern_" + node_attr_img);
		var pattern_defs = pattern_svg.append("defs").attr("id", "attr_defs_" + node_attr_img);
		pattern_defs.selectAll("pattern")
		.data(img_scale.range())
		.enter().append("pattern")
			.attr("id", function(d) { return "attr" + node_attr_img + "_" + d; })
			.attr("x", 0)
			.attr("y", 0)
			.attr("height", "100%")
			.attr("width", "100%")
			.attr("viewBox", "0 0 1 1")
			.attr("preserveAspectRatio","xMidYMid slice")
			.insert("image")
			  .attr("x", 0)
			  .attr("y", 0)
			  .attr("height", 1)
			  .attr("width", 1)
			  .attr("preserveAspectRatio","xMidYMid slice")
			  .attr("xlink:href", function(d) { return img_src[d]; });
	}
	
	
	for (var i = 0; i < node_events_img.length; i ++)
	{
		var node_event_img = node_events_img[i]['node_event_img'];
		var img_scale = node_events_img[i]['img_scale'];
		var img_src = node_events_img[i]['img_src'];
  	  	
		// setup an image pattern if node attribute to image map has been specified and patterns have not been created before
		var pattern_svg = d3.select("body").append("svg").attr("id", "pattern_event_" + node_event_img);
		var pattern_defs = pattern_svg.append("defs").attr("id", "defs_event_" + node_event_img);
		pattern_defs.selectAll("pattern")
		.data(img_scale.range())
		.enter().append("pattern")
			.attr("id", function(d) { return "event" + node_event_img + "_" + d; })
			.attr("x", 0)
			.attr("y", 0)
			.attr("height", "100%")
			.attr("width", "100%")
			.attr("viewBox", "0 0 1 1")
			.attr("preserveAspectRatio","xMidYMid slice")
			.insert("image")
			  .attr("x", 0)
			  .attr("y", 0)
			  .attr("height", 1)
			  .attr("width", 1)
			  .attr("preserveAspectRatio","xMidYMid slice")
			  .attr("xlink:href", function(d) { return img_src[d]; });
	}
	
	load_slider(
			"prevalence_hhs.tsv",
			"prevalence_dates_slider",
			{},
			".resourcecontainer.maps", //target container,
			{
		   			"selector":{"function": {"func":update_widgets, "params":{}}},
		   			"attributes_req":["time"]
			}
	);
	
	map = map_data_file;
	load_map(
	 		   'anim_drugs', // map id 
	 		   map, 
	 		   ".resourcecontainer.maps", //target container,
	 		   {
	 			   width:window.innerWidth-170,
	 			   height:window.innerHeight - 110,
	 			   //node_attrs_img:node_attrs_img,
				   base_tile_layer : L.tileLayer('http://{s}.tile.thunderforest.com/landscape/{z}/{x}/{y}.png', {
						attribution: '&copy; <a href="http://www.thunderforest.com/">Thunderforest</a>, &copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
				   	  })
	 		   }
	);		
	
	load_timeseries(
			'prevalence_hhs.tsv',
			'prevalence_hhs', 
			'prevalence', 
			//['#a6cee3','#1f78b4','#b2df8a','#33a02c','#fb9a99','#e31a1c','#fdbf6f','#ff7f00','#cab2d6','#6a3d9a','#ffff99','#b15928'],
			['#89d0c5','#f9b554','#b2df8a'],
			{"special":"avg_itn_hh","time_idx":0, 'width':1100, 'height':500, 'margin':{top: 20, right: 350, bottom: 100, left: 50},'margin2':{ top: 430, right: 150, bottom: 20, left: 40 }},
			".resourcecontainer.timeseries" // target display location: place the timeseries next to the maps (to the right of previously placed maps) if enough horizontal space is available for the width of the timeseries; otherwise place the timeseries below the previously displayed maps
			//".resourcecontainer.timeseries" // target display location: place the timeseries below maps (if any maps are visualized)
	);
	
	
	//animate();
	if(!playing)
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
				   //node_attr_2_color : ["New_Diagnostic_Prevalence", d3.scale.quantize().domain([0, 0.52]).range(colorbrewer.OrRd[9])],
				   node_attr_2_color: ["New_Diagnostic_Prevalence", d3.scale.quantize().domain([0, 1]).range(colorbrewer.Greys[9])],
				   //node_attr_2_color : ["Prevalence", d3.scale.quantize().domain([0, 0.7]).range(colorbrewer.OrRd[9])],
				   //node_attr_2_stroke : ["Received_ITN", d3.scale.threshold().domain([0, 10]).range(['#000000','#281005','#471609','#691a0c','#8c1b0c','#b11a0a','#d71306','#ff0000'])],
				   //node_attrs_2_img : node_attrs_img,
				   node_events_2_img:node_events_img,
				   //node_attr_2_opacity : ["Received_Campaign_Drugs", d3.scale.threshold().domain([0, 10]).range(['0.1','0.2','0.3','0.4','0.5','0.6','0.7','0.8'])],
				   node_attr_2_radius : ["Population", d3.scale.sqrt().domain([0, 15]).range([2, 10])]
			    }
		);	
		update_date("prevalence_hhs", d3.select("#prevalence_hhs"), time); // function in timeseries.js
		update_slider("prevalence_dates_slider", time); //function in slider.js
		time ++;
	}
	else
	{
		clearInterval(int_id); 
		return;
	}
}


/*
Provides requestAnimationFrame in a cross browser way.
http://paulirish.com/2011/requestanimationframe-for-smart-animating/
*/

if (!window.requestAnimationFrame) {

  window.requestAnimationFrame = (function() {

      return window.webkitRequestAnimationFrame ||
          window.mozRequestAnimationFrame || // comment out if FF4 is slow (it caps framerate at ~30fps: https://bugzilla.mozilla.org/show_bug.cgi?id=630127)
      window.oRequestAnimationFrame ||
          window.msRequestAnimationFrame ||
          function( /* function FrameRequestCallback */ callback, /* DOMElement Element */ element) {

              window.setTimeout(callback, 2000 / 60);

      };

  })();

}

function animate() {
  requestAnimationFrame(animate);
  draw();
}

function draw() 
{
	//alert(time);
	//alert(timesteps[time["idx"]]);
	style_map(
		    'anim_drugs', 
		    map,
		    {
			   time_idx : timesteps[time],
			   //node_attr_2_color : ["New_Diagnostic_Prevalence", d3.scale.quantize().domain([0, 0.52]).range(colorbrewer.OrRd[9])],
			   node_attr_2_color: ["New_Diagnostic_Prevalence", d3.scale.quantize().domain([0, 1]).range(colorbrewer.Greys[9])],
			   //node_attr_2_color : ["Prevalence", d3.scale.quantize().domain([0, 0.7]).range(colorbrewer.OrRd[9])],
			   //node_attr_2_stroke : ["Received_ITN", d3.scale.threshold().domain([0, 10]).range(['#000000','#281005','#471609','#691a0c','#8c1b0c','#b11a0a','#d71306','#ff0000'])],
			   //node_attrs_2_img : node_attrs_img,
			   node_events_2_img:node_events_img,
			   //node_attr_2_opacity : ["Received_Campaign_Drugs", d3.scale.threshold().domain([0, 10]).range(['0.1','0.2','0.3','0.4','0.5','0.6','0.7','0.8'])],
			   node_attr_2_radius : ["Population", d3.scale.sqrt().domain([0, 15]).range([2, 10])]
		    }
	);	
	update_slider("prevalence_dates_slider", time);
	time ++;
  
}