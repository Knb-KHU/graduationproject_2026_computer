import json
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import requests,re,ast
import datetime
from transformers import BitsAndBytesConfig

model=None
tokenizer=None

def call_model():
    local_path= "/local_datasets/Qwen2.5-3B-Instruct"
    quant_config = BitsAndBytesConfig(load_in_8bit=True)
    m = AutoModelForCausalLM.from_pretrained(local_path, quantization_config=quant_config, device_map="auto")
    t = AutoTokenizer.from_pretrained(local_path, local_files_only=True)
    return m,t

    

class User:
    def __init__(self,pref,weight,tlist=[]):
        self.pref=pref
        self.weight=weight
        self.tlist=tlist

def revaluater(question, answers, criteria):
    prompt = f"""
    You are an impartial judge evaluating multiple answers to the same question.
    Question: {question}

    Candidate Answers:
    {chr(10).join([f"Answer {i+1}: {ans}" for i, ans in enumerate(answers)])}

    Evaluation Criteria: {", ".join(criteria)}

    The answers are a review about a place.
    Please rate each place on a scale of 1 to 5 for each criterion,
    then provide an overall score (average).
    Finally, rank the answers from best to worst.

    Respond strictly in JSON with the following structure:
    {{
      "evaluations": [
        {{
          "answer_id": int,
          "scores": {{
            "{criteria[0]}": int,
            "{criteria[1]}": int,
            "{criteria[2]}": int,
            ...
            "criteria[i]": int
          }},
          "overall": float,
          "comments": "short explanation"
        }}
      ],
      "ranking": [int, int, ...]
    }}
    """
    
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(**inputs, max_new_tokens=2048,do_sample=False,temperature=0.0,)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    res=response
    match = re.findall(r"\"answer_id\": 1,.*?ranking", res, re.DOTALL)
    
    try:
        m = match[0].replace("json","").replace("`","")
    except IndexError:
        return {
        "individual_results": None,
        "ensemble_scores": None,
        "specific_scores":None
    }



    m=match[0].replace("json","").replace("`","")
    j=re.findall(r"overall\": *?,",m,re.DOTALL)
    for i in range (len(j)):
        j[i]=float(j[i].replace("overall\": ","").replace(",",""))
    sp=[]
    for i in range (len(criteria)):
        k=re.findall(rf"\"{criteria[i]}\":\s*\d+", m, re.DOTALL)
        for t in range (len(k)):
            k[t]=float(k[t].replace(f"\"{criteria[i]}\":","").replace(",",""))
    

    return {
        "individual_results": res,
        "ensemble_scores": j,
        "specific_scores":sp
    }



placesapi = "AIzaSyCt3hPrnbAejMixTLJlP2xDeZKOq-n_EGw"
restapi = "3b06b2ec80486b28690f23d7c000ee3e"

def searchloc(query):
    url="https://dapi.kakao.com/v2/local/search/keyword.json"
    headers={"Authorization": f"KakaoAK {restapi}"}
    params={"query":query,"size": 1}
  
    response = requests.get(url, params=params, headers=headers)
    if(response.status_code==200):
        p=response.json().get('documents', [])
        name=p[0]['place_name']
        lat,lon=p[0]['y'],p[0]['x']
        return lat,lon,name
    else:
        print("error:status_error")
        return 0,0,0

def routes(slat,slon,dlat,dlon):
    url = "https://apis-navi.kakaomobility.com/v1/directions"
    headers = {
        "Authorization": f"KakaoAK {restapi}",
        "Content-Type": "application/json"
    }
    
    params = {
        "origin": f"{slon},{slat}",
        "destination": f"{dlon},{dlat}",
        "priority": "RECOMMEND",
        "car_type": 1
    }
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json()
        try:
            dis= data['routes'][0]['summary']['distance']
            tim = data['routes'][0]['summary']['duration']
        except:
            return 0,3000
        return dis,tim
    else:
        print(f"Error: {response.status_code}")
        return None
