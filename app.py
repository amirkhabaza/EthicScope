# app.py
import os
from flask import Flask, request, jsonify  # type: ignore
from dotenv import load_dotenv  # type: ignore

# load environment variables from .env
load_dotenv()

# Helper modules
from oc_gleif import lookup_company
from oc_nominatim import geocode_company, geocode_address
from sea_routes import estimate_sea_route  # type: ignore
from parcel import track_parcel

app = Flask(__name__)

@app.route("/", methods=["GET"])
def trace():
    # Query parameters
    company       = request.args.get("company")
    origin_str    = request.args.get("origin")
    dest_str      = request.args.get("destination")
    tracking_code = request.args.get("tracking")

    # 1) Corporate record lookup
    corp = lookup_company(company) if company else {}

    # 2) Geocode origin & destination
    origin = geocode_address(origin_str) if origin_str else {}
    dest   = geocode_address(dest_str)    if dest_str   else {}

    # 3) Sea‐route estimate (stub if no SEAROUTES_KEY)
    sea_leg = {}
    try:
        if origin.get("coordinates") and dest.get("coordinates"):
            # Nominatim returns [lon, lat]
            o_lon, o_lat = origin["coordinates"]
            d_lon, d_lat = dest["coordinates"]
            sea_leg = estimate_sea_route(
                {"lat": o_lat, "lng": o_lon},
                {"lat": d_lat, "lng": d_lon},
            )
    except Exception:
        sea_leg = {"error": "Sea‑route estimation failed."}

    # 4) Parcel tracking via EasyPost
    try:
        parcel_events = track_parcel(tracking_code) if tracking_code else []
    except Exception as e:
        parcel_events = {"error": str(e)}

    return jsonify({
        "corporate_record": corp,
        "origin": origin,
        "destination": dest,
        "sea_leg": sea_leg,
        "parcel_events": parcel_events
    }), 200

if __name__ == "__main__":
    host  = os.getenv("HOST", "127.0.0.1")
    port  = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(host=host, port=port, debug=debug)