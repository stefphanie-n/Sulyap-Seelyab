import os
import math
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "solar-calc-secret")

AREAS = [
    {"district": "1st District", "location": "Tabaco City",  "classification": "Commercial", "type": "Mainland", "rate": 10.3008, "psh": 5.04},
    {"district": "1st District", "location": "Tiwi",          "classification": "Residential","type": "Mainland", "rate": 11.2812, "psh": 5.04},
    {"district": "1st District", "location": "Malinao",       "classification": "Residential","type": "Mainland", "rate": 11.2812, "psh": 5.04},
    {"district": "1st District", "location": "Bacacay",       "classification": "Residential","type": "Mainland", "rate": 11.2812, "psh": 5.04},
    {"district": "1st District", "location": "Malilipot",     "classification": "Residential","type": "Mainland", "rate": 11.2812, "psh": 5.04},
    {"district": "1st District", "location": "Sto. Domingo",  "classification": "Residential","type": "Mainland", "rate": 11.2812, "psh": 5.04},
    {"district": "2nd District", "location": "Legazpi City",  "classification": "Commercial", "type": "Mainland", "rate": 10.3008, "psh": 4.98},
    {"district": "2nd District", "location": "Daraga",        "classification": "Commercial", "type": "Mainland", "rate": 10.3008, "psh": 4.98},
    {"district": "2nd District", "location": "Camalig",       "classification": "Residential","type": "Mainland", "rate": 11.2812, "psh": 4.98},
    {"district": "2nd District", "location": "Guinobatan",    "classification": "Residential","type": "Mainland", "rate": 11.2812, "psh": 4.98},
    {"district": "2nd District", "location": "Rapu-Rapu",     "classification": "Residential","type": "Island",   "rate": 10.3008, "psh": 5.11},
    {"district": "2nd District", "location": "Manito",        "classification": "Residential","type": "Mainland", "rate": 10.3008, "psh": 4.92},
    {"district": "3rd District", "location": "Ligao City",    "classification": "Commercial", "type": "Mainland", "rate": 10.3008, "psh": 4.85},
    {"district": "3rd District", "location": "Oas",           "classification": "Residential","type": "Mainland", "rate": 11.2812, "psh": 4.85},
    {"district": "3rd District", "location": "Polangui",      "classification": "Residential","type": "Mainland", "rate": 11.2812, "psh": 4.85},
    {"district": "3rd District", "location": "Libon",         "classification": "Residential","type": "Mainland", "rate": 11.2812, "psh": 4.85},
    {"district": "3rd District", "location": "Pio Duran",     "classification": "Residential","type": "Mainland", "rate": 11.2812, "psh": 4.78},
    {"district": "3rd District", "location": "Jovellar",      "classification": "Residential","type": "Mainland", "rate": 11.2812, "psh": 4.78},
]

APPLIANCES = [
    {"name": "Air Conditioner (1 ton)",    "watts": 900},
    {"name": "Air Conditioner (1.5 ton)",  "watts": 1500},
    {"name": "Air Conditioner (2 ton)",    "watts": 2000},
    {"name": "Refrigerator",               "watts": 150},
    {"name": "Electric Fan",               "watts": 70},
    {"name": "LED TV (32\")",              "watts": 30},
    {"name": "LED TV (50\")",              "watts": 80},
    {"name": "Washing Machine",            "watts": 500},
    {"name": "Electric Water Heater",      "watts": 2000},
    {"name": "LED Bulb",                   "watts": 10},
    {"name": "Fluorescent Light",          "watts": 20},
    {"name": "Rice Cooker",                "watts": 700},
    {"name": "Microwave Oven",             "watts": 1000},
    {"name": "Electric Iron",              "watts": 1200},
    {"name": "Desktop Computer",           "watts": 200},
    {"name": "Laptop",                     "watts": 65},
    {"name": "WiFi Router",                "watts": 10},
    {"name": "Electric Stove (1 burner)",  "watts": 1500},
]

SHADE_FACTORS   = {"none": 1.0,  "partial": 0.80, "heavy": 0.50}
DUST_FACTORS    = {"weekly": 0.98, "monthly": 0.95, "rarely": 0.90}
WEATHER_FACTORS = {"sunny": 1.0,  "mixed": 0.85,  "cloudy": 0.70}
WIRING_FACTOR   = 0.97

