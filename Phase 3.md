# **Phase 3: Incremental Scaling & Strategy Test**. This is where the core hypothesis is tested under more realistic conditions, integrating the chosen strategies and managing the budget.

**Goal:** Evaluate if the agentic loop (using Gemini 2.0 Flash Thinking, with history, refining `adjustText` output, processing points incrementally) can manage a denser region (Florida) and demonstrably improve layout quality over multiple iterations with minimal manual intervention.

**Estimated Cost:** Highest cost phase (~$30-50 for ~15-20 iterations, depending on token usage per iteration). Moderate developer time to enhance the loop script and monitor progress.

**Key Assumptions for Phase 3:**

1.  **Flash Model Capability:** We assume Gemini 2.0 Flash Thinking possesses sufficient visual analysis and Python code generation capabilities to understand the `adjustText` output and make meaningful modifications to the Matplotlib/Cartopy code.
2.  **`adjustText` Effectiveness:** We assume `adjustText` provides a somewhat reasonable baseline layout, meaning the agent's task is primarily *refinement* (fixing remaining collisions or awkward placements) rather than full layout generation from scratch.
3.  **Incremental Strategy Benefit:** We assume plotting points incrementally helps the agent (and potentially `adjustText`) by reducing the complexity it needs to handle in any single iteration.
4.  **Code Replacement Sufficiency:** Continuing the simplification from Phase 2, we assume the agent outputting the *entire modified script file* each time is sufficient and manageable, avoiding the complexity of true diff parsing/application.
5.  **Simple Override Feasibility:** We assume the primary successful strategy for the agent will be to manually override specific label positions (by adding/modifying `ax.text` calls *after* `adjustText`) for points that `adjustText` fails to place well, and that the LLM can generate code to do this. Tweaking `adjustText` parameters via code modification is a less certain, secondary possibility.
6.  **Error Recovery:** We assume basic error handling (e.g., the loop continues even if one iteration's generated code fails to run) is sufficient, without needing complex automatic recovery logic. Engineer oversight can manually fix if needed.

**Steps & Implementation Details:**

1.  **Data Preparation:**
    *   Filter the `us_hurricane_landfalls_cat1_5.csv` (from Phase 0) to include only landfalls within a bounding box roughly corresponding to Florida and its immediate coastal waters.
    *   Save this subset as `florida_landfalls.csv`.

2.  **Enhanced Plotting Script (`plotting_script_phase3.py`):**
    *   Start by copying/modifying the script used in Phase 2.
    *   **Load Full Data:** Load the *entire* `florida_landfalls.csv` at the start.
    *   **Argument Parsing:** Accept the current iteration number `N` as a command-line argument.
    *   **Incremental Data Selection:**
        *   Define `BATCH_SIZE` (e.g., 10 or 15).
        *   Calculate the number of points to plot for this iteration: `num_points = (N + 1) * BATCH_SIZE`. Ensure it doesn't exceed the total number of points.
        *   Select the first `num_points` from the loaded DataFrame.
    *   **Plotting with `adjustText`:**
        *   Plot the selected landfall points (`ax.scatter`).
        *   Create a list `texts = []`.
        *   Iterate through the *selected* data subset:
            *   Append `ax.text(lon, lat, f"{name} ({year})", ...)` to the `texts` list. **Crucially, do not draw them immediately.**
        *   Call `adjust_text(texts, ax=ax, arrowprops=dict(arrowstyle='-', color='grey', lw=0.5))` (or similar default `adjustText` settings). This will handle the initial layout attempt.
    *   **Save Output:** Save the image with an iteration-specific name, e.g., `output_florida_iter_{N}.png`.

3.  **Enhanced Loop Orchestrator (`agent_loop_phase3.py`):**
    *   Adapt the script from Phase 2.
    *   **Configuration:**
        *   Set `MAX_ITERATIONS` (e.g., 20 or 30).
        *   Set `BATCH_SIZE` (matching the plotting script).
        *   Set `BUDGET_THRESHOLD` (e.g., $95).
        *   Specify the path to the initial plotting script code (`plotting_script_phase3_v0.py`).
        *   Initialize `total_estimated_cost = 0.0`.
    *   **Loop (N=0 to MAX_ITERATIONS-1):**
        *   **a. Cost Estimation/Check:** (Optional but Recommended) Before the API call, estimate the potential cost based on input token count (code size, image data, prompt length). If `total_estimated_cost + estimated_call_cost > BUDGET_THRESHOLD`, break the loop.
        *   **b. Save & Execute:** Save `current_code` to `temp_plotter_p3.py`. Run it using `subprocess.run(['python', 'temp_plotter_p3.py', str(N)])`. Check return code; log errors but potentially continue.
        *   **c. Prepare LLM Input:** Assemble the prompt (see Step 4) with current code, iteration number `N`, paths to `output_florida_iter_{N}.png` and `output_florida_iter_{N-1}.png` (if N>0), and the previous LLM modification string.
        *   **d. Call LLM API (Flash Model):** Send the request.
        *   **e. Cost Update:** (Optional) Add the actual cost of the completed API call (if available from API response/headers) to `total_estimated_cost`.
        *   **f. Process Output:** Extract the full Python code block. Basic validation.
        *   **g. Update State & Log:** Update `current_code`, `previous_image_path`, `previous_llm_modification`. Log everything for this iteration (N, prompt, full response, cost estimate/actual, image path, success/failure of script execution).

4.  **Refined LLM Prompt (for Phase 3):**
    *   Needs to guide the agent to work with the incremental approach and `adjustText`.
    *   Example Prompt Structure:
        ```text
        You are an AI agent improving a Python script (`current_code`) that generates a map of Florida hurricane landfalls using Matplotlib/Cartopy and the `adjustText` library. The script plots points incrementally; this is iteration N={N}, plotting the first {(N+1)*BATCH_SIZE} points. `adjustText` has already been applied in the `current_code`.

        **Context:**
        *   **Current Iteration Number:** N = {N}
        *   **Current Plotting Script (`current_code`):**
            ```python
            # [Content of current_code string]
            ```
        *   **Image from Previous Script (`previous_image`):** [Image data for previous_image_path, if N>0]
        *   **Modification made by LLM in Previous Step (`previous_llm_modification`):**
            ```
            # [Content of previous_llm_modification string, if N>0]
            ```
        *   **Image Generated by Current Script (`current_image`):** [Image data for current_image_path]

        **Task:**
        1.  Analyze the `current_image`. Focus on the layout of the {(N+1)*BATCH_SIZE} points plotted so far. Remember `adjustText` was used. Identify ONE significant remaining layout issue (e.g., overlapping labels, label far from point, label obscuring points). Compare with `previous_image` if available.
        2.  Modify the `current_code` to address the issue you identified. The most likely useful modification is to *manually add or adjust* an `ax.text(...)` call *after* the `adjust_text(...)` line for the specific problematic label, overriding its position. Less likely, you might try adjusting `adjust_text` arguments if you see a clear parameter change needed. Do NOT change the data loading or which points are selected for this iteration.
        3.  Output the *entire, complete, modified Python script*. Ensure it remains runnable and includes the `adjustText` call. Enclose the code in markdown triple backticks (```python ... ```).

        **Constraint:** Improve clarity for the points plotted *so far*. Only generate the full Python code.
        ```

5.  **Execution and Monitoring:**
    *   Run `agent_loop_phase3.py`.
    *   Closely monitor the console output, generated images sequence (`output_florida_iter_*.png`), and the log file.
    *   Keep an eye on estimated/actual costs if implemented, stopping if the budget is reached.

6.  **Preliminary Evaluation (Post-Run):**
    *   Review the full sequence of generated images. Is there a visible trend of improvement in the layout as N increases? Does it stabilize or degrade later?
    *   Check the logs: Did the agent consistently generate runnable code? What kinds of modifications did it attempt (override positions vs. adjusting `adjustText` params)? Did it seem to get stuck on specific issues?
    *   Compare the final image (`output_florida_iter_{MAX_ITERATIONS-1}.png`) qualitatively against the corresponding region in the original baseline (`baseline_us_cat1_5.png`).

**Expected Outputs:**

1.  Filtered data file (`florida_landfalls.csv`).
2.  An initial plotting script using `adjustText` (`plotting_script_phase3_v0.py`).
3.  The enhanced loop orchestrator script (`agent_loop_phase3.py`).
4.  A sequence of output images for the Florida region (`output_florida_iter_0.png` to `output_florida_iter_{N_final}.png`).
5.  A detailed log file capturing the state, prompts, LLM responses, and costs for each iteration.
6.  An initial engineer assessment of the loop's performance: Did it run stably? Was there evidence of layout improvement? Did it stay within budget?

This phase directly tackles the core complexity and provides the primary data needed to evaluate the hypothesis in Phase 4.