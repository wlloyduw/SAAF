# WARNING (Autogenerated Code): Editing this file manually is NOT RECOMMENDED! CHANGES MAY BE LOST!
def yourFunction(request, context): 
    from SAAF import Inspector
    inspector = Inspector() 
    inspector.inspectAll()
    
    import subprocess
    result = subprocess.run(['bash', 'your_script.sh'], capture_output=True, text=True)
    
    output = result.stdout
    error = result.stderr
    
    inspector.addAttribute("standard_output", output)
    inspector.addAttribute("error_output", error)

    inspector.inspectAllDeltas()  
    return inspector.finish()
