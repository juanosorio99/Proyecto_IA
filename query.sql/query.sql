SELECT
    vr.rent_num              AS "ALQUILER_VARIABLE",
    p.period_num             AS "NRO_PERIODO",
    vol.start_date           AS "FECHA_INICIAL",
    vol.end_date             AS "FECHA_FINAL",
    vol.group_date           AS "FECHA_GRUPO",
    vol.due_date             AS "FECHA_VENCIMIENTO",
    vol.actual_amount        AS "IMPORTE_REAL",
    vol.vol_hist_status_code AS "ESTADO",
    l.name                   AS "NOMBRE_CLIENTE",
    vl.sales_type_code       AS "TIPO_1",
    vl.item_category_code    AS "CICLO_FACTURACION"
FROM
    pn.pn_var_rents_all vr
    JOIN pn.pn_var_periods_all p
        ON p.var_rent_id = vr.var_rent_id
    JOIN pn.pn_var_lines_all vl
        ON vl.var_rent_id = vr.var_rent_id
       AND vl.period_id = p.period_id
    JOIN apps.pn_var_vol_hist_all vol
        ON vol.line_item_id = vl.line_item_id
    JOIN pn.pn_leases_all l
        ON vr.lease_id = l.lease_id
WHERE
    p.start_date >= DATE '2026-01-01'
    AND p.end_date <= DATE '2026-12-31'
ORDER BY
    vr.rent_num,
    vol.group_date;