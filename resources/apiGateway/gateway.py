


def getOrigins():
    return "dakobedbard.com"

def getResponseTemplate(deployment_type):
    domainChecks = getOrigins()
    return f"""set($origin = $input.params().header.get("Origin"))
    #if(#origin == "")
        #set)
    $input.json('S')
    """