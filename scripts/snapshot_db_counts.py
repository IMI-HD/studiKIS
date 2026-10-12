import os
import subprocess
import json

env_path = r"f:\Workspace\Bahmni_Project\bahmni-docker\bahmni-standard\.env"
env_vars = {}
with open(env_path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("=", 1)
        if len(parts) == 2:
            val = parts[1].strip()
            # remove inline comments
            val = val.split(" ")[0].strip("'\"")
            env_vars[parts[0]] = val

# Definitions of the databases and their containers from docker-compose
db_configs = [
    ("OPENELIS", "openelisdb", "postgres", "OPENELIS_DB_USER", "OPENELIS_DB_PASSWORD", "OPENELIS_DB_NAME"),
    ("ODOO", "odoodb", "postgres", "ODOO_DB_USER", "ODOO_DB_PASSWORD", "ODOO_DB_NAME"),
    ("ODOO_10", "odoo-10-db", "postgres", "ODOO_10_DB_USER", "ODOO_10_DB_PASSWORD", "ODOO_10_DB_NAME"),
    ("OPENMRS", "openmrsdb", "mysql", "OPENMRS_DB_USERNAME", "OPENMRS_DB_PASSWORD", "OPENMRS_DB_NAME"),
    ("REPORTS", "reportsdb", "mysql", "REPORTS_DB_USERNAME", "REPORTS_DB_PASSWORD", "REPORTS_DB_NAME"),
    ("DCM4CHEE", "pacsdb", "postgres", "DCM4CHEE_DB_USERNAME", "DCM4CHEE_DB_PASSWORD", "DCM4CHEE_DB_NAME"),
    ("PACS_INTEGRATION", "pacsdb", "postgres", "PACS_INTEGRATION_DB_USERNAME", "PACS_INTEGRATION_DB_PASSWORD", "PACS_INTEGRATION_DB_NAME"),
    ("METABASE", "metabasedb", "postgres", "METABASE_DB_USER", "METABASE_DB_PASSWORD", "METABASE_DB_NAME"),
    ("MART", "martdb", "postgres", "MART_DB_USERNAME", "MART_DB_PASSWORD", "MART_DB_NAME")
]

output_file = r"F:\Workspace\Bahmni_Project\KIS-Projekt\scripts\JSON\DB Snapshots\db_table_counts.json"

print(f"Starting database snapshot process. Output will be written to {output_file}")

result_dict = {}
active_containers = [c.strip() for c in subprocess.getoutput('docker ps --format "{{.Names}}"').split('\n')]

for prefix, container, db_type, user_var, pass_var, db_var in db_configs:
    user = env_vars.get(user_var)
    password = env_vars.get(pass_var)
    db_name = env_vars.get(db_var)
    
    if not db_name:
        continue
        
    actual_container = None
    for c in active_containers:
        if container in c:
            actual_container = c
            break
            
    if not actual_container:
        print(f"Skipping {prefix} ({db_name}) since container wasn't found.")
        continue
        
    print(f"Processing {prefix} ({db_name}) in {actual_container}...")
    
    if db_type == "postgres":
        # Command to get exact counts by generating a query
        cmd = f'docker exec -e PGPASSWORD="{password}" {actual_container} psql -U {user} -d {db_name} -t -c "SELECT relname, n_live_tup FROM pg_stat_user_tables;"'
    elif db_type == "mysql":
        cmd = f'docker exec {actual_container} mysql -u{user} -p"{password}" -D {db_name} -e "SELECT table_name, table_rows FROM information_schema.tables WHERE table_schema=\'{db_name}\';" -s'
    
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            lines = [line.strip() for line in res.stdout.split('\n') if line.strip()]
            
            table_counts = {}
            for line in lines:
                if db_type == "postgres":
                    parts = line.split("|")
                    if len(parts) == 2:
                        t_name = parts[0].strip()
                        try:
                            t_count = int(parts[1].strip())
                        except ValueError:
                            t_count = 0
                        table_counts[t_name] = t_count
                elif db_type == "mysql":
                    parts = line.split("\t")
                    if len(parts) == 2:
                        t_name = parts[0].strip()
                        try:
                            t_count = int(parts[1].strip())
                        except ValueError:
                            t_count = 0
                        table_counts[t_name] = t_count
            
            # Sort by count descending
            sorted_table_counts = {k: v for k, v in sorted(table_counts.items(), key=lambda item: item[1], reverse=True)}
            
            result_dict[db_name] = sorted_table_counts
        else:
            print(f"Error querying {db_name}: {res.stderr.strip()}")
    except Exception as e:
        print(f"Exception querying {db_name}: {str(e)}")

with open(output_file, "w", encoding="utf-8") as out:
    json.dump(result_dict, out, indent=4)

print("Done!")
