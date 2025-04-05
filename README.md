# Hurricane Landfall Map Label Optimization

## Phase 0: Foundation & Baseline Setup

This project aims to improve label layout on hurricane landfall maps using an agentic loop with Gemini 2.0 Flash Thinking.

### Environment Setup

1. Create a Python virtual environment using uv:
   ```bash
   uv venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   uv pip install -r requirements.txt
   ```

### Data Preparation

1. Download the HURDAT2 data file:
   - Visit: https://www.nhc.noaa.gov/data/hurdat/hurdat2-1851-2023-051124.txt
   - Save the file to the `data/` directory as `hurdat2-1851-2023-051124.txt`

2. Parse the HURDAT2 data:
   ```bash
   python src/parse_hurdat.py
   ```
   This will create `data/us_hurricane_landfalls_cat1_5.csv` with filtered landfall data.

### Generate Baseline Map

Run the baseline plotting script to create a map with raw labels:
```bash
python src/baseline_plot.py
```
This will generate `output/baseline_us_cat1_5.png` showing all US hurricane landfalls with labels placed directly at the landfall points.

### API Connectivity Check

1. Set your Gemini API key:
   ```bash
   export GEMINI_API_KEY='your-api-key-here'
   ```

2. Test the API connection:
   ```bash
   python src/check_api.py
   ```

## Project Structure

```
landfall/
├── data/                      # Data files
│   ├── hurdat2-1851-2023-051124.txt  # Raw HURDAT2 data
│   └── us_hurricane_landfalls_cat1_5.csv  # Processed landfall data
├── output/                    # Generated images
│   └── baseline_us_cat1_5.png  # Baseline map with raw labels
├── src/                       # Source code
│   ├── parse_hurdat.py        # HURDAT2 data parser
│   ├── baseline_plot.py       # Baseline map generator
│   └── check_api.py           # API connectivity check
├── .venv/                     # Python virtual environment
├── requirements.txt           # Project dependencies
└── README.md                  # This file
``` 