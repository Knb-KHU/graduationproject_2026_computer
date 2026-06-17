import requests
from flask import Flask, render_template, request, jsonify
from tourmaker import findroute,User,call_model

app = Flask(__name__)
restapi = "3b06b2ec80486b28690f23d7c000ee3e"


@app.route("/")
def index():
    user1=User(['청결도','인스타감성'],1.5)
    #coords=findroute(user1,m,t)
    coords=[[{"장소명": "스타벅스 공릉DT점",
            "lat":127.07426417069411,
            "lon":37.620790371073866,}],[{"장소명": "고궁 전주본점",
            "lat":127.11944108335835,
            "lon":35.85005951799748,}]]
    return render_template("index.html", coords=coords)

@app.route("/route", methods=["POST"])
def get_route():
    data = request.json
    points = data["points"]
    origin = f"{points[0]['lon']},{points[0]['lat']}"
    destination = f"{points[-1]['lon']},{points[-1]['lat']}"
    waypoints = "|".join([f"{p['lon']},{p['lat']}" for p in points[1:-1]])

    url = "https://apis-navi.kakaomobility.com/v1/directions"
    headers = {"Authorization": f"KakaoAK {restapi}"}
    params = {
    "origin": origin,
    "destination": destination,
    "waypoints": waypoints,
    "priority": "DISTANCE"
    }

    if waypoints:
        params["waypoints"] = waypoints

    res = requests.get(url, headers=headers, params=params)
    return jsonify(res.json())

if __name__ == "__main__":
    m,t=call_model()
    app.run(host="0.0.0.0", port=5000)
