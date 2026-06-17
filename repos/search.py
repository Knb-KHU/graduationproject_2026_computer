"""import requests

query = "롯데월드"
url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json"

response = requests.get(url)
print(response.status_code)
print(response.text)

data = response.json()

print(data)
for place in data:
    print(place["display_name"], "-", place["lat"], place["lon"])"""



import requests
def search(query):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": query, "format": "json"}
    headers = {"User-Agent": "search.py/1.0 (srain0723@khu.ac.kr)"}

    response = requests.get(url, params=params, headers=headers)
    if(response.status_code==200):
        data=response.json()
        for place in data:
            print(place["display_name"], "-", place["lat"], place["lon"])
    else:
        print("error:status_error")

search("강남구 다이소")
