import logging
import os
import json

snapshot_dir = r"F:\Workspace\Bahmni_Project\KIS-Projekt\scripts\JSON\DB Snapshots"
output_file = r"F:\Workspace\Bahmni_Project\KIS-Projekt\scripts\JSON\DB Snapshots\snapshot_comparison.md"
files = sorted([f for f in os.listdir(snapshot_dir) if f.endswith('.json')])

snapshots = []
for f in files:
    path = os.path.join(snapshot_dir, f)
    with open(path, 'r', encoding='utf-8') as file:
        snapshots.append((f, json.load(file)))

with open(output_file, 'w', encoding='utf-8') as out:
    out.write("# Database Snapshot Comparison\n\n")
    
    for idx in range(len(snapshots) - 1):
        f_old, data_old = snapshots[idx]
        f_new, data_new = snapshots[idx + 1]
        
        step_name = f_new.replace("db_table_counts_", "").replace(".json", "")
        out.write(f"## Step {idx+1} to {idx+2}: {step_name}\n")
        
        changes_found = False
        all_dbs = set(data_old.keys()).union(set(data_new.keys()))
        
        for db in sorted(all_dbs):
            tables_old = data_old.get(db, {})
            tables_new = data_new.get(db, {})
            
            all_tables = set(tables_old.keys()).union(set(tables_new.keys()))
            
            db_changes = []
            for table in sorted(all_tables):
                count_old = tables_old.get(table, 0)
                count_new = tables_new.get(table, 0)
                
                if count_old != count_new:
                    diff = count_new - count_old
                    sign = "+" if diff > 0 else ""
                    db_changes.append(f"| `{table}` | {count_old} | {count_new} | {sign}{diff} |")
                    
            if db_changes:
                changes_found = True
                out.write(f"### Database: `{db}`\n")
                out.write("| Table | Old Count | New Count | Difference |\n")
                out.write("|-------|-----------|-----------|------------|\n")
                out.write("\n".join(db_changes) + "\n\n")
                    
        if not changes_found:
            out.write("*No changes detected in any database.*\n\n")
