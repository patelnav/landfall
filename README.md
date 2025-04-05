# Hurricane Landfall Map Label Optimization

Follow my progress in this project [here](https://x.com/patelnav/status/1908371085495533707)!

This project aims to reproduce and optimize the label placement for [Michael Ferragamo's visualization](https://x.com/FerragamoWx/status/1908213794314019049) of 1,167 Atlantic hurricane landfalls (1851-2024):

![Original Hurricane Landfall Visualization by Michael Ferragamo](tweet/FerragamoWx.png)

## Progress So Far

### Phase 0: Baseline Map ✅
First attempt at plotting all US hurricane landfalls with raw label placement:
![Baseline US Hurricane Landfalls](output/baseline_us_cat1_5.png)

### Phase 1: South Florida Focus 🚧
Testing our label optimization approach on the dense South Florida region:
![South Florida Landfalls](output/south_florida_landfalls.png)

We're using an agentic loop with Gemini 2.0 Flash Thinking to iteratively improve label placement and reduce overlaps.

## Project Progress

### Current Phase: Label Optimization with AI

We're using an agentic loop approach with Gemini 2.0 Flash Thinking to iteratively improve label placement. The process involves:

1. **Phase 0: Baseline Map (Completed)**
   - Parsed HURDAT2 data for all US hurricane landfalls
   - Created initial visualization with raw label placement
   - Established baseline for improvement measurement

2. **Phase 1: South Florida Focus (In Progress)**
   - Selected South Florida region as initial test area
   - Using AI to analyze label overlaps
   - Developing strategies for optimal label placement

3. **Future Phases**
   - Expand to full US coastline
   - Implement advanced label collision avoidance
   - Fine-tune visual aesthetics

## Acknowledgments

Special thanks to Michael Ferragamo ([@FerragamoWx](https://x.com/FerragamoWx)) for creating the original visualization that inspired this project. 