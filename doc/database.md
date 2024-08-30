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
    "max_y" real,
    "latitude" double precision,
    "longitude" double precision
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
## Retention policy
In order to run the setup sustainably, we need to set a retention policy (i.e. drop data after x days):
```sql
SELECT add_retention_policy('detection', INTERVAL '60 days');
```

# Chunk size optimization
TimescaleDB documentation recommends a chunk size that fits into 25% of the available memory. Adjust accordingly:
```sql
SELECT set_chunk_time_interval('detection', INTERVAL '24 hours');
```

# Database migration <1.0.0 => 1.0.0
With 1.0.0 the data type of the bounding box coordinates changed from `integer` to `real` as the coordinates are now normalized (i.e. a fraction of image height / width). If needed, the existing data can be migrated, if the resolution of the camera the data originated from is known. In practice, it is probably advisable to just drop all data and change the table format, as migrating big amounts of data can take a while and short downtime is mostly preferable to keeping historic data.

## Schema migration
```sql
ALTER TABLE detection RENAME COLUMN min_x TO min_x_abs;
ALTER TABLE detection RENAME COLUMN min_y TO min_y_abs;
ALTER TABLE detection RENAME COLUMN max_x TO max_x_abs;
ALTER TABLE detection RENAME COLUMN max_y TO max_y_abs;

ALTER TABLE detection
    ADD COLUMN min_x REAL,
    ADD COLUMN min_y REAL,
    ADD COLUMN max_x REAL,
    ADD COLUMN max_y REAL;

UPDATE detection SET
    min_x = min_x_abs::REAL / <x_resolution>,
    min_y = min_y_abs::REAL / <y_resolution>,
    max_x = max_x_abs::REAL / <x_resolution>,
    max_y = max_y_abs::REAL / <y_resolution>;

ALTER TABLE detection DROP COLUMN min_x_abs;
ALTER TABLE detection DROP COLUMN min_y_abs;
ALTER TABLE detection DROP COLUMN max_x_abs;
ALTER TABLE detection DROP COLUMN max_y_abs;
```

# Database migration <2.1.0 => 2.1.0 (geo-mapper)
```sql
ALTER TABLE detection ADD COLUMN "latitude" DOUBLE PRECISION;
ALTER TABLE detection ADD COLUMN "longitude" DOUBLE PRECISION;
```

# Export database as CSV
## With remote access
`psql -U sae -h <host> -p <port> -c "\copy (select * from detection order by capture_ts asc limit 10) TO STDOUT CSV HEADER"`
## Gzipped through kubectl
`kubectl exec -n timescale timescale-0 -- bash -c "psql sae -c \"COPY (select * from detection limit 10) TO STDOUT DELIMITER ',' CSV HEADER;\" | gzip" > out.csv.gz`

# Backup and Restore
## Backup
`pg_dump -h <db_host> -p <db_port> -U <db_user> -F custom -f <dumpfile> -d <db_name>`
If you need to only export a certain schema (default: all schemas in specified database), you can add `-n <pattern>`

## Restore
- Before restoring run `SELECT timescaledb_pre_restore();`
- Do the restore\
    `pg_restore -U <db_user> -h <db_host> -p <db_port> -d <target_db_name> --no-tablespaces --no-owner --no-privileges <dumpfile>`
- After process has finished run `SELECT timescaledb_post_restore();`