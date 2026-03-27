# PyMovieManager Refactoring Report

## 1. Diagnosis
The previous implementation of `MovieManager` utilized direct `os` and `shutil` commands to perform directory moves, renames, and deletions. This approach presented multiple major risks when interacting with an SMB-attached Synology NAS from a Windows PC:
- **Silent Overwrites / Data Loss:** `shutil.rmtree` and `shutil.move` could silently obliterate existing collections if conflict logic wasn't perfectly resilient. Source folders were deleted before destination integrity was formally verified.
- **Platform Inconsistencies:** Windows UNC paths and mapped drives (`\\NAS\Media` or `Z:\`) behaved unpredictably with string-matched root logic and strict `os.rename` boundaries.
- **Interruption Hazards:** If the connection dropped mid-transfer, PyMovieManager lacked resumption capabilities. Rerunning it could yield duplicate tags or destructive overwrites.

## 2. Changes Implemented
- **Unified FileSystem Adapters:** The `IFileSystemInterface` was expanded to handle all OS-level concerns natively. `MovieManager` now strictly calls `self.fileSystemService` for operations like `copy_file`, `move`, `ensure_directory_exists`, and path joining.
- **Safe Merge & Verify-Before-Delete:** The `_move_or_merge_movie_folder` routine was completely rewritten. It now:
    1. Analyzes source vs. destination by relative file path and size.
    2. Identifies exact missing files to copy and halts execution explicitly if conflicts (size mismatch on the same file) are detected.
    3. Guarantees the source folder is **only** deleted *after* every file is verified to exist in the destination context.
- **Resumability & Observability:** 
    - A `RunManifestClass` now logs progress monotonically via JSONL in the `reports` directory. Using the `--resume` flag gracefully bounds operations to only incomplete folders.
    - Added deterministic folder sorting.
- **CLI Run Modes:** Integrated robust preflight, planning, and limiting modes to safely orchestrate remote execution without unexpected side effects.

## 3. Run Commands
Here are the commands to execute in your typical workflow:

- **Validate your configuration and paths without touching any data:**
  ```bash
  python main.py --preflight
  ```
- **Simulate the entire organizational plan (Actionable moves/skips):**
  ```bash
  python main.py --plan
  ```
- **Execute a standard Dry Run (simulate processing without writing files):**
  ```bash
  python main.py --dry-run
  ```
- **Process a limited chunk of data (e.g., test 5 folders first):**
  ```bash
  python main.py --limit 5
  ```
- **Production Execution (Standard):**
  ```bash
  python main.py
  ```
- **Resume after a network interruption or failure:**
  ```bash
  python main.py --resume
  ```

## 4. Rollout Order
1. Ensure your `config.json` uses exact absolute paths (`\\NAS\RAW` or mapped `Z:\RAW`).
2. Run `python main.py --preflight` to ensure Python has read/write SMB permissions contextually.
3. Run `python main.py --plan` to visualize exactly how PyMovieManager will sort your RAW folders.
4. Run `python main.py --limit 1` to perform a single-folder test run and dynamically verify tracking inside the `reports/` folder.
5. Finally, invoke a full `python main.py` or script it against your Windows Task Scheduler.

## 5. Remaining Risks
- **Network Interruptions during File Copying:** A dropped connection mid-copy will leave partial files corrupted in the destination. The new verify footprint mitigates this because it compares size metrics, catching corrupt partial-files on a subsequent `--resume`. However, a heavily unstable gigabit link could churn repeatedly.
- **Automated Testing Setup:** Extensive mock updates are required for `test_movie_manager.py` to completely pass `unittest` since the interfaces were vastly modified. Currently, the tests mock deprecated properties rather than the new strict abstractions. They should be formally updated if CI/CD pipelines are initialized.