def get_target_category(category):
    if category=="AT4":
        return ["가성비","전망","특이성","지역성"]
    elif category=="AT5":
        return ["가성비","전망","특이성","문화적가치"]
    elif category=="FD6":
        return ["청결도","가성비","맛","서비스"] # 음식점
    elif category=="AD5":
        return ["청결도","가성비","부가시설","서비스",""] # 숙박
    else:
        return ["청결도","가성비","맛","서비스"]  # 기본값: 카페 (사용자 선호 카테고리로 변경 가능)

def get_kakao_places(lat, lng, category_code):
    """카카오맵 API를 사용하여 반경 1km 이내 10곳 검색"""
    url = "https://dapi.kakao.com/v2/local/search/category.json"
    headers = {"Authorization": f"KakaoAK {restapi}"}
    params = {
        "category_group_code": category_code,
        "x": lng,
        "y": lat,
        "radius": 1000,
        "size": 10,
        "sort": "distance"
    }
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json().get('documents', [])
    return []

def get_google_rating(place_name, lat, lng):
    """Google Places API를 통해 장소 ID 확보 및 평점/리뷰수 수집"""
    # 1. Find Place (장소명과 좌표로 Google Place ID 찾기)
    search_url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
    search_params = {
        "input": place_name,
        "inputtype": "textquery",
        "locationbias": f"circle:200@{lat},{lng}",
        "fields": "place_id",
        "key": placesapi
    }
    
    res = requests.get(search_url, params=search_params).json()
    candidates = res.get('candidates', [])
    
    if not candidates:
        return None, 0,[]
        
    place_id = candidates[0]['place_id']
    
    # 2. Place Details (평점 및 리뷰 개수 가져오기)
    url = f"https://places.googleapis.com/v1/places/{place_id}"
    headers = {
        "X-Goog-Api-Key": placesapi,
        "X-Goog-FieldMask": "rating,userRatingCount,reviews"
    }
    result = requests.get(url, headers=headers).json()
    
    
    return result.get('rating', 0), result.get('userRatingCount', 0),result.get('reviews', [])

def reviewcountapply(google_rating, review_count, user_preference_score):
    """평점 정량화 및 사용자 만족도 계산 (베이지안 평균법 응용)"""
    m = 10    # 신뢰도를 위한 최소 리뷰 개수 가중치
    C = 3.0   # 평점 데이터가 없을 때의 기본 점수
    
    if review_count == 0:
        adjusted_rating = C
    else:
        # 리뷰 수가 많을수록 실제 평점에 가중치를 둠
        adjusted_rating = (review_count / (review_count + m) * google_rating) + (m / (review_count + m) * C)
    
    # 사용자 선호도(1.0 ~ 1.5)를 곱하여 최종 점수 산출
    final_score = adjusted_rating * user_preference_score
    return round(final_score, 2)

def run_evaluation_system(start_lat, start_lng, ttime, user_pref=[],user_pref_weight=1.2,category=""):
    """시스템 메인 실행 함수"""
    criteria = get_target_category(category)
    for item in user_pref:
        criteria.append(item)
    
    print(f"--- 현재 시간: {ttime}시 | 선택된 카테고리: {category} ---")
    
    
    kakao_list = get_kakao_places(start_lat, start_lng, category)
    print("불러온 장소 개수:",len(kakao_list))
    results = []
    revtexts=[]
    for p in kakao_list:
        name = p['place_name']
        lat, lng = p['y'], p['x']

        g_rating, g_reviews, g_reviewsli = get_google_rating(name, lat, lng)

        rate,revtext=0,""
        for review in g_reviewsli:
            rate+=review['rating']
            if "text" in review and "text" in review["text"]:
                revtext += review["text"]["text"] + "\n"
            elif "originalText" in review and "text" in review["originalText"]:
                revtext += review["originalText"]["text"] + "\n"
            else:
                revtext += "(본문 없음)\n"
              
        revtexts.append(revtext)
        results.append({
            "장소명": name,
            "lat":lat,
            "lon":lng,
            "거리": f"{p['distance']}m",
            "Google평점": g_rating,
            "리뷰수": g_reviews,
            "리뷰내용":revtext
        })
    
    ensemble_result = revaluater("How was the place you experienced", revtexts, criteria)
    for i in range (len(ensemble_result["ensemble_scores"])):
        results[i]["상대평점"]=ensemble_result["ensemble_scores"][i]
        satisfaction_score = reviewcountapply(ensemble_result["ensemble_scores"][i],results[i]["리뷰수"], user_pref_weight)
        results[i]["최종만족도"]=satisfaction_score
    # 최종 점수순 정렬
    results.sort(key=lambda x: x.get('최종만족도', 0), reverse=True)

    return results

