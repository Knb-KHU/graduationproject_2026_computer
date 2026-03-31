
import re,json,requests


def search(query):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": query, "format": "json"}
    headers = {"User-Agent": "search.py/1.0 (srain0723@khu.ac.kr)"}

    response = requests.get(url, params=params, headers=headers)
    if(response.status_code==200):
        data=response.json()
        for place in data:
            return place["lat"],place["lon"]
            print(place["display_name"], "-", place["lat"], place["lon"])
    else:
        print("error:status_error")
        
def vahallaroutes(slac,sloc,dlat,dloc):
    dummy1,dummy2=10,30
    return dummy1,dummy2
    url="http://localhost:80002/route"
    payload={
        "locations":[
            {"lat":slat,"lon":slon},
            {"lat":dlat,"lon":dloc}
            ],
        "costing": "auto",
        "units":"kilometers"
        }
    response=requests.post(url,json=payload)
    return response.jsonloads["trip"]["legs"][0]["summary"]["length"],response.jsonloads["trip"]["legs"][0]["summary"]["time"]


start=input("출발지를 입력하세요")
slat,slon=search(start)
dest=input("여행지를 입력하세요")
dlat,dlon=search(dest)
tlen,ttime=vahallaroutes(slat,slon,dlat,dlon)
print("이동거리:",tlen,"이동시간:",ttime)
