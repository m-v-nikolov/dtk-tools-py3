var timesteps = ["14417", "14418", "14419", "14420", "14421", "14422", "14423", "14424", "14425", "14426", "14427", "14428", "14429", "14430", "14431", "14432", "14433", "14434", "14435", "14436", "14437", "14438", "14439", "14440", "14441", "14442", "14443", "14444", "14445", "14446", "14447", "14448", "14449", "14450", "14451", "14452", "14453", "14454", "14455", "14456", "14457", "14458", "14459", "14460", "14461", "14462", "14463", "14464", "14465", "14466", "14467", "14468", "14469", "14470", "14471", "14472", "14473", "14474", "14475", "14476", "14477", "14478", "14479", "14480", "14481", "14482", "14483", "14484", "14485", "14486", "14487", "14488", "14489", "14490", "14491", "14492", "14493", "14494", "14495", "14496", "14497", "14498", "14499", "14500", "14501", "14502", "14503", "14504", "14505", "14506", "14507", "14508", "14509", "14510", "14511", "14512", "14513", "14514", "14515", "14516", "14517", "14518", "14519", "14520", "14521", "14522", "14523", "14524", "14525", "14526", "14527", "14528", "14529", "14530", "14531", "14532", "14533", "14534", "14535", "14536", "14537", "14538", "14539", "14540", "14541", "14542", "14543", "14544", "14545", "14546", "14547", "14548", "14549", "14550", "14551", "14552", "14553", "14554", "14555", "14556", "14557", "14558", "14559", "14560", "14561", "14562", "14563", "14564", "14565", "14566", "14567", "14568", "14569", "14570", "14571", "14572", "14573", "14574", "14575", "14576", "14577", "14578", "14579", "14580", "14581", "14582", "14583", "14584", "14585", "14586", "14587", "14588", "14589", "14590", "14591", "14592", "14593", "14594", "14595", "14596", "14597", "14598", "14599", "14600", "14601", "14602", "14603", "14604", "14605", "14606", "14607", "14608", "14609", "14610", "14611", "14612", "14613", "14614", "14615", "14616", "14617", "14618", "14619", "14620", "14621", "14622", "14623", "14624", "14625", "14626", "14627", "14628", "14629", "14630", "14631", "14632", "14633", "14634", "14635", "14636", "14637", "14638", "14639", "14640", "14641", "14642", "14643", "14644", "14645", "14646", "14647", "14648", "14649", "14650", "14651", "14652", "14653", "14654", "14655", "14656", "14657", "14658", "14659", "14660", "14661", "14662", "14663", "14664", "14665", "14666", "14667", "14668", "14669", "14670", "14671", "14672", "14673", "14674", "14675", "14676", "14677", "14678", "14679", "14680", "14681", "14682", "14683", "14684", "14685", "14686", "14687", "14688", "14689", "14690", "14691", "14692", "14693", "14694", "14695", "14696", "14697", "14698", "14699", "14700", "14701", "14702", "14703", "14704", "14705", "14706", "14707", "14708", "14709", "14710", "14711", "14712", "14713", "14714", "14715", "14716", "14717", "14718", "14719", "14720", "14721", "14722", "14723", "14724", "14725", "14726", "14727", "14728", "14729", "14730", "14731", "14732", "14733", "14734", "14735", "14736", "14737", "14738", "14739", "14740", "14741", "14742", "14743", "14744", "14745", "14746", "14747", "14748", "14749", "14750", "14751", "14752", "14753", "14754", "14755", "14756", "14757", "14758", "14759", "14760", "14761", "14762", "14763", "14764", "14765", "14766", "14767", "14768", "14769", "14770", "14771", "14772", "14773", "14774", "14775", "14776", "14777", "14778", "14779", "14780", "14781"];
var int_id;
var time;
var map;

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

var node_attrs_img = []


