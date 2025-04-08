Okay, this is a significant but potentially very effective pivot! Moving away from the LLM for fine-grained layout and towards a structured, deterministic algorithm based on your observations of the target map makes a lot of sense. The core idea is to treat cluster labels as grouped units within polygons and manage the placement of these polygons algorithmically.

Here's an algorithm concept and a phased plan to implement it, replacing the previous LLM-based Phase 3 approach.

**Algorithm Concept: Structured Polygon Placement**

1.  **Initialization:**
    *   Load landfall data (filtered for Florida, Cat 1-5).
    *   Define map projection (Plate Carree or Albers Equal Area) and plotting area (Matplotlib/Cartopy axes).
    *   Initialize an empty list to store the bounding polygons of already placed clusters (`placed_polygons`).

2.  **Clustering & Ordering:**
    *   Perform spatial clustering on landfall points (DBSCAN, as before, or adjust parameters if needed).
    *   Determine an order to process clusters (e.g., by significance/category mean, then by location - maybe south-to-north or coast-inward to place offshore labels first).

3.  **Iterative Cluster Placement Loop:** For each cluster `C` in the determined order:
    *   **a. Calculate Label Box Geometry:**
        *   Get points `P` belonging to cluster `C`.
        *   Determine number of labels `N = len(P)`.
        *   Estimate text dimensions (requires font metrics or approximation) to calculate required height (`box_H`) and width (`box_W`) for a rectangular label box. Assume fixed font size, vertical stacking, left/right alignment.
        *   Calculate the relative coordinates of each label *within* this theoretical box (e.g., label `j` at `(padding_x, box_H - (j+0.5) * line_height)` for left-alignment).
    *   **b. Determine Target Placement Area & Initial Position:**
        *   Based on the cluster's centroid (`centroid_x`, `centroid_y`), define a preferred placement region (e.g., "offshore to the east", "northwest margin").
        *   Calculate an initial target position (`target_x`, `target_y`) for the *corner* (e.g., bottom-left) of the label box within this preferred region. This requires heuristics (e.g., if `centroid_x > -81`, place box further east; if `centroid_y < 27`, place box north or east).
    *   **c. Collision Detection & Repositioning:**
        *   **Create Candidate Polygon:** Define the candidate bounding polygon (`candidate_poly`) for this cluster. This polygon should enclose both the cluster's points (`P`) *and* the theoretical label box placed at (`target_x`, `target_y`). A simple approach is the rectangular minimum bounding box (MBR) covering all points and the label box corners. A more complex but tighter fit is the convex hull. Use Shapely library for geometry.
        *   **Check Overlaps:** Iterate through `placed_polygons`. If `candidate_poly.intersects(existing_poly)` for any `existing_poly`, a collision exists.
        *   **Reposition (if collision):**
            *   Define a search strategy to find a non-colliding position for the label box. Examples:
                *   Try moving the label box slightly further offshore (e.g., increase x offset if east, decrease if west).
                *   Try moving it perpendicular to the initial offset direction.
                *   Implement a limited spiral search or grid search around the initial target position.
            *   For each new trial position, recalculate the `candidate_poly` and re-check for collisions.
            *   Stop after a fixed number of attempts or when a non-colliding position is found. If no position is found, accept the last tried position (documenting the overlap) or potentially skip labeling this cluster for now.
        *   **Final Position:** Set the `final_x`, `final_y` for the label box corner based on the successful (or last-attempted) position.
    *   **d. Store Final Polygon:** Calculate the final bounding polygon based on the points `P` and the label box at (`final_x`, `final_y`). Add this polygon to `placed_polygons`.
    *   **e. Render Cluster Elements:**
        *   Draw the landfall points `P` on the map.
        *   (Optional) Draw the label box rectangle background at (`final_x`, `final_y`) with `box_W`, `box_H`.
        *   Draw the labels *inside* the box area, using their calculated relative coordinates transformed by (`final_x`, `final_y`). Ensure correct alignment (left/right).
        *   Draw leader lines (`ConnectionPatch`) from each point in `P` to its corresponding label's anchor point within the placed box.

4.  **Finalization:** Add title, legend, save the map.

