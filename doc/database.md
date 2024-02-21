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
    "min_x" real,
    "min_y" real,
    "max_x" real,
    "max_y" real
);
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

# Export database as CSV
`psql -U sae -h <host> -p <port> -c "\copy (select * from detection order by capture_ts desc limit 10) TO STDOUT CSV HEADER"`

# Backup and Restore
## Backup
`pg_dump -h <db_host> -p <db_port> -U <db_user> -F custom -f <dumpfile> -d <db_name>`
If you need to only export a certain schema (default: all schemas in specified database), you can add `-n <pattern>`

## Restore
- Before restoring run `SELECT timescaledb_pre_restore();`
- Do the restore\
    `pg_restore -U <db_user> -h <db_host> -p <db_port> -d <target_db_name> --no-tablespaces --no-owner --no-privileges <dumpfile>`
- After process has finished run `SELECT timescaledb_post_restore();`