PANEL_TYPES = {
    "mono": {
        "name": "Monocrystalline Silicon",
        "watts": 400,
        "price_low": 8000,
        "price_high": 15000,
        "description": "Best for residential roofs with limited space, as they produce more power per square meter.",
        "efficiency_label": "High Efficiency (18–22%)",
    },
    "poly": {
        "name": "Polycrystalline Silicon",
        "watts": 320,
        "price_low": 5000,
        "price_high": 10000,
        "description": "Best for larger installations where space isn't a primary concern and the budget is tighter.",
        "efficiency_label": "Moderate Efficiency (15–17%)",
    },
}


def calculate(data):
    input_mode = data.get("input_mode")
    area_index = int(data.get("area_index", 0))
    shade    = data.get("shade", "none")
    dust     = data.get("dust", "monthly")
    weather  = data.get("weather", "sunny")
    panel    = data.get("panel", "mono")

    area = AREAS[area_index]
    psh  = area["psh"]
    rate = area["rate"]

    if input_mode == "A":
        monthly_bill = float(data.get("monthly_bill", 0))
        daily_kwh = (monthly_bill / rate) / 30
    else:
        appliance_usage = data.get("appliance_usage", {})
        daily_kwh = 0.0
        breakdown = []
        for app_data in APPLIANCES:
            hours = float(appliance_usage.get(app_data["name"], 0) or 0)
            kwh = (app_data["watts"] * hours) / 1000
            if hours > 0:
                breakdown.append({
                    "name": app_data["name"],
                    "watts": app_data["watts"],
                    "hours": hours,
                    "kwh": round(kwh, 3),
                })
            daily_kwh += kwh

    system_efficiency = (
        SHADE_FACTORS.get(shade, 1.0) *
        DUST_FACTORS.get(dust, 0.95) *
        WEATHER_FACTORS.get(weather, 1.0) *
        WIRING_FACTOR
    )

    panel_info = PANEL_TYPES[panel]
    panel_watts = panel_info["watts"]

    system_size_kwp = daily_kwh / (psh * system_efficiency)
    num_panels = math.ceil(system_size_kwp * 1000 / panel_watts)
    actual_size_kwp = round((num_panels * panel_watts) / 1000, 2)

    monthly_savings = daily_kwh * 30 * rate
    annual_savings  = monthly_savings * 12

    panel_price_mid   = (panel_info["price_low"] + panel_info["price_high"]) / 2
    equipment_cost    = num_panels * panel_price_mid
    installation_cost = equipment_cost * 0.25
    total_cost        = equipment_cost + installation_cost
    payback_years     = total_cost / annual_savings if annual_savings > 0 else 0

    result = {
        "area": area,
        "daily_kwh": round(daily_kwh, 3),
        "psh": psh,
        "system_efficiency_pct": round(system_efficiency * 100, 1),
        "system_size_kwp": round(system_size_kwp, 3),
        "num_panels": num_panels,
        "actual_size_kwp": actual_size_kwp,
        "panel_info": panel_info,
        "monthly_savings": round(monthly_savings, 2),
        "annual_savings": round(annual_savings, 2),
        "equipment_cost_low":  round(num_panels * panel_info["price_low"], 2),
        "equipment_cost_high": round(num_panels * panel_info["price_high"], 2),
        "total_cost_low":  round(num_panels * panel_info["price_low"] * 1.25, 2),
        "total_cost_high": round(num_panels * panel_info["price_high"] * 1.25, 2),
        "payback_years": round(payback_years, 1),
        "shade": shade,
        "dust": dust,
        "weather": weather,
        "input_mode": input_mode,
    }

    if input_mode == "B":
        result["appliance_breakdown"] = breakdown

    return result


@app.route("/")
def index():
    return render_template("index.html", areas=AREAS, appliances=APPLIANCES)