from transformers import AutoTokenizer,AutoModelForCausalLM
import torch

import re,json

def locextractor(userinput):
    # 모델
    local_path= "/local_datasets/Qwen2.5-3B-Instruct"
    
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

    문장: 나는 서울시에 있는 강남역의 스타벅스와 노원구에 있는 공릉역의 다이소에 가고 싶어.
    출력: {{\"locations\": [\"서울시 강남역 스타벅스\",\"노원구 공릉역 다이소\"]}}

    문장: 홍대입구에서 올리브영 들렀어
    출력: {{\"locations\": [\"홍대입구 올리브영\"]}}

    문장: {userinput}
    출력:
    """

    inputs = tokenizer(prompt, add_generation_prompt=False, return_tensors="pt").to(model.device)
    outputs = model.generate(**inputs, max_new_tokens=256,do_sample=False,temperature=0.0,)
    result = tokenizer.decode(outputs[0], skip_special_tokens=True)

    match = re.findall(r"\{.*?\}", result, re.DOTALL)
    match[2]=ast.literal_eval(match[2])
    #(match[2].replace("{\"locations\": ","").replace("}",""))

    return (match[2]["locations"][0])

def findroute(U,m,t):
        global model, tokenizer
        model=m
        tokenizer=t
        route=[]
        totime=8*3600
        sname=input("출발지를 입력하세요")
        #sname=locextractor(start)
        slat,slon,sname=searchloc(sname)
        ttime=0
        route.append([{"장소명": sname,
            "lat":slat,
            "lon":slon,
            "거리": "0m"}])
        dname=input("여행지를 입력하세요")
        #dname=locextractor(dest)
        dlat,dlon,dname=searchloc(dname)
        tlen,ttime=routes(slat,slon,dlat,dlon)
        route.append([{"장소명": dname,
            "lat":dlat,
            "lon":dlon,
            "거리":tlen,
            "시간":ttime}])
        day=int(input("여행일자를 입력해주세요:"))
        
        totime+=ttime
        category="AD5"
        h=run_evaluation_system(dlat,dlon,totime//3600,U.pref,U.weight,category)
        route.append(h)
        hlat,hlon=h[0]["lat"],h[0]["lon"]
        tlen,ttime=routes(route[1][0]["lat"],route[1][0]["lon"],hlat,hlon)
        totime+=ttime+5400
        rlat,rlon=hlat,hlon
        for d in range (day):
            for i in range(6):
                if (8 <= totime//3600 <= 9 or 11 <= totime//3600 <= 13 or 17<= totime//3600 <= 18)and category!="FD6":
                    category="FD6"
                elif category!="CE7":
                    category="CE7"
                elif category!="AT4":
                    category="AT4"
                else:category="AT5"
                r=run_evaluation_system(rlat,rlon,totime//3600,U.pref,U.weight,category)
                rlat,rlon=r[0]["lat"],r[0]["lon"]
                tlen,ttime=routes(route[-1][0]["lat"], route[-1][0]["lon"],rlat,rlon)
                route.append(r)
                totime+=ttime+5400
            tlen,ttime=routes(route[-1][0]["lat"],route[-1][0]["lon"],hlat,hlon)
            route.append(h)
            totime=8*3600
        tlen,ttime=routes(hlat,hlon,dlat,dlon)
        totime+=ttime
        route.append([{"장소명": dname,
            "lat":dlat,
            "lon":dlon,
            "거리":tlen,
            "시간":ttime}])
        tlen,ttime=routes(dlat,dlon,slat,slon)
        totime+=ttime
        route.append([{"장소명": sname,
            "lat":slat,
            "lon":slon,
            "거리":tlen,
            "시간":ttime}])
               

        print(f"여행종료시간:{totime//3600}시{(totime%3600)//60}분")
        U.tlist=route
        print(route)
        return U.tlist
