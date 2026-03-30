import requests
from bs4 import BeautifulSoup

def search_web(query):
    # 예시: Bing 검색 URL
    query="+"+query
    url = f"https://www.bing.com/search?q={query}"
    
    response = requests.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        results = []
        
        # 검색 결과 제목과 링크 추출
        for item in soup.select("li.b_algo h2 a"):
            title = item.get_text()
            link = item["href"]
            results.append((title, link))
        
        return results
    else:
        print("검색 실패:", response.status_code)
        return []

# 사용 예시
query = "노원구 찻집"
results = search_web(query)

for title, link in results:
    print(f"- {title}: {link}")
