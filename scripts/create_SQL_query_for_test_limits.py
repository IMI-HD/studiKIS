import pandas as pd
import numpy as np
import os

def generate_sql_for_openelis(filename):
    # Pfad relativ zum Skript auflösen
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, filename)
    if not os.path.exists(file_path):
        alt_path = os.path.join(script_dir, 'modify_LIS_scripts', filename)
        if os.path.exists(alt_path):
            file_path = alt_path

    # Datei laden (Excel oder CSV)
    if file_path.endswith('.xlsx'):
        df = pd.read_excel(file_path)
    else:
        df = pd.read_csv(file_path)
    sql_statements = []
    
    # PL/pgSQL-Block für atomare Ausführung und dynamische ID-Vergabe
    sql_statements.append("DO $$")
    sql_statements.append("DECLARE")
    sql_statements.append("    v_test_id int;")
    sql_statements.append("    v_next_id int;")
    sql_statements.append("BEGIN")
    sql_statements.append("    SELECT COALESCE(MAX(id), 0) INTO v_next_id FROM clinlims.result_limits;\n")
    
    limit_count = 0
    
    for _, row in df.iterrows():
        test_name = row.get('Neuer Name')
        if pd.isna(test_name): continue
        
        safe_test_name = str(test_name).strip().replace("'", "''")
        
        for i in range(1, 5):
            low_norm = row.get(f'normal range low{i}')
            high_norm = row.get(f'normal range high{i}')
            
            # Nur verarbeiten, wenn min. ein Grenzwert da ist
            if pd.isna(low_norm) and pd.isna(high_norm): continue
            
            # 1. Geschlecht
            gender = str(row.get(f'Gender{i}', '')).upper().strip()
            gender_sql = f"'{gender}'" if gender in ['M', 'F'] else "''"
            
            # 2. Min Age (Sicherstellen, dass es 0 ist wenn leer/NaN)
            min_age_val = row.get(f'Age (years) min{i}')
            min_age = float(min_age_val) if pd.notna(min_age_val) else 0.0
            
            # 3. Max Age
            max_age_val = row.get(f'Age (years) max{i}')
            max_age_sql = "'Infinity'" if pd.isna(max_age_val) or max_age_val >= 100 else str(max_age_val)
            
            # 4. Grenzwerte (Sicherstellen, dass kein 'nan' im SQL landet)
            low_sql = str(low_norm) if pd.notna(low_norm) else "'-Infinity'"
            high_sql = str(high_norm) if pd.notna(high_norm) else "'Infinity'"

            max_age_condition = "(max_age = 'Infinity' OR max_age IS NULL)" if max_age_sql == "'Infinity'" else f"max_age = {max_age_sql}"

            stmt = f"""    -- Test: {safe_test_name} (Bereich {i})
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = '{safe_test_name}' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = {low_sql},
            high_normal = {high_sql},
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = {gender_sql}
          AND COALESCE(min_age, 0) = {min_age}
          AND {max_age_condition};

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, {min_age}, {max_age_sql}, {gender_sql}, {low_sql}, {high_sql}, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;
"""
            sql_statements.append(stmt)
            limit_count += 1
            
    sql_statements.append("END $$;")
    return sql_statements, limit_count

# Datei generieren
script_dir = os.path.dirname(os.path.abspath(__file__))
inserts, total_processed = generate_sql_for_openelis('Laborwerte_zum_behalten_mit_Normwerten.xlsx')
output_file = os.path.join(script_dir, 'insert_result_limits.sql')
with open(output_file, 'w', encoding='utf-8') as f:
    f.write("\n".join(inserts))

print(f"Erfolgreich {total_processed} UPSERT-Statements für Result Limits generiert -> {output_file}")
# sudo docker cp /home/kislab/KIS-Projekt/scripts/insert_result_limits.sql bahmni-standard-openelisdb-1:/
# sudo docker exec -it bahmni-standard-openelisdb-1 psql -U clinlims -d clinlims -f /insert_result_limits.sql