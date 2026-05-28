# GECX Agent Repository Synchronizer & Pruner CLI

An enterprise-grade, zero-dependency **DevOps garbage collection and synchronization tool** designed to align live Google Cloud Customer Engagement Suite (GECX) / Dialogflow CX application configurations 100% with your Git repository.

---

## 🏛️ Why this tool is necessary: The "Additive Deployment Gap"

Standard GECX CLI tools (like `cxas push`) are strictly **additive deployment utilities**. When you merge a Pull Request that deletes old agents, configurations, tools, or toolsets from your repository, GECX will update the active code, but **it will NOT automatically delete or prune orphaned resources from Google Cloud.**

These obsolete files remain active on the GECX cloud console server as orphans, causing instruction drift, permission mismatches, and linter errors. 

This Synchronizer CLI bridges the gap across three first-class GECX objects:
1. **Tools & Toolsets**: Identifies local folder deletion drift inside `tools/` and `toolsets/`.
2. **Sub-Agents**: Audits GECX Playbooks (LLM, DFCX, or workflow agents) inside the `agents/` directory (excluding GECX mandatory entry points like `root_agent`).
3. **Variables**: Detects session variables deleted from the local `app.json` declarations.

---

## 🚦 Prerequisites & Installation

### 1. Authentication & Authorization
The CLI uses Google's standard **Application Default Credentials (ADC)** under the hood. 
1. Ensure you have the Google Cloud SDK (`gcloud`) installed on your machine.
2. Authenticate your terminal:
   ```bash
   gcloud auth login
   gcloud auth application-default login
   ```
*Ensure your active ADC credentials have standard IAM reader/writer and delete permissions in your target GCP project.*

### 2. Local Installation
Clone the repository and install the GECX Scrapi SDK dependency inside your python environment:
```bash
pip install -r requirements.txt
```

---

## 💻 Terminal CLI Usage

The script accepts three dynamic CLI arguments:
* `--app-name`: The target GECX App Resource path on GCP (e.g., `projects/<PROJECT_ID>/locations/<REGION>/apps/<APP_ID>`).
* `--app-dir`: The path to your local Git repository directory containing your `app.json` orchestrator file.
* `--mode`: Execution mode: `audit` (dry-run report) or `prune` (interactive deletion).

### Mode 1: Dry-Run Audit (`--mode=audit`)
To scan for drift and print a descriptive Markdown warning table of orphans in your terminal without modifying Google Cloud:
```bash
python prune_gecx_assets.py \
  --mode=audit \
  --app-name=projects/<PROJECT_ID>/locations/<LOCATION>/apps/<APP_ID> \
  --app-dir=<LOCAL_APP_FOLDER>
```
* **Output**: Consolidates and warning-flags Tools, Sub-Agents, and Variables inside a rich descriptive Markdown table detailing Object Type, Display Name, and System ID.

### Mode 2: Interactive Pruning (`--mode=prune`)
To clean up the live GCP GECX server:
```bash
python prune_gecx_assets.py \
  --mode=prune \
  --app-name=projects/<PROJECT_ID>/locations/<LOCATION>/apps/<APP_ID> \
  --app-dir=<LOCAL_APP_FOLDER>
```

The CLI will display the audit table in your terminal and prompt you with three clean operational choices:
```
[AUDIT] Detected 3 orphaned assets active on GCP GECX:
-----------------------------------------------------
 [1] Tool ➔ Display Name: cache_anonymized_ledger | ID: cache_anonymized_ledger
 [2] Sub-Agent ➔ Display Name: wealth_advisor | ID: wealth_advisor
 [3] Variable ➔ Variable Name: legacy_balance_cache

Choose an operation to proceed:
 [A] Delete ALL orphaned assets from Google Cloud
 [S] Selectively review and delete assets ONE-BY-ONE
 [N] Leave all and Exit

Select option (A/S/N) [N]: 
```

* **Option `A` (All)**: Instantly deletes all orphaned assets from Google Cloud.
* **Option `S` (Select)**: Iterates through each orphan individually, prompting you for confirmation:
  `➔ [1/3] Delete Tool 'cache_anonymized_ledger' (ID: cache_anonymized_ledger)? (y/N): `
* **Option `N` (None)**: Exits safely without modifying GCP.

---

## 🛡️ Safety & Transaction Integrity Gates

To protect your live production systems, the CLI implements three layers of transaction-safe gates:

1. **Selective Double-Confirmation (`S` option)**: Reviews each asset one-by-one. Deletions require typing an explicit `y` / `yes`, ensuring you have complete veto power.
2. **Graceful Dependency Protection**: GECX prohibits deleting sub-agents that are still referenced inside parent routing rules (e.g., `root_agent` transitions). The CLI gracefully catches these exceptions, skips the deletion safely (preventing crashes), and prints clear advisory guidelines:
   ```
   [DEPENDENCY WARNING] Skipping deletion of Sub-Agent 'wealth_advisor'.
     Reason: The agent cannot be deleted because it is the child agent of other agents.
     Action Required: Please remove any routing rules or transitions pointing to 'wealth_advisor' in GECX, and re-run.
   ```
3. **Variable Batch-Transaction Safety**: Modifying GECX global session variables requires updating the App config metadata. To prevent multiple slow network calls, the CLI **stages variable removals in memory** during the loop. The final push is committed to Google Cloud in a single transaction **only when the loop runs fully to completion.** Aborting the script early (e.g., pressing `Ctrl+C` to exit) safely discards all staged variable deletions, protecting your environment from partial updates.

---

## 🤖 CI/CD Pipeline Integration (GitHub Actions)

We have provided a clean, standardized reference workflow template inside this repository:
📂 **`/examples/github_actions_reference.yaml`**

### How to Configure:
1. Copy the contents of `/examples/github_actions_reference.yaml` into your own repository's `.github/workflows/deploy.yml` file.
2. Replace the `<PLACEHOLDERS>` with your specific GCP Project ID, Project Number, and local folder directory.
3. Push to GitHub.
4. **The Job Summary Dashboard**: On every deploy, the pipeline will automatically run the script in audit mode. GitHub Actions will render a beautiful, rich Markdown table directly under the Actions **Job Summary** tab showing all orphans!

---

## 📄 License
Copyright 2026 Google LLC. Licensed under the Apache License, Version 2.0.
