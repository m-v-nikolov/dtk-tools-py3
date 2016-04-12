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
		alert(emit_candidates.length);
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
     { //IE
	       var ev_object = document.createEventObject();
	       trigger_object.fireEvent( 'on' + event, ev_object );
     } 
	 
}

//helper function to trigger emit signal to elements of certain class, id, etc.
//element: element triggering the event
//event: event to trigger
//selector: {selector_type:value}; e.g. {"class":class_name}
function trigger_emit(element, event, selector)
{
	if(d3.select(element).attr("emitted") == "false")
	{
		// if the emit function is defined somewhere, execute it
		if (typeof(emit) == "function")
		{
			emit({
				"event":event,
				"selector":selector
			});
	
			// set the emitted to false for the next mouseover event
			d3.select(element).attr("emitted", false);
		}
	}
}