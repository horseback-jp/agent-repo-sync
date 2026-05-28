# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
prune_gecx_assets — Generic GECX Server Garbage Collection & Audit CLI

Enables:
  - --mode=audit: Dry-run scan that writes descriptive Markdown tables of orphans
                 (Object Type, Display Name, System ID) to GitHub step summaries.
  - --mode=prune: Interactive terminal actuator offering selective All, None,
                 or One-by-One manual deletions.
"""

import argparse
import os
import sys
from cxas_scrapi.core.tools import Tools


def fetch_local_and_live_assets(app_name, app_dir):
    """Queries GECX Cloud server and scans local repository folders to find orphaned tools.

    Args:
        app_name: Deployed GECX App resource name (projects/.../apps/...).
        app_dir: Path to the local application folder containing app.json.
    """
    t_client = Tools(app_name=app_name)

    # 1. Resolve local Git workspace directories dynamically relative to app_dir
    local_tools_dir = os.path.abspath(os.path.join(app_dir, "tools"))
    local_toolsets_dir = os.path.abspath(os.path.join(app_dir, "toolsets"))

    local_tool_ids = set()
    if os.path.exists(local_tools_dir):
        for item in os.listdir(local_tools_dir):
            if os.path.isdir(os.path.join(local_tools_dir, item)):
                local_tool_ids.add(item)

    local_toolset_ids = set()
    if os.path.exists(local_toolsets_dir):
        for item in os.listdir(local_toolsets_dir):
            if os.path.isdir(os.path.join(local_toolsets_dir, item)):
                local_toolset_ids.add(item)

    # 2. Fetch live deployed tools from Google Cloud GECX
    print(f"Fetching active deployed assets from GECX server: {app_name}...")
    live_tools = t_client.list_tools()

    orphans = []
    for t in live_tools:
        system_id = t.name.split("/")[-1]
        is_toolset = "/toolsets/" in t.name

        if is_toolset:
            if system_id not in local_toolset_ids:
                orphans.append(
                    {
                        "type": "Toolset",
                        "display_name": t.display_name,
                        "system_id": system_id,
                        "resource_path": t.name,
                    }
                )
        else:
            if system_id not in local_tool_ids:
                orphans.append(
                    {
                        "type": "Tool",
                        "display_name": t.display_name,
                        "system_id": system_id,
                        "resource_path": t.name,
                    }
                )

    return t_client, orphans


def run_audit(orphans):
    print(f"\n[AUDIT COMPLETED] Found {len(orphans)} orphaned GECX assets on GCP.\n")

    if not orphans:
        print("All GECX assets are perfectly in sync with Git! 0 orphans found.")
        # Output a clean summary to GITHUB_STEP_SUMMARY if running in CI
        summary_env = os.getenv("GITHUB_STEP_SUMMARY")
        if summary_env:
            with open(summary_env, "a") as f:
                f.write("### ✅ GECX Server Alignment Audit Passed\n")
                f.write(
                    "All deployed GECX assets are perfectly aligned with Git! **0 orphans detected.**\n"
                )
        return

    # Format descriptive markdown table
    table = []
    table.append(
        "| Object Type | Display Name | System ID | Git Status | Action Recommended |"
    )
    table.append(
        "| :--- | :--- | :--- | :--- | :--- |"
    )

    for o in orphans:
        row = f"| `{o['type']}` | `{o['display_name']}` | `{o['system_id']}` | ❌ **DELETED** | Prune Recommended |"
        table.append(row)

    markdown_table = "\n".join(table)

    # Print to stdout for CLI review
    print("GECX Orphaned Assets Audit Summary:")
    print("-----------------------------------")
    for row in table:
        print(row)

    # Write directly to GITHUB_STEP_SUMMARY if running inside GitHub Actions
    summary_env = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_env:
        with open(summary_env, "a") as f:
            f.write("### 🚦 GECX Server Alignment Audit Warnings\n")
            f.write(
                f"The following **{len(orphans)} GECX cloud resources** have been deleted from the Git repository but still exist active on the live Google Cloud server. Pruning is recommended.\n\n"
            )
            f.write(markdown_table)
            f.write(
                "\n\n*To safely clean these up, open your VSCode terminal and execute: `python scratch/prune_gecx_assets.py --mode=prune`*\n"
            )
        print("\n[INFO] Successfully wrote audit table to GitHub Step Summary.")


def run_prune(t_client, orphans):
    if not orphans:
        print("\nNo orphaned assets found on the GECX server. Nothing to prune!")
        return

    print(f"\n[AUDIT] Detected {len(orphans)} orphaned assets active on GCP GECX:")
    print("-------------------------------------------------------------------")
    for idx, o in enumerate(orphans, 1):
        print(
            f" [{idx}] {o['type']} ➔ Display Name: {o['display_name']} | System ID: {o['system_id']}"
        )

    print("\nChoose an operation to proceed:")
    print(" [A] Delete ALL orphaned assets from Google Cloud")
    print(" [S] Selectively review and delete assets ONE-BY-ONE")
    print(" [N] Leave all and Exit")

    # Fetch user choice from interactive prompt
    try:
        choice = input("\nSelect option (A/S/N) [N]: ").strip().upper()
    except (KeyboardInterrupt, EOFError):
        print("\nExiting safely.")
        sys.exit(0)

    if choice == "A":
        print("\nPruning all orphaned assets...")
        for o in orphans:
            print(f"Deleting {o['type']} '{o['display_name']}' ({o['system_id']})...")
            t_client.delete_tool(o["resource_path"])
            print("Successfully deleted.")
        print("\nGECX Server Pruning completed successfully!")

    elif choice == "S":
        print("\nInitiating Selective One-by-One review...")
        for idx, o in enumerate(orphans, 1):
            try:
                confirm = (
                    input(
                        f"➔ [{idx}/{len(orphans)}] Delete {o['type']} '{o['display_name']}' (ID: {o['system_id']})? (y/N): "
                    )
                    .strip()
                    .lower()
                )
            except (KeyboardInterrupt, EOFError):
                print("\nInterrupted. Exiting safely.")
                sys.exit(0)

            if confirm in ["y", "yes"]:
                print("Deleting...")
                t_client.delete_tool(o["resource_path"])
                print("Successfully deleted.")
            else:
                print("Skipped.")
        print("\nSelective pruning completed.")

    else:
        print("\nOperation cancelled. No changes were made to Google Cloud GECX.")


def main():
    parser = argparse.ArgumentParser(description="GECX Server Pruner & Audit CLI")
    parser.add_argument(
        "--app-name",
        required=True,
        help="Deployed GECX App resource name ID (e.g. projects/<id>/locations/<region>/apps/<app_id>)",
    )
    parser.add_argument(
        "--app-dir",
        required=True,
        help="Path to your local repository GECX application folder containing app.json",
    )
    parser.add_argument(
        "--mode",
        choices=["audit", "prune"],
        default="audit",
        help="Execution mode: audit (dry-run / summary) or prune (interactive deletes).",
    )
    args = parser.parse_args()

    # Verify local app directory exists
    if not os.path.exists(args.app_dir):
        print(f"[ERROR] Local GECX app directory does not exist: {args.app_dir}")
        sys.exit(1)

    t_client, orphans = fetch_local_and_live_assets(args.app_name, args.app_dir)

    if args.mode == "audit":
        run_audit(orphans)
    elif args.mode == "prune":
        run_prune(t_client, orphans)


if __name__ == "__main__":
    main()
