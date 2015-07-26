# ----------------
# Source database:
# ----------------
\o p2.sql
select 'update sale_order_line set price_unit_manual= ' || price_unit_manual || ', price_use_manual=' || price_use_manual || ' where migration_old_id = ' || id || ';' from sale_order_line where multi_discount_rates is  null;

\o p1.sql
select 'update sale_order_line set price_unit_manual= ' || price_unit_manual || ', price_use_manual=' || price_use_manual || ', multi_discount_rates=''' || multi_discount_rates || ''' where migration_old_id = ' || id || ';' from sale_order_line where multi_discount_rates is not null;


# --------------------------
# Clean sql from extra line!
# --------------------------

# ---------------------
# Destination database:
# ---------------------
\i p1.sql
\i p2.sql

