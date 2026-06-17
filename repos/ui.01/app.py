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
    points = data["points"]  # [[lat, lon, name], ...]
    origin = f"{points[0][1]},{points[0][0]}"
    destination = f"{points[-1][1]},{points[-1][0]}"
    waypoints = "|".join([f"{p[1]},{p[0]}" for p in points[1:-1]])

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
