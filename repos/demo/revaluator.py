import json
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import requests,re
import datetime

def revaluater(question, answers, criteria):
    local_path= "/local_datasets/Qwen2.5-3B-Instruct"
    
    model = AutoModelForCausalLM.from_pretrained(local_path, dtype=torch.float16, local_files_only=True).to("cuda")
    tokenizer = AutoTokenizer.from_pretrained(local_path, local_files_only=True)
    
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
    print(response)
    res=response
    match = re.findall(r"\"answer_id\": 1,.*?ranking", res, re.DOTALL)
    m=match[0].replace("json","").replace("`","")
    j=re.findall(r"overall.*?,",m,re.DOTALL)
    for i in range (len(j)):
        j[i]=float(j[i].replace("overall\":","").replace(",",""))
    print(j)
    sp=[]
    for i in range (len(criteria)):
        k=re.findall(rf"\"{criteria[i]}\":\s*\d+", m, re.DOTALL)
        print(k)
        for t in range (len(k)):
            k[t]=float(k[t].replace(f"\"{criteria[i]}\":","").replace(",",""))
        print(criteria[i],k)
        sp.append(k)
    

    return {
        "individual_results": res,
        "ensemble_scores": j,
        "specific_scores":sp
    }




# --- API 키 설정 ---
placesapi = "AIzaSyCt3hPrnbAejMixTLJlP2xDeZKOq-n_EGw"
restapi = "3b06b2ec80486b28690f23d7c000ee3e"
"""
url="https://dapi.kakao.com/v2/local/search/keyword.json?y=37.514322572335935&x=127.06283102249932&radius=20000"
headers={"Authorization: KakaoAK ${restapi}"}
params={"query":query,
        "size": 5}
  
response = requests.get(url, headers=headers, params=params)
"""

def searchloc(query):
    url="https://dapi.kakao.com/v2/local/search/keyword.json"
    headers={f"Authorization: KakaoAK ${restapi}"}
    params={"query":query,"size": 1}
  
    response = requests.get(url, params=params, headers=headers)
    if(response.status_code==200):
        p=response.json().get('documents', [])
        name=p[0]['place_name']
        lat,lon=p['y'],p['x']
        return lat,lon,name
    else:
        print("error:status_error")
        return 0,0

def routes(sname,slat,slon,dname,dlat,dlon):
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
        dis= data['routes'][0]['summary']['distance']
        tim = data['routes'][0]['summary']['duration']
        return dis,tim
    else:
        print(f"Error: {response.status_code}")
        return None
def get_target_category(current_hour):
    """시간대에 따른 카카오 카테고리 그룹 코드 반환"""
    if 11 <= current_hour <= 13:
        return "FD6" , ["청결도","가성비","맛","서비스"] # 음식점
    elif 19 <= current_hour <= 24 or 0 <= current_hour <= 1:
        return "AD5",["청결도","가성비","부가시설","서비스",""] # 숙박
    else:
        return "CE7",["청결도","가성비","맛","서비스"]  # 기본값: 카페 (사용자 선호 카테고리로 변경 가능)

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
        return None, 0
        
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

def run_evaluation_system(start_lat, start_lng, user_pref_weight=1.2):
    """시스템 메인 실행 함수"""
    current_hour = datetime.datetime.now().hour
    category,criteria = get_target_category(current_hour)
    
    print(f"--- 현재 시간: {current_hour}시 | 선택된 카테고리: {category} ---")
    
    
    kakao_list = get_kakao_places(start_lat, start_lng, category)
    print("불러온 장소 개수:",len(kakao_list))
    results = []
    revtexts=[]
    for p in kakao_list:
        name = p['place_name']
        lat, lng = p['y'], p['x']
        
        print(name,lat,lng)

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
        print(revtext)       
        satisfaction_score = reviewcountapply(g_rating, g_reviews, user_pref_weight)
        revtexts.append(revtext)
        results.append({
            "장소명": name,
            "거리": f"{p['distance']}m",
            "Google평점": g_rating,
            "리뷰수": g_reviews,
            "최종만족도": satisfaction_score,
            "리뷰내용":revtext
        })
    print(len(revtexts),":",revtexts)
    
    ensemble_result = revaluater("How was the place you experienced", revtexts, criteria)
    for i in range (len(ensemble_result["ensemble_scores"])):
        results[i]["상대평점"]=ensemble_result["ensemble_scores"][i]
    
    # 최종 점수순 정렬
    results.sort(key=lambda x: x['최종만족도'], reverse=True)
    
    return results

# --- 실행 예시 ---
if __name__ == "__main__":
    # 시작 장소 좌표 (예: 강남역 인근)
    START_LAT = 37.4979
    START_LNG = 127.0276
    
    final_list = run_evaluation_system(START_LAT, START_LNG)
    
    print(f"{'장소명':<15} | {'거리':<6} | {'Google':<5} | {'리뷰수':<5} | {'만족도 점수'} | {'리뷰내용'} | {'상대평점'}" )
    print("-" * 70)
    for item in final_list:
        print(f"{item['장소명']:<15} | {item['거리']:<6} | {item['Google평점']:<6} | {item['리뷰수']:<6} | {item['최종만족도']} | {item['리뷰내용']} | {item['상대평점']}")