function update_widgets(params) {
    time = Math.round(params["time"]);
    last_paused_time = time;
    //alert(time);
    if (time <= timesteps.length - 1) {
        //alert(timesteps[time["idx"]]);
        style_map(
			    'anim_drugs',
			    map,
			    {
			        time_idx: timesteps[time],
			        node_attr_2_color: ["Prevalence", d3.scale.quantize().domain([0, 1]).range(colorbrewer.Greys[9])],
			        node_events_2_img: node_events_img,
			        node_attr_2_radius: ["Population", d3.scale.sqrt().domain([0, 15]).range([2, 10])]
			    }
		);
        update_date("hhs_160524_prev", d3.select("#hhs_160524_prev"), time); // function in timeseries.js
        update_date("hhs_160524_counts", d3.select("#hhs_160524_counts"), time); // function in timeseries.js
        update_slider("prevalence_dates_slider", time);
    }

}

function load_dashboard(map_data_file)
{
    
    var playing = false;
    d3.select(".resourcecontainer.buttons")
				.append("button")
				.attr("id", "control")
				.attr("type", "button")
				.html("Play")
				.on("click", function () {
				    //alert(time);
				    if (!playing) {
				        if (last_paused_time < timesteps.length - 1)
				            time = last_paused_time;
				        else {
				            time = 0;
				            last_paused_time = 0;
				        }
				        d3.select(this).html("Pause")

				        playing = true;

				        int_id = setInterval(load_snapshot, 125);
				    }
				    else {
				        clearInterval(int_id);
				        last_paused_time = time;
				        //time = timesteps.length+1;
				        d3.select(this).html("Play")
				        playing = false;
				        return;
				    }

				});
    

    
    for (var i = 0; i < node_events_img.length; i++) {
        var node_event_img = node_events_img[i]['node_event_img'];
        var img_scale = node_events_img[i]['img_scale'];
        var img_src = node_events_img[i]['img_src'];

        // setup an image pattern if node attribute to image map has been specified and patterns have not been created before
        var pattern_svg = d3.select("body").append("svg").attr("id", "pattern_event_" + node_event_img);
        var pattern_defs = pattern_svg.append("defs").attr("id", "defs_event_" + node_event_img);
        pattern_defs.selectAll("pattern")
		.data(img_scale.range())
		.enter().append("pattern")
			.attr("id", function (d) { return "event" + node_event_img + "_" + d; })
			.attr("x", 0)
			.attr("y", 0)
			.attr("height", "100%")
			.attr("width", "100%")
			.attr("viewBox", "0 0 1 1")
			.attr("preserveAspectRatio", "xMidYMid slice")
			.insert("image")
			  .attr("x", 0)
			  .attr("y", 0)
			  .attr("height", 1)
			  .attr("width", 1)
			  .attr("preserveAspectRatio", "xMidYMid slice")
			  .attr("xlink:href", function (d) { return img_src[d]; });
    }
    
    
    for (var i = 0; i < node_attrs_img.length; i++) {
        var node_attr_img = node_attrs_img[i]['node_attr_img'];
        var img_scale = node_attrs_img[i]['img_scale'];
        var img_src = node_attrs_img[i]['img_src'];

        // setup an image pattern if node attribute to image map has been specified and patterns have not been created before
        var pattern_svg = d3.select("body").append("svg").attr("id", "pattern_" + node_attr_img);
        var pattern_defs = pattern_svg.append("defs").attr("id", "defs_" + node_attr_img);
        pattern_defs.selectAll("pattern")
		.data(img_scale.range())
		.enter().append("pattern")
			.attr("id", function (d) { return node_attr_img + "_" + d; })
			.attr("x", 0)
			.attr("y", 0)
			.attr("height", 17)
			.attr("width", 17)
			.insert("image")
			  .attr("x", 0)
			  .attr("y", 0)
			  .attr("height", 20)
			  .attr("width", 20)
			  .attr("xlink:href", function (d) { return img_src[d]; });
    }
    
    
    load_slider(
			"prevalence_hhs_160524.tsv",
			"prevalence_dates_slider",
			{},
			".resourcecontainer.maps", //target container,
			{
			    "selector": { "function": { "func": update_widgets, "params": {} } },
			    "attributes_req": ["time"]
			}
	);
    
    
	map = map_data_file;
	load_map(
	 		   'anim_drugs', // map id 
	 		   map, 
	 		   ".resourcecontainer.maps", //target container,
	 		   {
	 		       width: 800,
	 		       height: 600,
	 			   node_opacity:0.8, // controls node opacity; if specified, it overrides the node_attr_2_opacity parameter values (the latter allows the binding of channel's values to node opacity)
	 			   node_attrs_img: [],
                   
	 			   additional_layers: [L.tileLayer.wms('http://idmdvsmt01.internal.idm.ctr:8080/cgi-bin/mapserv.exe?map=c:/ms4w/apps/idm/malaria/zambia.map&', {
	 				    layers: 'CHW_locations_Rural,CHW_locations_RHC',
						format: 'image/png', 
						transparent: false, 
						crs: L.CRS.EPSG4326,
					})],
                    
					base_tile_layer : L.tileLayer('http://{s}.tile.thunderforest.com/landscape/{z}/{x}/{y}.png', {
						attribution: '&copy; <a href="http://www.thunderforest.com/">Thunderforest</a>, &copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
				   	  })
	 		   }
	);
	
	
	load_timeseries(
			'prevalence_hhs_160524.tsv',
			'hhs_160524_prev', 
			'prevalence', 
			['#89D0C5', '#F9B554', '#b2df8a', '#fb9a99', '#e31a1c', '#fdbf6f', '#ff7f00', '#cab2d6', '#6a3d9a', '#ffff99', '#b15928'],
			{'width':900, 'height':500, 'margin':{top: 20, right: 250, bottom: 100, left: 50},'margin2':{ top: 430, right: 150, bottom: 20, left: 40 }},
			".resourcecontainer.maps" // target display location: place the timeseries next to the maps (to the right of previously placed maps) if enough horizontal space is available for the width of the timeseries; otherwise place the timeseries below the previously displayed maps
			//".resourcecontainer.timeseries" // target display location: place the timeseries below maps (if any maps are visualized)
	);
	
	
	load_timeseries(
			'counts_hhs_160524.tsv',
			'hhs_160524_counts', 
			'counts', 
			['#BA3E39', '#F9B554', '#c51b8a', '#BA7FB7', '#87CAC1', '#fb9a99', '#e31a1c', '#fdbf6f', '#ff7f00', '#cab2d6', '#6a3d9a', '#ffff99', '#b15928'],
			{'special' : 'Received_ITN', 'width':900, 'height':500, 'margin':{top: 20, right: 250, bottom: 100, left: 50},'margin2':{ top: 430, right: 150, bottom: 20, left: 40 } },
			".resourcecontainer.maps" // target display location: place the timeseries next to the maps (to the right of previously placed maps) if enough horizontal space is available for the width of the timeseries; otherwise place the timeseries below the previously displayed maps
			//".resourcecontainer.timeseries" // target display location: place the timeseries below maps (if any maps are visualized)
	);
	
	
	if(!playing)
		load_snapshot();
	//time = 0;
	//int_id = setInterval(load_snapshot, 125);
}



function load_snapshot()
{	
	
	if(time < timesteps.length - 1)
	{
		style_map(
			    'anim_drugs', 
			    map,
			    {
				   time_idx : timesteps[time],
				   node_attr_2_color: ["Prevalence", d3.scale.quantize().domain([0, 1]).range(colorbrewer.Greys[9])],
				   node_attr_2_radius : ["Population", d3.scale.sqrt().domain([0, 15]).range([2, 10])],
				   node_events_2_img: node_events_img,
			    }
		);

		update_date("hhs_160524_prev", d3.select("#hhs_160524_prev"), time); // function in timeseries.js
        update_date("hhs_160524_counts", d3.select("#hhs_160524_counts"), time); // function in timeseries.js
		update_slider("prevalence_dates_slider", time);
		time++;
		
	}
	else
	{
	    clearInterval(int_id);
	    return;
    }
}

