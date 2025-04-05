# **Phase 0: Foundation & Baseline Setup**:

**Goal:** Prepare necessary data and code foundations, and generate a baseline map showing raw hurricane landfall points and labels (with expected heavy overlap) for comparison later.

**Estimated Cost:** Minimal API cost (likely $0, as no LLM calls needed for this phase). Primarily developer setup time.

**Steps & Implementation Details:**

1.  **Environment Setup:**
    *   Create a Python virtual environment.
    *   Install necessary libraries:
        ```bash
        pip install pandas matplotlib cartopy google-generativeai Pillow requests
        ```
        *(Note: `Pillow` and `requests` might be needed for potential image handling or data fetching later, good to have them)*.
    *   Ensure Cartopy's dependencies (like GEOS, PROJ) are correctly installed, which can sometimes be tricky depending on the OS. Follow Cartopy installation instructions carefully.

2.  **Data Acquisition & Preparation:**
    *   **Download HURDAT2:** Get the latest Atlantic basin HURDAT2 data file (usually a `.txt` file) from the NOAA/NHC website (e.g., `hurdat2-1851-2023-051124.txt` - use the most current version).
    *   **Parse HURDAT2:** Write a Python script (`parse_hurdat.py`) using Pandas to parse the raw HURDAT2 format into a structured DataFrame.
        *   The script should iterate through the file, identifying header lines (storm ID, name, number of entries) and data lines.
        *   Extract columns like `datetime`, `record_identifier` (for 'L' landfall), `status`, `latitude`, `longitude`, `max_wind_knots`.
        *   Handle latitude/longitude formats (N/S/E/W).
        *   Convert `max_wind_knots` to integer.
        *   Store the result perhaps as a CSV or Pickle file (`hurdat_processed.pkl`) for easier loading later.
    *   **Filter for US Hurricane Landfalls:**
        *   Filter the parsed DataFrame for records where `record_identifier` contains 'L' (denoting landfall, primarily US-centric in HURDAT2's standard flagging).
        *   Filter for records where `status` indicates Hurricane strength (`HU`).
        *   *Further filter* based on `max_wind_knots` to ensure **Category 1-5** at landfall (Cat 1 >= 64 knots, Cat 2 >= 83, Cat 3 >= 96, Cat 4 >= 113, Cat 5 >= 137 knots). Create a `category` column based on this.
        *   Add a `year` column extracted from the `datetime`.
        *   Add a `name` column (handling unnamed storms using their ID/year).
        *   Save this filtered data (e.g., `us_hurricane_landfalls_cat1_5.csv`).

3.  **Baseline Plotting Script (`baseline_plot.py`):**
    *   Import `pandas`, `matplotlib.pyplot as plt`, `cartopy.crs as ccrs`, `cartopy.feature as cfeature`.
    *   Load the filtered landfall data (`us_hurricane_landfalls_cat1_5.csv`).
    *   Create a Matplotlib figure and axes with a Cartopy projection (using `ccrs.PlateCarree()` for simplicity as decided).
    *   Set an appropriate map extent covering the US East Coast, Gulf Coast, and perhaps a bit of the Atlantic.
    *   Add map features: `cfeature.COASTLINE`, `cfeature.STATES`, `cfeature.BORDERS`.
    *   **Plot Landfall Points:** Iterate through the DataFrame. For each landfall:
        *   Plot a point (e.g., `ax.scatter`) at the `longitude`, `latitude`. Use color based on the `category` column.
    *   **Add Raw Labels:** Iterate through the DataFrame again. For each landfall:
        *   Add a text label (e.g., `ax.text`) with the storm `name` and `year` (e.g., `"Katrina (2005)"`) positioned *directly at* the `longitude`, `latitude`. Use a small font size. **Do not** use `adjustText` or any overlap avoidance here.
    *   Add a title (e.g., "Baseline US Hurricane Landfalls (Cat 1-5), 1851-Present - Raw Labels").
    *   Save the plot as a PNG image (`baseline_us_cat1_5.png`).

4.  **API Connectivity Check:**
    *   Write a minimal script (`check_api.py`) using the `google-generativeai` library.
    *   Configure it with your API key.
    *   Make a simple text-only call to the chosen Flash model (e.g., "Hello") to confirm authentication and connectivity are working correctly.

**Expected Outputs:**

1.  A processed data file (`us_hurricane_landfalls_cat1_5.csv` or similar) containing filtered landfall points with necessary info (lat, lon, name, year, category).
2.  A Python script (`baseline_plot.py`) that generates the baseline map.
3.  A PNG image (`baseline_us_cat1_5.png`) showing the US coastline and states with colored dots for hurricane landfalls and heavily overlapping text labels placed directly on the points. This serves as the visual baseline for improvement.
4.  Confirmation that the development environment can successfully connect to and get a response from the Gemini API.

This phase lays the groundwork by preparing the core data asset and establishing the visual "problem" (the overlapping baseline map) that the agent will attempt to solve in later phases.