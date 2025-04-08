## **Phase 3.1: Refactor Plotting Script for `adjustText` Focus**

*   **Goal:** Create a new baseline plotting script that uses `adjustText` as the primary layout engine, removing complex heuristics and simplifying the agent's future task.
*   **Checkpoints:**
    1.  Script successfully removes heuristic positioning and callouts.
    2.  Script uses `adjustText` effectively for initial layout.
    3.  Script runs manually for a few iterations, producing visually different (even if imperfect) layouts relying on `adjustText`.

*   **To-Do List:**
    1.  **Copy Script:** Duplicate `src/plotting_script_phase3_incremental.py` to `src/plotting_script_phase3_adjustText_focused.py`. This will be the new script the agent modifies.
    2.  **Remove Heuristics:**
        *   Delete the entire `get_cluster_offset` function definition.
        *   Remove the lines within the cluster processing loop that call `get_cluster_offset`.
        *   Remove the calculation and usage of `label_x`, `label_y` based on offsets.
    3.  **Remove Callout Boxes:**
        *   Delete the code block that creates `plt.Rectangle` (the white background boxes).
    4.  **Simplify Initial Text Placement:**
        *   Inside the loop `for j, (_, row) in enumerate(cluster_df.iterrows()):` (or the equivalent loop iterating through points in displayed clusters):
            *   Modify the `ax.text(...)` call:
                *   Set the initial position to `(row['longitude'], row['latitude'])` or slightly offset like `(row['longitude'] + 0.01, row['latitude'] + 0.01)`.
                *   Remove any `ha` (horizontal alignment) or `va` (vertical alignment) arguments that were dependent on the old offsets; let `adjustText` handle alignment or use Matplotlib defaults initially.
                *   Remove the `bbox` argument for single points for now (can be added back later if desired).
            *   Ensure this simplified `ax.text` object is still appended to the `all_texts` list.
    5.  **Consolidate Text Creation:** Remove the `if num_points > 1:` / `else:` logic that handled text differently for single vs. multi-point clusters. Apply the simplified `ax.text` logic (from step 4) to *all* points being plotted in the current iteration.
    6.  **Remove Old Leader Lines:** Delete the code creating `ConnectionPatch` instances *before* the `adjust_text` call.
    7.  **Configure `adjustText`:**
        *   Locate the `adjust_text(...)` call.
        *   Set `autoalign=True` (experimentally, to let it control alignment).
        *   Ensure `arrowprops=dict(arrowstyle='-', color='grey', lw=0.5)` (or similar) is present, so it draws leader lines from the *final adjusted position* back towards the original point coordinates (or the slightly offset initial text position).
        *   Review/adjust `force_points`, `force_text`, `expand_points`, `expand_text`. Reasonable starting values might be `force_text=(0.5, 0.5)`, `force_points=(0.1, 0.1)`.
        *   Remove the `only_move` argument initially, allowing `adjustText` more freedom.
    8.  **Manual Test & Refine:**
        *   Run the new script manually from the command line for the first few iterations:
            ```bash
            python src/plotting_script_phase3_adjustText_focused.py 0
            python src/plotting_script_phase3_adjustText_focused.py 1
            python src/plotting_script_phase3_adjustText_focused.py 2
            ```
        *   Examine the output images (`output/phase3/images/florida_iter_*.png`). Does `adjustText` seem to be working? Are labels moving? Are leader lines present? Tweak `adjustText` parameters (step 7) if needed to get a reasonable (though likely imperfect) starting layout.
    9.  **Save Final Version:** Once satisfied with the manual test, save this version as the definitive starting point for the agent loop (e.g., overwrite the copy in `src/` or note this version).

---

## **Phase 3.2: Adapt Agent Loop Script for Diff Handling**

