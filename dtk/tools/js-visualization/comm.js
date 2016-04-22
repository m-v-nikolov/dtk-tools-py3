var events = {
				"mouseover":"mouseover",
				"click":"click"
			 }

function emit(comm_msg)
{	
	
	if(comm_msg.hasOwnProperty("event"))
		var event = comm_msg["event"];
	else
		return;

	if(comm_msg.hasOwnProperty("selector"))
	{
		var selector_type = Object.keys(comm_msg["selector"])[0];
		var selector = comm_msg["selector"][selector_type];
	}
	else
		return;
	
	/* just testing; will make these more concise w/ jquery/d3 and more generic*/
	if(selector_type == "class")
	{
		emit_candidates = document.getElementsByClassName(selector);
		
		for(var i = 0; i < emit_candidates.length; i++)
		{
			emit_candidate = emit_candidates[i];
			if(emit_candidate.getAttribute("emitted") == "false")
			{
				emit_candidate.setAttribute("emitted", "true");
				trigger_event(emit_candidate, event);
			}
		}
	}
	else	
	if(selector_type == "id")
	{
		emit_candidate = document.getElementById(selector);
		if(emit_candidate.getAttribute("emitted") == "false")
		{
			emit_candidate.setAttribute("emitted", "true");
			trigger_event(emit_candidate, event);
		}
	}
	else // use select by attribute value
	{
		alert("in emit");
		alert(selector_type);
		alert(selector);
		emit_candidates = document.querySelectorAll('['+selector_type+'='+ selector+ ']');
		
		for(var i = 0; i < emit_candidates.length; i++)
		{
			emit_candidate = emit_candidates[i];
			if(emit_candidate.getAttribute("emitted") == "false")
			{
				emit_candidate.setAttribute("emitted", "true");
				trigger_event(emit_candidate, event);
			}
		}
	}
}

function trigger_event(emit_candidate, event)
{
     var trigger_object = emit_candidate;
     if( document.createEvent ) 
     {
	       var ev_object = document.createEvent('MouseEvents');
	       ev_object.initEvent( event, true, false );
	       trigger_object.dispatchEvent( ev_object );
     }
     else 
     if( document.createEventObject ) 
     { 	   //IE
	       var ev_object = document.createEventObject();
	       trigger_object.fireEvent( 'on' + event, ev_object );
     } 
	 
}

//helper function to trigger emit signal to elements of certain class, id, etc.
/* comm_msg: message object (json) w/ format

{
	"event":javascript event (e.g. mouseover, click, etc), // optional 
	"selector": {
					type of entity to be configured : configuration message (object)
				},
	
	"attributes_req":[array of attribute names that may be binded to the comm_msg], // optional
}				

"selector" is a required attribute of comm_msg.


//known types of entities for selectors
	"id",
	"class",
	"function"
	"param"
	
	"id", "class" and "param" types map to javascript dispatchevent determined by the "event" key;
	e.g. "mouseover", "click", etc.. The configuration message is assumed to be 
	a valid element id, class or param value. The corresponding "event" of the matching elements (based on id/class/param value) is triggered.
	param is a custom attribute of an arbitrary html element.  
	By default, if "event" key is missing, the mouseover event is triggered. 
	
	"function" entity types map to a generic configuration object with format
	
	{
	  "func":func, //function
	  "params":params //object
	 }
	 
	The function func is executed with parameter object params; e.g. equivalent to func(params);
*/
function trigger_emit(element, comm_msg)
{
	if(!comm_msg.hasOwnProperty("selector"))
		return; // if the selector attribute is not set, do nothing.

	var selector = Object.keys(comm_msg["selector"])[0];

	if(d3.select(element).attr("emitted") == "false") // if the element has not emitted this message yet, emit the message
	{
		if (selector != "function") // if entity type is not "function" call emit to dispatch a javascript event to the matching elements   
		{
			var event = "mouseover";
			if(comm_msg.hasOwnProperty("event"))
				event = comm_msg["event"];

			// if the emit function is defined somewhere (in this case it is defined in this file), execute it
			if (typeof(emit) == "function")
			{
				emit({
					"event":event,
					"selector":selector
				});
			}
		}
		else
		{
			var func = comm_msg["selector"]["function"]["func"];
			if (typeof func === "function")
			{
				params = comm_msg["selector"]["function"]["params"];
				func(params);
			}
		}
		
		// set the element emitted attribute to false for the next mouseover event
		d3.select(element).attr("emitted", false);
	}
}

/*
 * Helper function parsing comm_msg and binding data attributes to comm_msg, if requested
 * 
 * comm_msg: communication message
 * data: json;
 */
function parse_comm_msg(comm_msg, data)
{
	if (comm_msg["selector"].hasOwnProperty("function"))
	{
		func = comm_msg["selector"]["function"]["func"];
		
		if (comm_msg.hasOwnProperty("attributes_req"))
		{
			attributes = comm_msg["attributes_req"]; 
			for(var i = 0; i < attributes.length; i++)
			{
				var attribute = attributes[i];
				if (data.hasOwnProperty(attribute))
					comm_msg["selector"]["function"]["params"][attribute] = data[attribute];
			}	
		}
	}
	
	return comm_msg;
}