#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
	CREATE TABLE IF NOT EXISTS public.data
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
EOSQL