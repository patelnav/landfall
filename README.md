# Hurricane Landfall Map Label Optimization

Follow my progress in this project [here](https://x.com/patelnav/status/1908371085495533707)!

This project aims to reproduce and optimize the label placement for [Michael Ferragamo's visualization](https://x.com/FerragamoWx/status/1908213794314019049) of 1,167 Atlantic hurricane landfalls (1851-2024):

![Original Hurricane Landfall Visualization by Michael Ferragamo](tweet/FerragamoWx.png)

## Progress So Far

### Phase 2: AI-Driven Label Placement ✅
Implemented an agentic loop with Gemini 2.0 Flash Thinking that successfully improved label placement over multiple iterations. The system analyzes overlapping labels in a visualization, generates code changes to fix them, and iteratively improves the layout.

![Phase 2 Progress](output/phase2/phase2_progress.gif)

### Phase 1: Visual Analysis with Gemini AI ✅
Tested if Gemini AI could identify label overlaps in a Florida region map with 116 hurricane landfalls. Both Gemini 2.0 Flash Thinking and 2.5 Pro successfully detected and described the overlaps.

![Florida Hurricane Landfalls](output/south_florida_landfalls.png)

### Phase 0: Baseline Map ✅
First attempt at plotting all US hurricane landfalls with raw label placement:
![Baseline US Hurricane Landfalls](output/baseline_us_cat1_5.png)

## Project Plan

1. **Phase 0: Baseline Map (Completed)** ✅
   - Parsed HURDAT2 data for hurricane landfalls
   - Created initial visualization with raw labels

2. **Phase 1: Visual Analysis with AI (Completed)** ✅
   - Verified AI can identify label overlaps
   - Confirmed viability of multimodal visual analysis

3. **Phase 2: AI-Driven Label Placement (Completed)** ✅
   - Implemented agent loop framework for iterative improvements
   - Successfully generated 6 iterations of improving label placement
   - Demonstrated LLM's ability to analyze visualizations and generate code changes

4. **Phase 3: Scaled Implementation** 📅
   - Apply to full US coastline
   - Fine-tune visual aesthetics

## Acknowledgments

Special thanks to Michael Ferragamo ([@FerragamoWx](https://x.com/FerragamoWx)) for creating the original visualization that inspired this project. 