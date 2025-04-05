# Phase 2: Agentic Code Generation & Basic History Loop

This directory contains the outputs from Phase 2 of the Hurricane Landfall Map Label Optimization project.

## Overview

In Phase 2, we successfully implemented an agentic loop using Gemini 2.0 Flash Thinking that iteratively improved label placement for a cluster of overlapping hurricane labels in the Miami area.

## Files

- `test_cluster_data.csv`: Contains data for the Miami area cluster (16 hurricane landfalls)
- `output_iteration_0.png` through `output_iteration_5.png`: Visualizations showing the progressive improvement of label layout
- `agent_loop_log.json`: Detailed log of each iteration, including prompts and model responses
- `phase2_progress.gif`: Animated GIF showing the progression of improvements

## Agent Loop Process

1. The agent starts with an initial visualization showing overlapping labels in the Miami area.
2. For each iteration:
   - The visualization is sent to Gemini 2.0 Flash Thinking for analysis
   - The model identifies overlapping labels and generates code changes to fix them
   - The new code is executed to produce the next visualization
   - The process repeats with the updated visualization

## Results

The agent successfully improved label placement over 6 iterations by implementing various strategies:

1. Iteration 1: Added vertical offsets to separate overlapping labels
2. Iteration 2: Implemented index-based offsets to create a staggered appearance
3. Iteration 3: Adjusted horizontal positioning to better distribute labels
4. Iteration 4: Further refined label positioning based on hurricane category
5. Iteration 5: Implemented varied offsets to minimize overlaps

This demonstrates that an LLM can effectively analyze visualizations, identify issues, and generate code to address those issues in an iterative fashion, with each iteration building on the previous improvements.

## Next Steps

This successful proof of concept will be scaled up in Phase 3 to handle the full US coastline hurricane dataset with all 1,167 landfalls. 