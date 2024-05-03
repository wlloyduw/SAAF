#cloud_function(platforms=[Platform.AWS], memory=512, config=config)
def yourFunction(request, context):
    import json
    import logging
    from Inspector import Inspector
    import time
    
    # Import the module and collect data 
    inspector = Inspector()
    inspector.inspectAll()

    # Add custom message and finish the function
    if ('name' in request):
        inspector.addAttribute("message", "Mello " + str(request['name']) + "!")
    else:
        inspector.addAttribute("message", "Dello World!")
    
    inspector.inspectAllDeltas()
    return inspector.finish()