@app.route("/calculate", methods=["POST"])
def do_calculate():
    try:
        data = request.get_json()
        result = calculate(data)
        return jsonify({"success": True, "result": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/download-report", methods=["POST"])
def download_report():
    try:
        data = request.get_json()
        r = calculate(data)

        loc       = r["area"].get("location", "Custom Location")
        pname     = r["panel_info"]["name"]
        generated = datetime.now().strftime("%B %d, %Y %I:%M %p")

        def peso(n):
            return "₱{:,.2f}".format(n)

        shade_label   = {"none": "None (×1.00)", "partial": "Partial (×0.80)", "heavy": "Heavy (×0.50)"}
        dust_label    = {"weekly": "Weekly (×0.98)", "monthly": "Monthly (×0.95)", "rarely": "Rarely (×0.90)"}
        weather_label = {"sunny": "Mostly Sunny (×1.00)", "mixed": "Mixed (×0.85)", "cloudy": "Often Cloudy (×0.70)"}

        appliance_html = ""
        if r.get("input_mode") == "B" and r.get("appliance_breakdown"):
            rows = "".join(
                f"<tr><td>{a['name']}</td><td>{a['watts']}W</td>"
                f"<td>{a['hours']} hrs</td><td>{a['kwh']:.3f} kWh</td></tr>"
                for a in r["appliance_breakdown"]
            )
            appliance_html = f"""
            <div class="section">
              <div class="section-head">Appliance Breakdown</div>
              <table>
                <thead><tr><th>Appliance</th><th>Watts</th><th>Hours/Day</th><th>Daily kWh</th></tr></thead>
                <tbody>{rows}</tbody>
              </table>
            </div>"""

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SULYAP-SEELYAB Solar Report — {loc}</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Segoe UI', system-ui, sans-serif;
    font-size: 13px;
    color: #111827;
    background: #fff;
    padding: 0;
  }}
  .page {{ max-width: 800px; margin: 0 auto; padding: 32px 40px 48px; }}
  .header {{
    background: #1A237E;
    color: #fff;
    padding: 20px 32px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-radius: 10px 10px 0 0;
  }}
  .header-logo {{ font-size: 1.25rem; font-weight: 800; letter-spacing: -0.01em; }}
  .header-logo em {{ color: #FFC107; font-style: normal; }}
  .header-sub {{ font-size: 0.72rem; color: rgba(255,255,255,0.55); margin-top: 2px; }}
  .header-date {{ font-size: 0.72rem; color: rgba(255,255,255,0.6); text-align: right; }}
  .body {{ border: 1.5px solid #E5E7EB; border-top: none; border-radius: 0 0 10px 10px; padding: 28px 32px 32px; }}
  .location-tag {{
    display: inline-block;
    background: #E8EAF6;
    color: #1A237E;
    font-size: 0.8rem;
    font-weight: 700;
    padding: 4px 14px;
    border-radius: 99px;
    margin-bottom: 20px;
  }}
  .kpi-row {{ display: grid; grid-template-columns: repeat(3,1fr); gap: 12px; margin-bottom: 24px; }}
  .kpi {{
    background: #1A237E;
    border-radius: 10px;
    padding: 18px 12px;
    text-align: center;
    color: #fff;
  }}
  .kpi-label {{ font-size: 0.62rem; text-transform: uppercase; letter-spacing: 0.07em; color: rgba(255,255,255,0.55); font-weight: 600; margin-bottom: 6px; }}
  .kpi-val   {{ font-size: 1.8rem; font-weight: 800; color: #FFC107; line-height: 1.1; letter-spacing: -0.02em; }}
  .kpi-sub   {{ font-size: 0.66rem; color: rgba(255,255,255,0.45); margin-top: 4px; }}
  .section {{ margin-bottom: 14px; border: 1.5px solid #E5E7EB; border-radius: 8px; overflow: hidden; }}
  .section-head {{
    background: #E8EAF6;
    color: #1A237E;
    font-size: 0.66rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 8px 16px;
  }}
  .row {{ display: flex; justify-content: space-between; padding: 9px 16px; border-bottom: 1px solid #F3F4F6; font-size: 0.82rem; }}
  .row:last-child {{ border-bottom: none; }}
  .row strong {{ font-weight: 600; color: #111827; }}
  .row.highlight {{ background: #FFFDE7; }}
  .row.highlight strong {{ color: #1A237E; font-weight: 700; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.8rem; }}
  thead tr {{ background: #F9FAFB; }}
  th, td {{ padding: 8px 14px; text-align: left; border-bottom: 1px solid #F3F4F6; }}
  th {{ font-weight: 700; font-size: 0.72rem; color: #6B7280; text-transform: uppercase; letter-spacing: 0.05em; }}
  .disclaimer {{
    background: #FFFDE7;
    border-left: 3px solid #FFC107;
    border-radius: 6px;
    padding: 10px 14px;
    font-size: 0.75rem;
    color: #6B7280;
    line-height: 1.6;
    margin-top: 18px;
  }}
  .footer {{
    text-align: center;
    margin-top: 24px;
    font-size: 0.7rem;
    color: #9CA3AF;
  }}
  @media print {{
    body {{ print-color-adjust: exact; -webkit-print-color-adjust: exact; }}
    .page {{ padding: 0; }}
  }}
</style>
</head>
<body>
<div class="page">
  <div class="header">
    <div>
      <div class="header-logo">SULYAP&#8209;<em>SEE</em>LYAB</div>
      <div class="header-sub">Albay Solar Sizing Estimator</div>
    </div>
    <div class="header-date">Generated<br>{generated}</div>
  </div>
  <div class="body">
    <div class="location-tag">&#9728; {loc} &nbsp;&middot;&nbsp; {pname} &nbsp;&middot;&nbsp; {r["system_efficiency_pct"]}% efficiency</div>

    <div class="kpi-row">
      <div class="kpi">
        <div class="kpi-label">System Size</div>
        <div class="kpi-val">{r["actual_size_kwp"]} kWp</div>
        <div class="kpi-sub">{r["num_panels"]} &times; {r["panel_info"]["watts"]}W panels</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">Monthly Savings</div>
        <div class="kpi-val">{peso(r["monthly_savings"])}</div>
        <div class="kpi-sub">{peso(r["annual_savings"])} / year</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">Payback Period</div>
        <div class="kpi-val">{r["payback_years"]} yrs</div>
        <div class="kpi-sub">Based on mid-range estimate</div>
      </div>
    </div>

    <div class="section">
      <div class="section-head">System Details</div>
      <div class="row"><span>Daily Energy Need</span><strong>{r["daily_kwh"]} kWh / day</strong></div>
      <div class="row"><span>Peak Sun Hours (PSH)</span><strong>{r["psh"]} hrs / day</strong></div>
      <div class="row"><span>Combined Efficiency</span><strong>{r["system_efficiency_pct"]}%</strong></div>
      <div class="row"><span>Required Capacity</span><strong>{r["system_size_kwp"]} kWp</strong></div>
      <div class="row"><span>Panels Required</span><strong>{r["num_panels"]} panels ({r["actual_size_kwp"]} kWp)</strong></div>
    </div>

    <div class="section">
      <div class="section-head">Cost Estimate (Equipment + 25% Installation)</div>
      <div class="row"><span>Panel Type</span><strong>{pname}, {r["panel_info"]["watts"]}W</strong></div>
      <div class="row"><span>Price per Panel</span><strong>{peso(r["panel_info"]["price_low"])} – {peso(r["panel_info"]["price_high"])}</strong></div>
      <div class="row"><span>Equipment Cost</span><strong>{peso(r["equipment_cost_low"])} – {peso(r["equipment_cost_high"])}</strong></div>
      <div class="row highlight"><span>Total Estimated Cost</span><strong>{peso(r["total_cost_low"])} – {peso(r["total_cost_high"])}</strong></div>
    </div>

    <div class="section">
      <div class="section-head">Efficiency Factors Applied</div>
      <div class="row"><span>Location</span><strong>{loc} (&#8369;{r["area"].get("rate", 0):.4f}/kWh)</strong></div>
      <div class="row"><span>Shade</span><strong>{shade_label.get(r["shade"], r["shade"])}</strong></div>
      <div class="row"><span>Dust / Cleaning</span><strong>{dust_label.get(r["dust"], r["dust"])}</strong></div>
      <div class="row"><span>Weather</span><strong>{weather_label.get(r["weather"], r["weather"])}</strong></div>
      <div class="row"><span>Wiring Loss</span><strong>Standard (×0.97)</strong></div>
    </div>

    {appliance_html}

    <div class="disclaimer">
      <strong>Note:</strong> These are rough estimates for planning purposes only. Actual performance depends on
      roof orientation, net metering eligibility, installer assessment, and panel degradation over time.
      Consult a PEC-accredited solar installer for a formal quotation.
    </div>
    <div class="footer">SULYAP-SEELYAB &mdash; Albay Solar Sizing Estimator &mdash; {generated}</div>
  </div>
</div>
</body>
</html>"""

        filename = f"SULYAP-SEELYAB-Report-{loc.replace(' ', '-')}.html"
        return Response(
            html,
            mimetype="text/html",
            headers={"Content-Disposition": f"attachment; filename=\"{filename}\""}
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port, debug=False)
