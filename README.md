Jonel to boi

STEPS TO INSTALL IN LOCAL

open integrated terminal of the folder

pip install -r requirements.txt

python app.py



PROJECT STRUCTURE
-----------------
  artifacts/solar-calculator/
  |-- app.py                   (Flask backend — all logic lives here)
  |-- requirements.txt         (Python package dependencies)
  |-- templates/
  |   |-- index.html           (Jinja2 HTML template — the full UI)
  |-- static/
      |-- css/
      |   |-- style.css        (All styling — colors, layout, cards)
      |-- js/
          |-- calculator.js    (Frontend JavaScript — wizard navigation & API call)


================================================================================
  BACKEND: app.py (Python / Flask)
================================================================================

This file is the heart of the application. It handles:
  1. Storing all reference data (areas, appliances, efficiency factors, panels)
  2. Defining the calculation logic
  3. Exposing two HTTP routes (the page and the calculate endpoint)


--------------------------------------------------------------------------------
1. EMBEDDED DATA
--------------------------------------------------------------------------------

All reference data is hardcoded as Python data structures — no database needed.

  AREAS (list of dicts)
  ---------------------
  Each entry represents one municipality or city covered by ALECO:
    {
      "district":       "1st District",
      "location":       "Tabaco City",
      "classification": "Commercial",   # Commercial or Residential
      "type":           "Mainland",     # Mainland or Island
      "rate":           10.3008,        # Utility rate in ₱/kWh
      "psh":            5.04            # Peak Sun Hours per day
    }

  APPLIANCES (list of dicts)
  --------------------------
  Common Philippine household and office appliances with their wattage:
    {"name": "Air Conditioner (1 ton)", "watts": 900}
    {"name": "Refrigerator",            "watts": 150}
    ... (18 appliances total)

  EFFICIENCY FACTORS (dicts)
  --------------------------
  Maps user selections to numerical derating factors:

    SHADE_FACTORS   = { "none": 1.0, "partial": 0.80, "heavy": 0.50 }
    DUST_FACTORS    = { "weekly": 0.98, "monthly": 0.95, "rarely": 0.90 }
    WEATHER_FACTORS = { "sunny": 1.0, "mixed": 0.85, "cloudy": 0.70 }
    WIRING_FACTOR   = 0.97   (constant — standard 3% wiring loss)

  PANEL_TYPES (dict)
  ------------------
  Two panel types with specs and price ranges:
    "mono" → Monocrystalline Silicon, 400W, ₱8,000–₱15,000 per panel
    "poly" → Polycrystalline Silicon, 320W, ₱5,000–₱10,000 per panel


--------------------------------------------------------------------------------
2. CALCULATION LOGIC  —  calculate(data) function
--------------------------------------------------------------------------------

This function receives the user's form inputs and returns all results.
Here is a step-by-step walkthrough:

  STEP A — Determine Daily Energy Requirement (daily_kwh)
  --------------------------------------------------------
  Two paths depending on the user's chosen input method:

    Option A (Monthly Bill):
      Formula:  daily_kwh = (monthly_bill / rate) / 30

      Explanation:
        - Dividing the bill by the rate converts Philippine Peso to kWh
          consumed in that month.
        - Dividing by 30 gives the average daily consumption.
      Example:  ₱3,500 bill ÷ ₱11.28/kWh ÷ 30 days = 10.34 kWh/day

    Option B (Appliances):
      Formula:  daily_kwh = Σ (watts × hours_of_use) / 1000
                (sum this for every selected appliance)

      Explanation:
        - Watts × Hours gives watt-hours (Wh) of energy used per day.
        - Dividing by 1000 converts to kilowatt-hours (kWh).
      Example:  900W AC × 8 hrs = 7,200 Wh = 7.2 kWh
                150W Ref × 24 hrs = 3,600 Wh = 3.6 kWh
                Total = 10.8 kWh/day

  STEP B — Calculate Combined System Efficiency
  ----------------------------------------------
  Formula:  efficiency = shade_factor × dust_factor × weather_factor × 0.97

  All four factors are multiplied together into a single decimal (0 to 1).
  Example (no shade, monthly cleaning, sunny, standard wiring):
    1.0 × 0.95 × 1.0 × 0.97 = 0.9215  (92.15% efficiency)

  This accounts for real-world losses that reduce how much energy the panels
  actually deliver compared to their rated output.

  STEP C — Calculate Required System Size
  ----------------------------------------
  Formula:  system_size_kwp = daily_kwh / (psh × efficiency)

  Explanation:
    - PSH is how many hours per day the sun shines at full intensity.
    - Multiplying PSH by efficiency gives effective production hours.
    - Dividing daily kWh needed by effective hours gives the system capacity.
  Example:  10.34 kWh ÷ (5.04 hrs × 0.9215) = 2.226 kWp

  STEP D — Calculate Number of Panels
  ------------------------------------
  Formula:  num_panels = ceil(system_size_kwp × 1000 / panel_watts)

  Explanation:
    - Converts kWp to watts (multiply by 1000).
    - Divides by the wattage of a single panel.
    - Uses ceiling (always rounds UP) so the system is never undersized.
  Example:  2,226 W ÷ 400 W/panel = 5.565 → rounds up to 6 panels

  STEP E — Actual System Size
  ----------------------------
  Formula:  actual_size_kwp = (num_panels × panel_watts) / 1000

  Since panel count is a whole number, the actual system may be slightly
  larger than the calculated requirement.
  Example:  6 panels × 400 W = 2,400 W = 2.4 kWp

  STEP F — Estimated Monthly Savings
  ------------------------------------
  Formula:  monthly_savings = daily_kwh × 30 × utility_rate

  Explanation:
    - Assumes full offset of the user's current electricity consumption.
    - Multiplies daily kWh by 30 days to get monthly generation.
    - Multiplies by the utility rate to convert to Philippine Peso savings.
  Example:  10.34 kWh × 30 × ₱11.28 = ₱3,499.78 ≈ ₱3,500/month

  STEP G — Cost Estimation
  -------------------------
  Equipment range:
    low  = num_panels × panel_price_low
    high = num_panels × panel_price_high

  Total cost (including installation at 25% markup):
    total_low  = equipment_low  × 1.25
    total_high = equipment_high × 1.25

  For payback calculation, the midpoint cost is used:
    mid_cost = (price_low + price_high) / 2 × num_panels × 1.25

  STEP H — Payback Period
  ------------------------
  Formula:  payback_years = total_cost_mid / annual_savings

  Explanation:
    - Uses the midpoint cost estimate divided by yearly savings.
    - Result is in years; rounded to one decimal place.
  Example:  ₱86,250 ÷ ₱42,000/year = 2.1 years


