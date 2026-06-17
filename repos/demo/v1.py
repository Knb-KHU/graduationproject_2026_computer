from transformers import AutoModelForCausalLM, AutoTokenizer
from bs4 import BeautifulSoup
import re,json,requests,random

class user:
    tlist={}
    def __init__(self,id, preft):
        self.id=id
        self.preft=preft
    def printtlist(self):
        print("")

def get_location_by_ip():
    try:
        response = requests.get("https://ipinfo.io/json", timeout=5)
        response.raise_for_status()
        data = response.json()

        loc = data.get("loc", "")
        if loc:
            latitude, longitude = loc.split(",")
            return float(latitude), float(longitude)
        else:
            return None
    except requests.RequestException as e:
        print(f"위치 정보를 가져오는 중 오류 발생: {e}")
        return None

def locextractor(userinput):
   
    # 모델
    model_name = "Qwen/Qwen2.5-3B"
    local_path = "C:/Users/safas/Downloads/Qwen2.5-3B"
    tokenizer = AutoTokenizer.from_pretrained(local_path)
    model = AutoModelForCausalLM.from_pretrained(local_path,
                                                 low_cpu_mem_usage=True,
                                                 device_map="auto")

    # Tool 정의 (JSON Schema)
    functions = [
        {
            "name": "extract_location",
            "description": "문장에서 장소명만 추출합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "locations": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "추출된 장소명 리스트"
                    }
                },
                "required": ["locations"]
            }
        }
    ]

    # 프롬프트
    prompt = f"""
    다음 예시를 참고하세요.

    문장: 나는 서울시에 있는 강남역 스타벅스에 갔다
    출력: {{"locations": ["서울시","강남역","스타벅스"]}}

    문장: 홍대입구에서 올리브영 들렀어
    출력: {{"locations": ["홍대입구","올리브영"]}}

    문장: {userinput}
    출력:
    """

    # 추론
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(**inputs, max_new_tokens=256,do_sample=False,temperature=0.0,)
    result = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # 디코딩
    print(result)
    match = re.findall(r"\{.*?\}", result, re.DOTALL)
    all_loc=[json.loads(m)["locations"]for m in match]
    if match:
        try:
            data = all_loc[2]
            loc=""
            for i in data:
                loc+=i
            print("장소:", data)
            return loc
        except json.JSONDecodeError:
            print("JSON 디코딩 실패:", match)
    else:
        print("JSON 패턴을 찾지 못했습니다:", result)
    
def searchloc(query):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": query, "format": "json"}
    headers = {"User-Agent": "search.py/1.0 (srain0723@khu.ac.kr)"}

    response = requests.get(url, params=params, headers=headers)
    if(response.status_code==200):
        data=response.json()
        for place in data:
            print(place["display_name"], "-", place["lat"], place["lon"])
            return place["lat"],place["lon"]
    else:
        print("error:status_error")
        return 0,0

def vahallaroutes(slac,sloc,dlat,dloc):

    url="http://localhost:8002/route"
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

def search_web(query):
    query="+"+query
    url = f"https://www.bing.com/search?q={query}"
    
    response = requests.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        results="."
        
        for item in soup.select("li.b_algo h2 a"):
            title = item.get_text()
            link = item["href"]
            results=results+title
        
        return results
    else:
        print("검색 실패:", response.status_code)
        return []
    
def findroute(U):
    route={}
    start=input("출발지를 입력하세요")
    slat,slon=searchloc(locextractor(start))
    dest=input("여행지를 입력하세요")
    dlat,dlon=searchloc(locextractor(dest))
    day=int(input("여행일자를 입력해주세요:"))
    tlen,ttime=vahallaroutes(slat,slon,dlat,dlon)
    print("이동거리:",tlen,"이동시간:",ttime)
    n=0
    totime=ttime
    route[f"{slat}"]=slon
    route[f"travel{n}"]=ttime
    route[f"{dlat}{n}"]=dlon
    destr=dest+"근처식당"
    desth=dest+"근처호텔"
    hlat,hlon=searchloc(locextractor(search_web(desth)))
    
    for d in range (day):
        for i in range(3):
            n+=1
            rlat,rlon=searchloc(locextractor(search_web(destr)))
            tlen,ttime=vahallaroutes(list(route.keys())[2*n],route[list(route.keys())[2*n]],rlat,rlon)
            print("이동거리:",tlen,"이동시간:",ttime)
            totime+=ttime
            route[f"travel{n}"]=ttime
            route[f"{rlat}{n}"]=rlon
        
        n+=1
        tlen,ttime=vahallaroutes(list(route.keys())[2*n],route[list(route.keys())[2*n]],rlat,rlon)
        print("이동거리:",tlen,"이동시간:",ttime)
        totime+=ttime
        route[f"travel{n}"]=ttime
        route[f"{hlat}{n}"]=hlon
    print(f"총여행시간:{totime}")
    U.tlist=route
    return U.tlist

u1=user("u1",30)
findroute(u1)
print("endofline")

