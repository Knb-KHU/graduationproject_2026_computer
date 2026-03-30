
def vahallaroutes(slac,sloc,dlat,dloc):
    url="http://localhost:80002/route"
    payload={
        "locations":[
            {"lat":slat,"lon":slon},
            {"lat":dlat,"lon":dloc}
            ],
        "costing": "auto",
        "units"="kilometers"
        }
    response=requests.post(url,json=payload)
    return response.jsonloads["summary"]["length"]
