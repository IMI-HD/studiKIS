DO $$
DECLARE
    v_test_id int;
    v_next_id int;
BEGIN
    SELECT COALESCE(MAX(id), 0) INTO v_next_id FROM clinlims.result_limits;

    -- Test: Base Excess (BE) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Base Excess (BE)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = -2.0,
            high_normal = 3.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', -2.0, 3.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: pH (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'pH' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 7.35,
            high_normal = 7.45,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 7.35, 7.45, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: pCO2 (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'pCO2' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 32.0,
            high_normal = 45.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 32.0, 45.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: pO2 (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'pO2' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 65.0,
            high_normal = 100.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 65.0, 100.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Standardbikarbonat (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Standardbikarbonat' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 22.0,
            high_normal = 26.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 22.0, 26.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Blutkörperchensenkungsgeschwindigkeit (BSG-BKS-BSR) nach Westergren (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Blutkörperchensenkungsgeschwindigkeit (BSG-BKS-BSR) nach Westergren' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 0.0,
            high_normal = 20.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = 'F'
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', 'F', 0.0, 20.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Blutkörperchensenkungsgeschwindigkeit (BSG-BKS-BSR) nach Westergren (Bereich 2)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Blutkörperchensenkungsgeschwindigkeit (BSG-BKS-BSR) nach Westergren' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 0.0,
            high_normal = 15.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = 'M'
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', 'M', 0.0, 15.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Leukozyten (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Leukozyten' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 4000.0,
            high_normal = 10000.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 4000.0, 10000.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Myelozyten/Metamyelozyten (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Myelozyten/Metamyelozyten' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 0.0,
            high_normal = 1.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 0.0, 1.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Stabkernige (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Stabkernige' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 3.0,
            high_normal = 5.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 3.0, 5.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Segmentkernige (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Segmentkernige' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 50.0,
            high_normal = 70.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 50.0, 70.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Eosinophile (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Eosinophile' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 1.0,
            high_normal = 4.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 1.0, 4.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Basophile (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Basophile' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 0.0,
            high_normal = 1.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 0.0, 1.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Lymphozyten (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Lymphozyten' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 25.0,
            high_normal = 45.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 25.0, 45.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Monozyten (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Monozyten' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 3.0,
            high_normal = 7.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 3.0, 7.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Thrombozyten (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Thrombozyten' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 150.0,
            high_normal = 400.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 150.0, 400.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Erythrozyten (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Erythrozyten' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 3.5,
            high_normal = 5.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = 'F'
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', 'F', 3.5, 5.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Erythrozyten (Bereich 2)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Erythrozyten' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 4.3,
            high_normal = 5.9,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = 'M'
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', 'M', 4.3, 5.9, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Retikulozyten (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Retikulozyten' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 0.5,
            high_normal = 2.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 0.5, 2.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: MCV (mittleres korpuskuläres Volumen) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'MCV (mittleres korpuskuläres Volumen)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 81.0,
            high_normal = 100.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 81.0, 100.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: MCH (mittlerer korpuskulärer Hämoglobingehalt) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'MCH (mittlerer korpuskulärer Hämoglobingehalt)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 27.0,
            high_normal = 34.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 27.0, 34.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: MCHC (mittlere korpuskuläre Hämoglobinkonzentration) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'MCHC (mittlere korpuskuläre Hämoglobinkonzentration)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 320.0,
            high_normal = 360.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 320.0, 360.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Hämoglobin (Hb) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Hämoglobin (Hb)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 12.0,
            high_normal = 15.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = 'F'
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', 'F', 12.0, 15.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Hämoglobin (Hb) (Bereich 2)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Hämoglobin (Hb)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 13.6,
            high_normal = 17.2,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = 'M'
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', 'M', 13.6, 17.2, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: HbA1c (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'HbA1c' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 4.0,
            high_normal = 6.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 4.0, 6.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Hämatokrit (Hkt) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Hämatokrit (Hkt)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 0.33,
            high_normal = 0.43,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = 'F'
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', 'F', 0.33, 0.43, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Hämatokrit (Hkt) (Bereich 2)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Hämatokrit (Hkt)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 0.39,
            high_normal = 0.49,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = 'M'
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', 'M', 0.39, 0.49, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Thromboplastinzeit (TPZ; Quick) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Thromboplastinzeit (TPZ; Quick)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 70.0,
            high_normal = 130.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 70.0, 130.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: aktivierte partielle Thromboplastinzeit (aPTT) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'aktivierte partielle Thromboplastinzeit (aPTT)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 28.0,
            high_normal = 40.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 28.0, 40.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Plasma-Thrombinzeit (PTZ) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Plasma-Thrombinzeit (PTZ)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 17.0,
            high_normal = 24.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 17.0, 24.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Fibrinogen (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Fibrinogen' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 1.8,
            high_normal = 3.5,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 1.8, 3.5, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Antithrombin III (AT-III) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Antithrombin III (AT-III)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 0.14,
            high_normal = 0.39,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 0.14, 0.39, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: D-Dimere (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'D-Dimere' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 0.0,
            high_normal = 0.5,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 0.0, 0.5, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Alanin-Aminotransferase (S) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Alanin-Aminotransferase (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 0.0,
            high_normal = 35.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = 'F'
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', 'F', 0.0, 35.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Alanin-Aminotransferase (S) (Bereich 2)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Alanin-Aminotransferase (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 0.0,
            high_normal = 45.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = 'M'
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', 'M', 0.0, 45.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Albumin (S) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Albumin (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 35.0,
            high_normal = 50.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 35.0, 50.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: α-Amylase (S) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'α-Amylase (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 0.0,
            high_normal = 100.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 0.0, 100.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Antistreptolysintiter (S) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Antistreptolysintiter (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 0.0,
            high_normal = 200.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 0.0, 200.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Aspartat-Aminotransferase (S) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Aspartat-Aminotransferase (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 0.0,
            high_normal = 30.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = 'F'
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', 'F', 0.0, 30.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Aspartat-Aminotransferase (S) (Bereich 2)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Aspartat-Aminotransferase (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 0.0,
            high_normal = 35.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = 'M'
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', 'M', 0.0, 35.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Bilirubin, gesamt (S) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Bilirubin, gesamt (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 0.0,
            high_normal = 1.1,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 0.0, 1.1, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Bilirubin, direkt (S) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Bilirubin, direkt (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 0.0,
            high_normal = 0.6,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 0.0, 0.6, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: CEA (S) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'CEA (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 0.0,
            high_normal = 5.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 0.0, 5.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Chlorid (S) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Chlorid (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 98.0,
            high_normal = 106.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 98.0, 106.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Cholesterin (Cholesterol), gesamt (S) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Cholesterin (Cholesterol), gesamt (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 0.0,
            high_normal = 200.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 0.0, 200.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: HDL-Cholesterin (S) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'HDL-Cholesterin (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 35.0,
            high_normal = 100.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 35.0, 100.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: LDL-Cholesterin (S) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'LDL-Cholesterin (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 0.0,
            high_normal = 155.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 0.0, 155.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: C-reaktives Protein (CRP) (S) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'C-reaktives Protein (CRP) (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 0.0,
            high_normal = 5.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 0.0, 5.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Cholinesterase (ChE) (S) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Cholinesterase (ChE) (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 4.3,
            high_normal = 11.3,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 4.3, 11.3, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Cholinesterase (ChE) (S) (Bereich 2)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Cholinesterase (ChE) (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 5.3,
            high_normal = 12.9,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = 'M'
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', 'M', 5.3, 12.9, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Eisen (S) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Eisen (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 45.0,
            high_normal = 160.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 45.0, 160.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Ferritin (S) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Ferritin (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 6.0,
            high_normal = 81.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = 'F'
          AND COALESCE(min_age, 0) = 18.0
          AND max_age = 45.0;

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 18.0, 45.0, 'F', 6.0, 81.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Ferritin (S) (Bereich 2)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Ferritin (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 30.0,
            high_normal = 233.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = 'M'
          AND COALESCE(min_age, 0) = 18.0
          AND max_age = 45.0;

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 18.0, 45.0, 'M', 30.0, 233.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Ferritin (S) (Bereich 3)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Ferritin (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 14.0,
            high_normal = 186.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = 'F'
          AND COALESCE(min_age, 0) = 46.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 46.0, 'Infinity', 'F', 14.0, 186.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Ferritin (S) (Bereich 4)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Ferritin (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 32.0,
            high_normal = 284.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = 'M'
          AND COALESCE(min_age, 0) = 46.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 46.0, 'Infinity', 'M', 32.0, 284.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Glukose (nüchtern) (VB) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Glukose (nüchtern) (VB)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 3.6,
            high_normal = 5.2,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 3.6, 5.2, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Glutamat-Dehydrogenase (GLDH) (S) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Glutamat-Dehydrogenase (GLDH) (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 0.0,
            high_normal = 6.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 0.0, 6.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: γ-Glutamyl-Transferase (γ-GT) (S) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'γ-Glutamyl-Transferase (γ-GT) (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 0.0,
            high_normal = 38.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = 'F'
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', 'F', 0.0, 38.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: γ-Glutamyl-Transferase (γ-GT) (S) (Bereich 2)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'γ-Glutamyl-Transferase (γ-GT) (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 0.0,
            high_normal = 55.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = 'M'
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', 'M', 0.0, 55.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Harnsäure (S) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Harnsäure (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 2.3,
            high_normal = 6.1,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = 'F'
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', 'F', 2.3, 6.1, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Harnsäure (S) (Bereich 2)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Harnsäure (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 3.6,
            high_normal = 8.2,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = 'M'
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', 'M', 3.6, 8.2, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Harnstoff (S) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Harnstoff (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 20.0,
            high_normal = 50.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND max_age = 65.0;

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 65.0, '', 20.0, 50.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Harnstoff (S) (Bereich 2)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Harnstoff (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 0.0,
            high_normal = 72.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 66.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 66.0, 'Infinity', '', 0.0, 72.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Harnstoff-N (S) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Harnstoff-N (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 9.0,
            high_normal = 23.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND max_age = 65.0;

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 65.0, '', 9.0, 23.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Harnstoff-N (S) (Bereich 2)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Harnstoff-N (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 0.0,
            high_normal = 33.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 66.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 66.0, 'Infinity', '', 0.0, 33.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Hydroxybutyrat-Dehydrogenase (HBDH) (S) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Hydroxybutyrat-Dehydrogenase (HBDH) (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 72.0,
            high_normal = 182.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 72.0, 182.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Kalium (S) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Kalium (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 3.6,
            high_normal = 5.2,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 3.6, 5.2, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Kalzitonin, basal (hCT) (S) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Kalzitonin, basal (hCT) (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 0.0,
            high_normal = 2.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 0.0, 2.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Kalzium, gesamt (S) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Kalzium, gesamt (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 2.2,
            high_normal = 2.65,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 2.2, 2.65, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Kalzium, ionisiert (S) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Kalzium, ionisiert (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 1.15,
            high_normal = 1.35,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 1.15, 1.35, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Komplementsystem (S) C3 (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Komplementsystem (S) C3' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 0.75,
            high_normal = 1.35,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 0.75, 1.35, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Komplementsystem (S) C4 (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Komplementsystem (S) C4' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 0.09,
            high_normal = 0.36,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 0.09, 0.36, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Kreatinin (S) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Kreatinin (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 0.0,
            high_normal = 0.9,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = 'F'
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', 'F', 0.0, 0.9, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Kreatinin (S) (Bereich 2)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Kreatinin (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 0.0,
            high_normal = 1.1,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = 'M'
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', 'M', 0.0, 1.1, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Kreatinkinase (S) CK (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Kreatinkinase (S) CK' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 0.0,
            high_normal = 145.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = 'F'
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', 'F', 0.0, 145.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Kreatinkinase (S) CK (Bereich 2)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Kreatinkinase (S) CK' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 0.0,
            high_normal = 170.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = 'M'
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', 'M', 0.0, 170.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Kreatinkinase (S) CK-MB (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Kreatinkinase (S) CK-MB' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 0.0,
            high_normal = 22.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = 'F'
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', 'F', 0.0, 22.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Kreatinkinase (S) CK-MB (Bereich 2)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Kreatinkinase (S) CK-MB' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 0.0,
            high_normal = 25.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = 'M'
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', 'M', 0.0, 25.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Laktat (P) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Laktat (P)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 0.6,
            high_normal = 1.7,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 0.6, 1.7, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Laktat-Dehydrogenase (LDH) (S) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Laktat-Dehydrogenase (LDH) (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 120.0,
            high_normal = 240.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 120.0, 240.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Lipase (S) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Lipase (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 0.0,
            high_normal = 60.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 0.0, 60.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Magnesium (S) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Magnesium (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 0.77,
            high_normal = 1.03,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = 'F'
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', 'F', 0.77, 1.03, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Magnesium (S) (Bereich 2)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Magnesium (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 0.73,
            high_normal = 1.06,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = 'M'
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', 'M', 0.73, 1.06, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Natrium (S) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Natrium (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 135.0,
            high_normal = 145.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 135.0, 145.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: PSA (S) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'PSA (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 0.0,
            high_normal = 4.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 0.0, 4.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Phosphat (S) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Phosphat (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 0.84,
            high_normal = 1.45,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 0.84, 1.45, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Phosphatase, alkalische (AP) (S) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Phosphatase, alkalische (AP) (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 35.0,
            high_normal = 105.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = 'F'
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', 'F', 35.0, 105.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Phosphatase, alkalische (AP) (S) (Bereich 2)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Phosphatase, alkalische (AP) (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 40.0,
            high_normal = 130.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = 'M'
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', 'M', 40.0, 130.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Protein, gesamt (S) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Protein, gesamt (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 65.0,
            high_normal = 85.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 65.0, 85.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Thyreoidea-stimulierendes Hormon (TSH) basal (S) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Thyreoidea-stimulierendes Hormon (TSH) basal (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 0.4,
            high_normal = 4.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 0.4, 4.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Thyroxin, gesamt (T4) (S) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Thyroxin, gesamt (T4) (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 55.0,
            high_normal = 110.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 55.0, 110.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Thyroxin, freies (fT4 ) (S) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Thyroxin, freies (fT4 ) (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 8.0,
            high_normal = 18.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 8.0, 18.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Transferrin (S) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Transferrin (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 200.0,
            high_normal = 360.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 200.0, 360.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Triglyzeride (S) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Triglyzeride (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 0.0,
            high_normal = 200.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 0.0, 200.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Triiodthyronin, gesamt (T3 ) (S) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Triiodthyronin, gesamt (T3 ) (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 0.9,
            high_normal = 1.8,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 0.9, 1.8, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Triiodthyronin, freies (fT3 ) (S) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Triiodthyronin, freies (fT3 ) (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 3.5,
            high_normal = 8.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 3.5, 8.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Troponin I (S) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Troponin I (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 0.0,
            high_normal = 0.1,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 0.0, 0.1, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Troponin T (S) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Troponin T (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 0.0,
            high_normal = 0.1,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 0.0, 0.1, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Troponin T-hs (S) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Troponin T-hs (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 0.0,
            high_normal = 14.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 0.0, 14.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Vitamin B1 (S) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Vitamin B1 (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 0.2,
            high_normal = 0.7,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 0.2, 0.7, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Vitamin B12 (S) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Vitamin B12 (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 20.0,
            high_normal = 100.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 20.0, 100.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Zäruloplasmin (S) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Zäruloplasmin (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 25.0,
            high_normal = 60.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = 'F'
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', 'F', 25.0, 60.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Zäruloplasmin (S) (Bereich 2)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Zäruloplasmin (S)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 22.0,
            high_normal = 40.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = 'M'
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', 'M', 22.0, 40.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: GFR nach CKD-EPI (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'GFR nach CKD-EPI' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 90.0,
            high_normal = 'Infinity',
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 90.0, 'Infinity', '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: NT-pro-BNP (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'NT-pro-BNP' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = '-Infinity',
            high_normal = 125.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', '-Infinity', 125.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Spezifisches Gewicht (U-Stix) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Spezifisches Gewicht (U-Stix)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 1015.0,
            high_normal = 1030.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 1015.0, 1030.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: pH (U-Stix) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'pH (U-Stix)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 4.8,
            high_normal = 7.6,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 4.8, 7.6, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Erythrozyten (Urinsediment) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Erythrozyten (Urinsediment)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 0.0,
            high_normal = 1.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 0.0, 1.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

    -- Test: Leukozyten (Urinsediment) (Bereich 1)
    SELECT id INTO v_test_id FROM clinlims.test WHERE name = 'Leukozyten (Urinsediment)' LIMIT 1;
    IF v_test_id IS NOT NULL THEN
        UPDATE clinlims.result_limits
        SET low_normal = 0.0,
            high_normal = 4.0,
            low_valid = '-Infinity',
            high_valid = 'Infinity',
            lastupdated = NOW(),
            always_validate = 'f'
        WHERE test_id = v_test_id
          AND COALESCE(TRIM(gender), '') = ''
          AND COALESCE(min_age, 0) = 0.0
          AND (max_age = 'Infinity' OR max_age IS NULL);

        IF NOT FOUND THEN
            v_next_id := v_next_id + 1;
            INSERT INTO clinlims.result_limits (id, test_id, test_result_type_id, min_age, max_age, gender, low_normal, high_normal, low_valid, high_valid, lastupdated, always_validate)
            VALUES (v_next_id, v_test_id, 4, 0.0, 'Infinity', '', 0.0, 4.0, '-Infinity', 'Infinity', NOW(), 'f');
        END IF;
    END IF;

END $$;