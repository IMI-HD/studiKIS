import pandas as pd
import numpy as np
import os

def generate_sql_for_openelis(filename):
    # Pfad relativ zum Skript auflösen
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, filename)

    # Datei laden (Excel oder CSV)
    if filename.endswith('.xlsx'):
        df = pd.read_excel(file_path)
    else:
        df = pd.read_csv(file_path)
    sql_statements = []
    
    # Wir starten einen SQL-Block, damit wir die Start-ID nur einmal ermitteln müssen
    sql_statements.append("DO $$")
    sql_statements.append("DECLARE")
    sql_statements.append("    start_id int;")
    sql_statements.append("BEGIN")
    sql_statements.append("    -- Wir holen uns die aktuell höchste ID als Startpunkt")
    sql_statements.append("    SELECT COALESCE(MAX(id), 0) INTO start_id FROM clinlims.result_limits;")
    
    current_row_index = 1
    
    for _, row in df.iterrows():
        test_name = row['Neuer Name']
        if pd.isna(test_name): continue
        
        safe_test_name = str(test_name).strip().replace("'", "''")
        
        for i in range(1, 5):
            low_norm = row.get(f'normal range low{i}')
            high_norm = row.get(f'normal range high{i}')
            
            # Nur verarbeiten, wenn min. ein Grenzwert da ist
            if pd.isna(low_norm) and pd.isna(high_norm): continue
            
            # 1. Geschlecht
            gender = str(row.get(f'Gender{i}', '')).upper().strip()
            gender_sql = f"'{gender}'" if gender in ['M', 'F'] else "NULL"
            
            # 2. Min Age (Sicherstellen, dass es 0 ist wenn leer/NaN)
            min_age_val = row.get(f'Age (years) min{i}')
            min_age = float(min_age_val) if pd.notna(min_age_val) else 0.0
            
            # 3. Max Age
            max_age_val = row.get(f'Age (years) max{i}')
            max_age_sql = "'Infinity'" if pd.isna(max_age_val) or max_age_val >= 100 else str(max_age_val)
            
            # 4. Grenzwerte (Sicherstellen, dass kein 'nan' im SQL landet)
            low_sql = str(low_norm) if pd.notna(low_norm) else "'-Infinity'"
            high_sql = str(high_norm) if pd.notna(high_norm) else "'Infinity'"

            stmt = f"""
    INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate) 
    VALUES (start_id + {current_row_index}, (SELECT id FROM clinlims.test WHERE name = '{safe_test_name}' LIMIT 1), 4, {min_age}, {max_age_sql}, {gender_sql}, {low_sql}, {high_sql}, '-Infinity', 'Infinity', NOW(), 'f');"""
            
            sql_statements.append(stmt)
            current_row_index += 1
            
    sql_statements.append("END $$;")
    return sql_statements

# Datei generieren
inserts = generate_sql_for_openelis('Laborwerte_zum_behalten_mit_Normwerten.xlsx')
with open('insert_result_limits_v3.sql', 'w', encoding='utf-8') as f:
    f.write("\n".join(inserts))

print(f"Erfolgreich {len(inserts)-5} Statements generiert. Fehlerhafte 'nan' wurden durch 0 oder Standardwerte ersetzt.")