---

**Phased Implementation Plan (Replacing Previous Phase 3):**

**Phase 3.A: Cluster Geometry & Single Box Rendering**

*   **Goal:** Implement the core geometry calculations for a *single* cluster's label box, alignment, leader lines, and bounding polygon *without* collision detection or iteration.
*   **Checkpoints:**
    1.  Clustering works and identifies logical groups.
    2.  Label box dimensions are calculated reasonably based on label count/text size.
    3.  Labels are correctly aligned (e.g., left-aligned) *within* the theoretical box coordinates.
    4.  Leader lines connect points to their respective label positions within the box.
    5.  A bounding polygon (MBR or convex hull) for the points + box is calculated using Shapely.
    6.  Script can render *one* specified cluster with its labels placed at an *arbitrary* fixed position.

*   **To-Do List:**
    1.  **New Script:** Create `src/plotting_script_phase3_algorithmic.py`. Copy relevant data loading, map setup, and clustering logic from previous scripts. Install `shapely` (`pip install shapely`).
    2.  **Cluster Selection:** Modify the script to accept a `cluster_id` to process, or just hardcode it to process the first/most significant cluster initially.
    3.  **Label Box Calculation:**
        *   Implement logic to estimate text width/height (can start with rough fixed values per character/line, e.g., `line_height = 0.2`, `char_width = 0.05` in map units - needs tuning).
        *   Calculate `box_W` and `box_H`.
        *   Calculate relative `(x, y)` for each label within the box based on chosen alignment (e.g., `label_rel_y = box_H - (j+0.5) * line_height`).
    4.  **Hardcoded Placement:** Define fixed `target_x`, `target_y` coordinates for placing the label box (e.g., somewhere visibly offshore).
    5.  **Rendering:**
        *   Draw the points for the selected cluster.
        *   Draw the labels at `target_x + label_rel_x`, `target_y + label_rel_y`.
        *   Draw `ConnectionPatch` leader lines from data points to these absolute label coordinates.
        *   (Optional) Draw the background rectangle for the label box.
    6.  **Bounding Polygon Calculation:**
        *   Get coordinates of all cluster points and the four corners of the label box placed at `(target_x, target_y)`.
        *   Use `shapely.geometry.MultiPoint` and then `.minimum_rotated_rectangle` or `.convex_hull` to calculate the bounding polygon. Store this `shapely_polygon`.
    7.  **Verification:** Run the script for a single cluster. Does it render correctly? Is the label alignment right? Are leader lines pointing correctly? Print or visualize the calculated `shapely_polygon`'s coordinates to verify it covers the elements.

---

**Phase 3.B: Placement Heuristics & Collision Detection**

*   **Goal:** Implement the logic to determine an *initial* target position for a cluster's label box based on heuristics, and the function to check if its bounding polygon intersects with previously placed ones.
*   **Checkpoints:**
    1.  Heuristic function calculates a plausible initial `(target_x, target_y)` based on cluster centroid location.
    2.  Collision check function correctly uses Shapely `intersects` against a list of stored polygons.
    3.  Can manually test placement & collision for two distinct clusters.

*   **To-Do List:**
    1.  **Placement Heuristic Function:**
        *   Create `def get_initial_label_box_position(cluster_centroid_x, cluster_centroid_y): ...`
        *   Implement rules based on centroid location (e.g., if north Florida, target NW offshore; if SE Florida, target E offshore). Return `(target_x, target_y)`.
    2.  **Collision Check Function:**
        *   Create `def check_collision(candidate_polygon, placed_polygons_list): ...`
        *   Inside, loop through `placed_polygons_list`. If `candidate_polygon.intersects(existing_polygon)` returns `True`, the function returns `True`. Otherwise, returns `False`.
    3.  **Integrate & Test:**
        *   Modify the main script logic from 3.A.
        *   Process two different, known clusters sequentially (e.g., Cluster 0 then Cluster 1).
        *   For Cluster 0: Calculate its initial position, calculate its bounding polygon, render it, store its polygon in `placed_polygons`.
        *   For Cluster 1: Calculate its initial position using the heuristic. Calculate its *candidate* bounding polygon. Call `check_collision` against the polygon(s) in `placed_polygons`. Print the result ("Collision detected" or "No collision"). Render Cluster 1 at its initial position regardless for now.

