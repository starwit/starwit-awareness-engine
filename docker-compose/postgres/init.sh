#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
	CREATE TABLE IF NOT EXISTS public.data
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
EOSQL