--------------------------------------------------------------------------------
3. FLASK ROUTES
--------------------------------------------------------------------------------

  GET  /
  ------
  Renders the main HTML page using Jinja2 template (index.html).
  Passes the AREAS list and APPLIANCES list to the template so the HTML
  can loop through them to generate the area cards and appliance checkboxes.

  POST  /calculate
  -----------------
  Accepts a JSON body from the browser containing all user inputs.
  Calls the calculate() function and returns the results as JSON.

  Request body example:
    {
      "input_mode":    "A",
      "monthly_bill":  3500,
      "area_index":    1,
      "shade":         "none",
      "dust":          "weekly",
      "weather":       "sunny",
      "panel":         "mono"
    }

  Response example:
    {
      "success": true,
      "result": {
        "daily_kwh":        10.342,
        "num_panels":       6,
        "actual_size_kwp":  2.4,
        "monthly_savings":  3500.0,
        "payback_years":    2.1,
        ...
      }
    }


================================================================================
  FRONTEND: index.html + calculator.js (HTML / CSS / Vanilla JavaScript)
================================================================================

The frontend is a SINGLE PAGE — the user never navigates to a new URL.
Instead, JavaScript shows and hides sections (called "steps") as the user
progresses through the wizard.

  index.html (Jinja2 Template)
  ----------------------------
  - The Jinja2 {% for %} loops generate all area radio buttons and appliance
    checkboxes dynamically from the AREAS and APPLIANCES Python lists.
  - The four steps (#step-1 through #step-4) and the results (#step-results)
    are all present in the DOM at once; only the active one is visible.

  calculator.js — Key Functions
  ------------------------------

    goToStep(n)
      Shows the requested step, hides all others, updates the progress bar.
      Calls validation before allowing forward navigation.

    validateStep1() / validateStep2()
      Checks that required fields are filled in before proceeding.
      For Option A: checks that monthly_bill > 0.
      For Option B: checks that at least one appliance has hours > 0.

    updateEfficiencyPreview()
      Reads the currently selected shade, dust, and weather radio buttons,
      multiplies their factors together with 0.97 (wiring), and displays
      the combined efficiency percentage live on Step 3.

    runCalculation()
      Collects ALL user inputs from the form, builds a JSON payload, and
      sends it to POST /calculate using the browser's fetch() API.
      On success, calls renderResults() with the Python-computed data.

    renderResults(r)
      Builds the full HTML results screen dynamically using template
      literals (backtick strings with ${...} expressions).
      Renders KPI cards, detail cards, appliance breakdown table, and
      the disclaimer.

  style.css — Design System
  --------------------------
  Uses CSS custom properties (variables) for the entire color palette:
    --navy:    #1A237E  (deep indigo blue — primary color)
    --sun:     #FFC107  (golden amber — accent color)
    --bg:      #F5F6FF  (light indigo page background)

  Layout uses CSS Grid for multi-column card layouts and Flexbox for
  rows and navigation elements. Fully responsive via media queries.


================================================================================
  DATA FLOW SUMMARY
================================================================================

  1. User opens the page → Flask renders index.html with area & appliance data
  2. User fills in the 4-step wizard (pure HTML + JS, no server calls yet)
  3. User clicks "Calculate My System"
  4. JavaScript collects all inputs → sends POST /calculate request
  5. Python calculate() function runs all formulas → returns JSON
  6. JavaScript receives JSON → renders the results screen in the browser
  7. No page reload at any point


================================================================================