*   **Goal:** Modify the orchestrator script to request, receive, parse, and apply code diffs, instead of replacing the entire file.
*   **Checkpoints:**
    1.  Script correctly requests a diff from the LLM (verified in prompt definition - Phase 3.3).
    2.  Script attempts to extract diff content from the LLM response.
    3.  Script includes logic to *apply* the diff to the current code state.
    4.  Basic error handling for diff application is present.

*   **To-Do List:**
    1.  **Copy Script:** Duplicate `src/agent_loop_phase3_incremental.py` to `src/agent_loop_phase3_diffs.py`.
    2.  **Import `difflib`:** Add `import difflib` at the top.
    3.  **Modify LLM Output Extraction:**
        *   In the `extract_code_from_response` function (or directly in the loop), change the logic to look for diff markers (e.g., ```diff ... ```) instead of Python markers.
        *   Return the *diff string*, not the full code. Rename the function to `extract_diff_from_response` if desired. Handle cases where the LLM might not provide the correct format (return None or empty string).
    4.  **Implement Diff Application Logic:**
        *   Inside the main loop, *after* receiving the response and extracting the `diff_text`:
            *   Store the `current_code` string as `previous_code` (for the *next* iteration's history).
            *   **Attempt to Apply Diff:**
                *   Use `difflib` or simple string manipulation. A potentially robust method (though complex) is to parse the unified diff format.
                *   **Simpler (Recommended) Approach:** Use `patch` utility if available, or Python libraries like `patch` (`pip install patch`) or `python-patch` (`pip install python-patch`). Example using `patch`:
                    ```python
                    import patch
                    # ... inside loop ...
                    diff_text = extract_diff_from_response(response_text)
                    if diff_text:
                        try:
                            # Ensure diff_text is bytes if the library requires it
                            patch_set = patch.fromstring(diff_text.encode('utf-8'))
                            # Apply patch to previous_code (which is the current code before modification)
                            patched_bytes = patch_set.apply(previous_code.encode('utf-8'))
                            if patched_bytes:
                                current_code = patched_bytes.decode('utf-8') # This is the new code
                                log.write("Successfully applied diff.\n")
                            else:
                                log.write("Failed to apply diff (patch library returned False).\n")
                                # Keep previous code: current_code remains previous_code
                        except Exception as e:
                            log.write(f"Error applying diff: {e}\n")
                            # Keep previous code: current_code remains previous_code
                    else:
                        log.write("No valid diff extracted from response. Using previous code.\n")
                        # Keep previous code: current_code remains previous_code
                    ```
            *   Ensure `current_code` variable holds the *result* of the patching (or the old code if patching failed).
    5.  **Update State/Logging:**
        *   Modify the logging to save the received `diff_text` and whether the patch application succeeded or failed.
        *   Ensure `previous_llm_modification` now stores the `diff_text` for the next iteration's context.
    6.  **Code Saving:** Modify the logic that saves the code for the next iteration (`CODE_DIR / f"plotting_script_phase3_iter_{i+1}.py"`) to write the *newly patched* `current_code`.

---

## **Phase 3.3: Revise Prompt & Small Test Run**

*   **Goal:** Define the new prompt for the LLM focusing on diffs and overrides, and run a brief test to ensure the diff request/apply mechanism works.
*   **Checkpoints:**
    1.  New prompt correctly instructs the LLM based on the refactored plotting script and asks for a diff.
    2.  Short loop run executes, attempts diff application, and logs results.
    3.  LLM attempts to provide diffs targeting label overrides.

*   **To-Do List:**
    1.  **Set Starting Script:** Ensure `agent_loop_phase3_diffs.py` initializes using the refactored plotting script from Phase 3.1 (e.g., `src/plotting_script_phase3_adjustText_focused.py`).
    2.  **Implement New Prompt:**
        *   In `agent_loop_phase3_diffs.py`, modify the `create_prompt` function (or inline prompt creation).
        *   Use the following structure (adjust placeholders):
            ```text
            You are an AI agent improving a Python script (`current_code`) that generates a map of Florida hurricane landfalls using Matplotlib/Cartopy and the `adjustText` library. The script plots points incrementally; this is iteration N={N}. `adjustText` handles the main layout, but sometimes fails.

            **Context:**
            *   **Current Iteration Number:** N = {N}
            *   **Current Plotting Script (`current_code`):**
                ```python
                # [Content of current_code string]
                ```
            *   **Image from Previous Script (`previous_image`):** [Image data for previous_image_path, if N>0]
            *   **Diff applied in Previous Step (`previous_llm_modification`):**
                ```diff
                # [Content of previous_llm_modification string (the diff), if N>0]
                ```
            *   **Image Generated by Current Script (`current_image`):** [Image data for current_image_path]

            **Task:**
            1.  Analyze the `current_image`, focusing on the layout generated primarily by `adjustText`. Identify the ONE WORST remaining overlap or label placement issue, especially concerning the newly added cluster or interactions between clusters.
            2.  Generate a code diff in standard `diff -u` format to modify the `current_code`.
            3.  The **primary goal** of the diff should be to add a *new* specific `ax.text(x, y, "Label (YEAR)", ...)` call *after* the main `adjust_text(...)` call. This new call manually sets the precise coordinates (x, y) for the single problematic label you identified, effectively overriding the position `adjustText` chose for it. Choose coordinates that resolve the issue identified in step 1.
            4.  Do NOT modify the main `adjust_text(...)` call or its parameters in this diff unless absolutely necessary and you explain why in a comment within the diff context. Do not modify data loading or loop logic.
            5.  Output **only the diff block**, correctly formatted and enclosed in markdown triple backticks (```diff ... ```).

            **Self-Correction Hint:** Review the `previous_image` and `previous_diff`. If the last change didn't improve the specific issue it targeted, try fixing a *different* problematic label in this iteration.
            ```
    3.  **Short Test Run:**
        *   Execute `agent_loop_phase3_diffs.py` with a low iteration count (`--iterations 3` or `--iterations 5`).
        *   Monitor the logs closely: Is the prompt correct? Is the LLM returning something that looks like a diff? Is the diff application logic running (and succeeding/failing as expected)? Are the output images changing?
        *   Manually inspect the generated code versions (`output/phase3/code/plotting_script_phase3_iter_*.py`). Do they show evidence of new `ax.text` calls being added after `adjustText`?

---

## **Phase 3.4: Run Scaled Experiment (Phase 3 Retry)**

*   **Goal:** Execute the refined agentic loop on the full Florida subset for multiple iterations to gather data for the final evaluation.
*   **Checkpoints:**
    1.  Loop runs stably for the target number of iterations or until budget is hit.
    2.  Logs capture sufficient detail for Phase 4 analysis.
    3.  Sequence of output images is generated for visual assessment.

*   **To-Do List:**
    1.  **Prepare:** Ensure the `florida_landfalls.csv` data is ready. Confirm the starting script is the correct refactored one from Phase 3.1. Double-check budget tracking/limits in `agent_loop_phase3_diffs.py`.
    2.  **Execute:** Run the main experiment:
        ```bash
        # Example: Start from iteration 0, run for 20 iterations
        python src/agent_loop_phase3_diffs.py --iterations 20 --start 0
        ```
    3.  **Monitor:** Keep an eye on:
        *   Console output for progress and errors.
        *   Log file growth and content (especially diff application success/failure).
        *   Output images being generated in `output/phase3/images/`.
        *   Estimated cost accumulation (if implemented). Stop manually if budget is exceeded unexpectedly.
    4.  **Completion:** Let the loop finish the specified iterations or hit the budget limit.

---

This detailed breakdown provides checkpoints and specific implementation steps to refactor Phase 3. Once Phase 3.4 is complete, you'll have the necessary artifacts (final image sequence, logs) to perform the evaluation in Phase 4.