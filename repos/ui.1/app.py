import requests
from flask import Flask, render_template, request, jsonify
from tourmaker import findroute,User,call_model

app = Flask(__name__)
restapi = "3b06b2ec80486b28690f23d7c000ee3e"


@app.route("/")
def index():
    user1=User(['청결도','인스타감성'],1.5)
    coords=findroute(user1,m,t)
    
    return render_template("index.html", coords=coords)


@app.route("/route", methods=["POST"])
def get_route():
    data = request.json
    points = data["points"]  # [{"lat": ..., "lon": ...}, ...]

    url = "https://apis-navi.kakaomobility.com/v1/directions"
    headers = {"Authorization": f"KakaoAK {restapi}"}

    all_sections = []
    summary = {"origin": None, "destination": None, "waypoints": []}

    # 출발지부터 목적지까지 3개 경유지 단위로 잘라 호출
    for i in range(0, len(points)-1, 4):  # 1+최대3+1 구조
        chunk = points[i:i+5]
        origin = f"{chunk[0]['lon']},{chunk[0]['lat']}"
        destination = f"{chunk[-1]['lon']},{chunk[-1]['lat']}"
        waypoints = "|".join([f"{p['lon']},{p['lat']}" for p in chunk[1:-1]])

        params = {
            "origin": origin,
            "destination": destination,
            "priority": "DISTANCE"
        }
        if waypoints:
            params["waypoints"] = waypoints

        res = requests.get(url, headers=headers, params=params)
        data_chunk = res.json()

        
        if "routes" in data_chunk and data_chunk["routes"]:
            all_sections.extend(data_chunk["routes"][0]["sections"])
            if summary["origin"] is None:
                summary["origin"] = data_chunk["routes"][0]["summary"]["origin"]
            summary["destination"] = data_chunk["routes"][0]["summary"]["destination"]

            # ✅ waypoints에 extra_info 병합
            for wp in data_chunk["routes"][0]["summary"].get("waypoints", []):
                for p in chunk:
                    try:
                        lon = float(p["lon"])
                        lat = float(p["lat"])
                    except (TypeError, ValueError):
                        continue
                    if abs(wp["x"] - lon) < 1e-5 and abs(wp["y"] - lat) < 1e-5:
                        wp["extra_info"] = {
                            "Google평점": p.get("Google평점"),
                            "리뷰수": p.get("리뷰수"),
                            "최종만족도": p.get("최종만족도"),
                            "리뷰내용": p.get("리뷰내용")
                        }
            summary["waypoints"].extend(data_chunk["routes"][0]["summary"].get("waypoints", []))


    return jsonify({
        "routes": [{
            "summary": summary,
            "sections": all_sections
        }]
    })

if __name__ == "__main__":
    m,t=call_model()
    app.run(host="0.0.0.0", port=5000)
