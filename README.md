# Hurricane Landfall Map Label Optimization

Follow my progress in this project [here](https://x.com/patelnav/status/1908371085495533707)!

This project aims to reproduce and optimize the label placement for [Michael Ferragamo's visualization](https://x.com/FerragamoWx/status/1908213794314019049) of 1,167 Atlantic hurricane landfalls (1851-2024):

<img src="tweet/FerragamoWx.png" alt="Original Hurricane Landfall Visualization by Michael Ferragamo" width="300">

## Progress So Far

### Phase 3: Full-Scale Implementation 🚧

#### Algorithmic Clustering Approach (Current)

We've implemented a systematic algorithmic approach to address the label placement challenges:

1. **DBSCAN Clustering**: Applied DBSCAN to group hurricane landfalls with a custom coastline-aware distance metric that gives more weight to longitude differences.
2. **Collision Detection**: Implemented polygon-based collision detection for label boxes that accounts for their actual dimensions.

The algorithmic approach gets closer to where we want to be, but lots of work to make this look any good:

<img src="output/phase3_algo/florida_algo_animation.gif" alt="Phase 3 Algorithmic Approach Animation" width="500">

Next steps for this approach include:
- Refining the collision detection to handle additional edge cases
- Implementing more sophisticated rules for initial label placement based on geographic regions
- Exploring additional visual hierarchy improvements for dense hurricane regions
- Combining the algorithmic approach with LLM-guided fine-tuning for optimal results

#### Earlier Approach: LLM-Guided Point Adjustments

Previously, we explored an LLM-guided approach using diff-based adjustments:

1. **Initial Strategies**: Tested regional strategies and cluster-based positioning.
2. **Incremental Approach**: Added clusters incrementally with adjustText for optimization.
3. **Diff-Based Corrections**: Implemented a system where the LLM identifies and fixes overlapping labels one by one.

<img src="output/phase3/florida_iterations-2.gif" alt="Phase 3 Iterations with Diff-Based Approach" width="500">

While this approach showed promise, it highlighted the need for more systematic rules for clustering and label placement, which led to our current algorithmic solution.

### Phase 2: AI-Driven Label Placement ✅
Implemented an agentic loop with Gemini 2.0 Flash Thinking that successfully improved label placement over multiple iterations. The system analyzes overlapping labels in a visualization, generates code changes to fix them, and iteratively improves the layout.

<img src="output/phase2/phase2_progress.gif" alt="Phase 2 Progress" width="500">

### Phase 1: Visual Analysis with Gemini AI ✅
Tested if Gemini AI could identify label overlaps in a Florida region map with 116 hurricane landfalls. Both Gemini 2.0 Flash Thinking and 2.5 Pro successfully detected and described the overlaps.

<img src="output/south_florida_landfalls.png" alt="Florida Hurricane Landfalls" width="500">

### Phase 0: Baseline Map ✅
First attempt at plotting all US hurricane landfalls with raw label placement:
<img src="output/baseline_us_cat1_5.png" alt="Baseline US Hurricane Landfalls" width="500">

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

4. **Phase 3: Full-Scale Implementation (In Progress)** 🚧
   - Applied to full US coastline with significant hurricanes
   - Implemented diff-based approach for precise label adjustments
   - Successfully generated 10+ iterations of improving label placement
   - Next steps: 
     - Develop more sophisticated geographic clustering
     - Implement systematic leader line placement rules
     - Create region-specific label placement strategies
     - Balance automated clustering with LLM-guided refinements

## Lessons Learned & Next Steps

The project has revealed several challenges in scaling LLM-guided data visualization:

1. **Geographic Context Matters**: Breaking down the problem geographically is essential
2. **Incremental Improvement Strategy**: The diff-based approach allows for precise adjustments but needs better initial placement
3. **Balance of Automation and Guidance**: Finding the right level of structure to provide the LLM remains challenging
4. **Systematic Clustering**: Need to develop better rules for initial label placement and leader line generation
5. **Region-Specific Strategies**: Different coastal regions may need different placement strategies

Future work will focus on:
1. Developing more sophisticated geographic clustering algorithms
2. Creating systematic rules for leader line placement
3. Implementing region-specific label placement strategies
4. Balancing automated clustering with LLM-guided refinements
5. Improving the visual hierarchy of labels and leader lines

## Acknowledgments

Special thanks to Michael Ferragamo ([@FerragamoWx](https://x.com/FerragamoWx)) for creating the original visualization that inspired this project. 