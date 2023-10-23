# Database Scheme
The database-writer expects the following table structure when inserting tracking results into the configured database.
```sql
CREATE TABLE IF NOT EXISTS public.detection
(
    "DETECTION_ID" integer,
    "CAPTURE_TS" timestamp with time zone NOT NULL,
    "CAMERA_ID" character varying COLLATE pg_catalog."default",
    "OBJECT_ID" character varying COLLATE pg_catalog."default",
    "CLASS_ID" integer,
    "CONFIDENCE" double precision,
    "MIN_X" integer,
    "MIN_Y" integer,
    "MAX_X" integer,
    "MAX_Y" integer
)
```

For performance it is important to create this table as a hypertable
(if the target database is a TimescaleDB, which it should be).
Also, the indices below might help to speed up common queries.

```sql 
SELECT create_hypertable('detection', 'CAPTURE_TS');

CREATE INDEX IF NOT EXISTS detection_camera_id
    ON public.detection USING btree
    ("CAMERA_ID" COLLATE pg_catalog."default" ASC NULLS LAST)
    TABLESPACE pg_default;
    
CREATE INDEX IF NOT EXISTS detection_object_id
    ON public.detection USING btree
    ("OBJECT_ID" COLLATE pg_catalog."default" ASC NULLS LAST)
    TABLESPACE pg_default;
```