# ----------------
# Source database:
# ----------------
\o c.sql
select 'update res_partner set migration_old_id=' || id || ' where sql_customer_code=''' || mexal_c || ''';'  from res_partner where mexal_c is not null;

\o s.sql
select 'update res_partner set migration_old_id=' || id || ' where sql_supplier_code=''' || mexal_s || ''';'  from res_partner where mexal_s is not null;

\o dc.sql 
select 'update res_partner set migration_old_id=' || id || ' where sql_destination_code=''' || mexal_c || ''';'  from res_partner where mexal_c is not null;

\o ds.sql 
select 'update res_partner set migration_old_id=' || id || ' where sql_destination_code=''' || mexal_s || ''';'  from res_partner where mexal_s is not null;

# --------------------------
# Clean sql from extra line!
# --------------------------

# ---------------------
# Destination database:
# ---------------------
\i c.sql
\i s.sql
\i dc.sql
\i ds.sql


# -------------------------------------------------------------------
# TODO delete partner duplicated (some destination with address code)
# -------------------------------------------------------------------

# Check:
select id, sql_customer_code, sql_supplier_code, sql_destination_code, migration_old_id from res_partner;
