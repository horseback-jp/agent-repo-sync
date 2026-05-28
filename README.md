# GECX Agent Repository Synchronizer & Pruner CLI

An enterprise-grade, zero-dependency **DevOps garbage collection and synchronization tool** designed to align live Google Cloud Customer Engagement Suite (GECX) / Dialogflow CX application configurations 100% with your Git repository.

---

## 🏛️ Why this tool is necessary: The "Additive Deployment Gap"

Standard GECX CLI tools (like `cxas push`) are strictly **additive deployment utilities**. When you merge a Pull Request that deletes old agents, configurations, tools, or toolsets from your repository, GECX will update the active code, but **it will NOT automatically delete or prune orphaned resources from Google Cloud.**

These obsolete files remain active on the cloud console server as orphans, causing instruction drift, permission mismatches, and linter errors. 

This Synchronizer CLI bridges the gap:
1. **Automated CI Audit**: Scans GECX post-deployment, compares it to your repository folders, and warning-flags any leftover orphans in a highly visible Markdown dashboard.
2. **Interactive Local Actuator**: Allows you to selectively review and prune orphans one-by-one inside your terminal, preserving 100% developer control.

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
*Ensure your active ADC credentials have standard IAM reader/writer and toolset delete permissions in your target GCP project.*

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
* **Output**: Shows the Object Type (Tool/Toolset), Display Name, System ID, and Git Status of all orphans.

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
[AUDIT] Detected 2 orphaned assets active on GCP GECX:
-----------------------------------------------------
 [1] Tool ➔ Display Name: cache_anonymized_ledger | ID: cache_anonymized_ledger
 [2] Toolset ➔ Display Name: lloyds_bank_toolset | ID: lloyds_bank_toolset

Choose an operation to proceed:
 [A] Delete ALL orphaned assets from Google Cloud
 [S] Selectively review and delete assets ONE-BY-ONE
 [N] Leave all and Exit

Select option (A/S/N) [N]: 
```

* **Option `A` (All)**: Instantly deletes all orphaned assets from Google Cloud.
* **Option `S` (Select)**: Iterates through each orphan individually, prompting you for confirmation:
  ```
  ➔ [1/2] Delete Tool 'cache_anonymized_ledger' (ID: cache_anonymized_ledger)? (y/N): y
    Successfully deleted.
  ```
* **Option `N` (None)**: Exits safely without modifying GCP.

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