---

**Phase 3.C: Iterative Placement Loop & Basic Repositioning**

*   **Goal:** Combine the pieces into a loop that processes all clusters, attempts placement, checks collisions, and implements a *very simple* repositioning strategy if needed.
*   **Checkpoints:**
    1.  Main loop iterates through all identified clusters in the chosen order.
    2.  Collision checking happens for each cluster after the first.
    3.  A basic repositioning attempt (e.g., move slightly further offshore) is triggered on collision.
    4.  Final map shows all clusters rendered, with labels potentially overlapping if repositioning failed, but attempts were made.

*   **To-Do List:**
    1.  **Main Loop Structure:** Refactor the script to loop through all cluster IDs in the desired order. Maintain the `placed_polygons` list across iterations.
    2.  **Integrate Placement & Collision:** Inside the loop for cluster `C`:
        *   Call `get_initial_label_box_position`.
        *   Calculate `candidate_poly` at this initial position.
        *   Call `check_collision`.
    3.  **Implement Basic Repositioning:**
        *   If `check_collision` returns `True`:
            *   Define `num_attempts = 0`, `MAX_ATTEMPTS = 5`.
            *   Start a `while collision and num_attempts < MAX_ATTEMPTS:` loop.
            *   Inside the `while`: Increment `num_attempts`. Calculate a *new* trial position (e.g., `trial_x = current_target_x + offset_step_x`, `trial_y = current_target_y + offset_step_y` based on the heuristic direction). Recalculate `candidate_poly` at the `trial_x, trial_y`. Re-run `check_collision`. Update `current_target_x/y` for the next attempt.
            *   After the `while` loop, set `final_x, final_y` to the last successful or last attempted position.
        *   If `check_collision` was initially `False`, set `final_x, final_y` to the initial target position.
    4.  **Store & Render:** Calculate the final bounding polygon based on `final_x, final_y`. Add it to `placed_polygons`. Render the cluster's elements using `final_x, final_y` for the label box placement.
    5.  **Run Full Test:** Execute the script for the full Florida dataset. Observe the output map. Check logs/print statements for collision/repositioning attempts.

---

**Phase 3.D: Algorithmic Evaluation & Refinement**

*   **Goal:** Assess the quality of the map produced by the algorithm and identify areas for improvement in the heuristics or collision handling.
*   **Checkpoints:**
    1.  Visual comparison against baseline and target shows improvement/tradeoffs.
    2.  Specific failure modes (e.g., unavoidable overlaps, poor heuristic choices) are identified.
    3.  Potential refinements to heuristics or repositioning strategy are documented.

*   **To-Do List:**
    1.  **Visual Assessment:** Compare the final map from 3.C to the baseline (Phase 0) and the target inspiration image. Is the layout significantly cleaner? Are labels readable? Does the structure make sense? Where does it fail?
    2.  **Analyze Overlaps:** Identify which cluster polygons still overlap significantly. Why did the repositioning fail for them? (Ran out of attempts? No clear space available? Poor initial heuristic?)
    3.  **Review Heuristics:** Does the initial placement logic (`get_initial_label_box_position`) generally work well, or does it often place boxes in problematic areas?
    4.  **Refinement Ideas:** Brainstorm improvements:
        *   More sophisticated repositioning (e.g., smarter search pattern, allowing slight rotation?).
        *   Better initial placement heuristics (consider proximity to *other cluster centroids*?).
        *   Dynamic label box sizing or allowing multi-column layouts within a box?
        *   More accurate bounding polygons (convex hull)?
        *   Prioritizing placement for more significant clusters?
    5.  **Documentation:** Summarize the results of the algorithmic approach – its strengths, weaknesses, and potential next steps for refinement based on the evaluation. Decide if this approach is promising enough to pursue further refinement over returning to the LLM approach.

This phased plan provides a structured way to build the deterministic layout algorithm, focusing on getting the geometry right first, then handling interactions, and finally evaluating the outcome.