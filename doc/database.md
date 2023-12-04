# Database Scheme
The database-writer expects the following table structure when inserting tracking results into the configured database.
```sql
CREATE TABLE IF NOT EXISTS public.detection
(
    "detection_id" integer,
    "capture_ts" timestamp with time zone NOT NULL,
    "camera_id" character varying COLLATE pg_catalog."default",
    "object_id" character varying COLLATE pg_catalog."default",
    "class_id" integer,
    "confidence" double precision,
    "min_x" integer,
    "min_y" integer,
    "max_x" integer,
    "max_y" integer
)
```

For performance it is important to create this table as a hypertable
(if the target database is a TimescaleDB, which it should be).
Also, the indices below might help to speed up common queries.

```sql 
SELECT create_hypertable('detection', 'capture_ts');

CREATE INDEX IF NOT EXISTS detection_camera_id
    ON public.detection USING btree
    ("camera_id" COLLATE pg_catalog."default" ASC NULLS LAST)
    TABLESPACE pg_default;
    
CREATE INDEX IF NOT EXISTS detection_object_id
    ON public.detection USING btree
    ("object_id" COLLATE pg_catalog."default" ASC NULLS LAST)
    TABLESPACE pg_default;
```