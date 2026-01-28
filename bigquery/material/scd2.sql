SCD1

MERGE `my_prj.dim.customer` AS T
USING `my_prj.stg.customer_updates` S
ON T.customer_id = S.customer_id
WHEN MATCHED THEN
  UPDATE SET
    T.full_name  = S.full_name,
    T.email      = S.email,
    T.city       = S.city,
    T.updated_at = S.updated_at,
    T._ingested_at = CURRENT_TIMESTAMP()
WHEN NOT MATCHED THEN
  INSERT (customer_id, full_name, email, city, updated_at, _ingested_at)
  VALUES (S.customer_id, S.full_name, S.email, S.city, S.updated_at, CURRENT_TIMESTAMP());


SCD2
CREATE OR REPLACE TABLE seraphic-camera-266118.scd2_implementation.customer_dim (
  customer_id STRING,
  customer_name STRING,
  city STRING,
  start_date DATE,
  end_date DATE
);

CREATE OR REPLACE TABLE seraphic-camera-266118.scd2_implementation.customer_stg (
  customer_id STRING,
  customer_name STRING,
  city STRING
);

INSERT INTO seraphic-camera-266118.scd2_implementation.customer_dim (customer_id, customer_name, city, start_date, end_date)
VALUES
  ('C001', 'John', 'London', DATE '2024-01-01', DATE '9999-12-31'),
  ('C002', 'Mary', 'Paris', DATE '2024-02-01', DATE '9999-12-31'),
  ('C003', 'David', 'Berlin', DATE '2024-03-01', DATE '9999-12-31');

INSERT INTO seraphic-camera-266118.scd2_implementation.customer_dim (customer_id, customer_name, city, start_date, end_date)
VALUES
  ('C000', 'Steve', 'USA', DATE '2024-01-01', DATE '2025-01-24'),
  ('C000', 'Steve', 'Canada', DATE '2025-01-24', DATE '9999-12-31');

  select * from seraphic-camera-266118.scd2_implementation.customer_dim;

  INSERT INTO seraphic-camera-266118.scd2_implementation.customer_stg (customer_id, customer_name, city)
VALUES
  ('C001', 'John', 'Amsterdam'),   -- city changed from London → Amsterdam
  ('C002', 'Mary', 'Paris'),       -- same, no change
  ('C004', 'Emma', 'Madrid'); 

select * from seraphic-camera-266118.scd2_implementation.customer_stg;

--delete from seraphic-camera-266118.scd2_implementation.customer_dim where true

select * from seraphic-camera-266118.scd2_implementation.customer_stg order by customer_id;
select * from seraphic-camera-266118.scd2_implementation.customer_dim order by customer_id,end_date;

CREATE OR REPLACE TEMP TABLE detect_changes AS
WITH detect_changes_cte AS (
  SELECT 
      stg.customer_id,
      stg.customer_name AS stg_customer_name,
      stg.city AS stg_city,
      dim.customer_name AS dim_customer_name,
      dim.city AS dim_city,
      dim.start_date,
      dim.end_date,
      CASE 
          WHEN dim.customer_id IS NULL THEN 'I'  -- New record
          WHEN dim.customer_name <> stg.customer_name 
               OR dim.city <> stg.city THEN 'U'  -- Updated record
          ELSE 'C'                               -- Current / no change
      END AS change_type
  FROM seraphic-camera-266118.scd2_implementation.customer_stg stg
  LEFT JOIN seraphic-camera-266118.scd2_implementation.customer_dim dim
    ON stg.customer_id = dim.customer_id
   AND dim.end_date = DATE "9999-12-31"
)
SELECT * FROM detect_changes_cte;


UPDATE seraphic-camera-266118.scd2_implementation.customer_dim AS dim
SET end_date = CURRENT_DATE()
FROM detect_changes AS dc
WHERE dim.customer_id = dc.customer_id
  AND dim.end_date = DATE "9999-12-31"
  AND dc.change_type = 'U';
  
INSERT INTO seraphic-camera-266118.scd2_implementation.customer_dim
(customer_id, customer_name, city, start_date, end_date)
SELECT 
    customer_id, 
    stg_customer_name, 
    stg_city, 
    CURRENT_DATE() AS start_date, 
    DATE "9999-12-31" AS end_date
FROM detect_changes
WHERE change_type IN ('I','U');
