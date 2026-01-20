-- SEED DE EQUIPOS Y EVENTOS DE MANTENIMIENTO
-- Ejecutar: psql -U usuario -d basedatos -f scripts/seed_equipment.sql

-- Limpiar tablas existentes
TRUNCATE failure_events, maintenance_events, equipment RESTART IDENTITY CASCADE;

-- INSERT DE EQUIPOS (50 equipos)
INSERT INTO equipment (equipment_id, tipo_maquina, marca, modelo, ano)
SELECT
    'EQ-' || lpad(gs::text, 3, '0'),
    (ARRAY['Excavadora','Cargador','Motoniveladora','Compactador','Dump Truck','Retroexcavadora'])[floor(random()*6)+1],
    (ARRAY['Caterpillar','Komatsu','Volvo','John Deere','Hyundai','Doosan','BOMAG','JCB'])[floor(random()*8)+1],
    'MD-' || floor(random()*500 + 100),
    floor(random()*10 + 2015)
FROM generate_series(1,50) gs;

-- INSERT DE MANTENIMIENTOS (5,000 registros)
INSERT INTO maintenance_events (
    equipment_id, fecha, tipo_intervencion, descripcion_tarea,
    horas_operacion, costo_total, duracion_horas, responsable, ubicacion_gps
)
SELECT
    'EQ-' || lpad((floor(random()*50)+1)::text,3,'0'),
    date '2022-01-01' + (floor(random()*800)) * interval '1 day',
    (ARRAY['Preventivo','Preventivo','Preventivo','Predictivo'])[floor(random()*4)+1],
    (ARRAY['Cambio aceite y filtros','Revisión general','Lubricación articulaciones',
           'Ajuste frenos','Inspección hidráulica','Análisis de vibraciones'])[floor(random()*6)+1],
    floor(random()*9000 + 500),
    floor(random()*1500000 + 50000),
    floor(random()*6 + 1),
    (ARRAY['Técnico A','Técnico B','Técnico C','Técnico D','Sistema IoT'])[floor(random()*5)+1],
    '-33.' || floor(random()*600) || ',-70.' || floor(random()*700)
FROM generate_series(1,5000);

-- INSERT DE FALLAS (3,000 registros)
INSERT INTO failure_events (
    equipment_id, fecha, codigo_falla, descripcion_falla, causa_raiz,
    horas_operacion, costo_total, duracion_horas, responsable, ubicacion_gps, impacto
)
SELECT
    'EQ-' || lpad((floor(random()*50)+1)::text,3,'0'),
    date '2022-01-01' + (floor(random()*800)) * interval '1 day',
    'F-' || floor(random()*999 + 1),
    (ARRAY['Baja presión aceite','Vibración anormal','Freno sin accionamiento',
           'Sobrecalentamiento motor','Fuga hidráulica','Dificultad encendido'])[floor(random()*6)+1],
    (ARRAY['Desgaste por uso','Falta de lubricación','Sensor fallado',
           'Obstrucción radiador','Rotura de sello','Fatiga mecánica'])[floor(random()*6)+1],
    floor(random()*9000 + 500),
    floor(random()*2000000 + 100000),
    floor(random()*10 + 1),
    (ARRAY['Técnico A','Técnico B','Técnico C','Técnico D'])[floor(random()*4)+1],
    '-33.' || floor(random()*600) || ',-70.' || floor(random()*700),
    (ARRAY['Detención 2h','Detención 4h','Detención 6h','Detención 8h','Detención 1h'])[floor(random()*5)+1]
FROM generate_series(1,3000);

-- Verificar
SELECT 'equipment' as tabla, COUNT(*) as registros FROM equipment
UNION ALL SELECT 'maintenance_events', COUNT(*) FROM maintenance_events
UNION ALL SELECT 'failure_events', COUNT(*) FROM failure_events;