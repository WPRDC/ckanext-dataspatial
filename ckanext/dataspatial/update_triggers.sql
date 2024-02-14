-- slightly modified from ckanext/datastore's version to ignore dataspatial__ fields
CREATE OR REPLACE FUNCTION populate_full_text_trigger() RETURNS trigger
AS
$body$
BEGIN
    IF NEW._full_text IS NOT NULL THEN
        RETURN NEW;
    END IF;
    NEW._full_text := (SELECT to_tsvector(string_agg(value, ' '))
                       FROM json_each_text(row_to_json(NEW.*))
                       WHERE key NOT LIKE '\_%'
                         AND key NOT ILIKE 'dataspatial%');
    RETURN NEW;
END;

$body$ LANGUAGE plpgsql;

ALTER FUNCTION populate_full_text_trigger() OWNER TO ckanuser;

SELECT 'dataspatial__wkt' ILIKE 'dataspatial%';
