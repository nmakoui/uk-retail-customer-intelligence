-- =========================================================================
-- Phase 4 — Churn/CLV Modelling
-- Builds the per-customer feature table + churn label for the ML model.
--
-- Cutoff date: 2011-09-09 (3-month holdout, chosen deliberately for a
-- stricter/earlier churn signal — dataset runs 2009-12-01 to 2011-12-09).
-- Calibration period (features): before cutoff
-- Holdout period (churn label):  cutoff onward — no purchase = churned
-- =========================================================================

WITH cutoff AS (
    SELECT DATE '2011-09-09' AS cutoff_date
),
calibration AS (
    SELECT
        t.customer_id,
        MIN(t.invoice_date)::date AS first_purchase_date,
        MAX(t.invoice_date)::date AS last_purchase_date,
        COUNT(DISTINCT t.invoice)  AS frequency,
        SUM(t.line_value)          AS monetary,
        BOOL_OR(t.is_cancellation) AS has_returned
    FROM transactions t, cutoff
    WHERE t.customer_id IS NOT NULL
      AND t.invoice_date < cutoff.cutoff_date
    GROUP BY t.customer_id
),
holdout_purchasers AS (
    SELECT DISTINCT t.customer_id
    FROM transactions t, cutoff
    WHERE t.customer_id IS NOT NULL
      AND t.invoice_date >= cutoff.cutoff_date
)
SELECT
    c.customer_id,
    (cutoff.cutoff_date - c.first_purchase_date)      AS tenure_days,
    (cutoff.cutoff_date - c.last_purchase_date)        AS recency_days,
    c.frequency,
    c.monetary,
    ROUND((c.monetary / c.frequency)::numeric, 2)      AS avg_order_value,
    c.has_returned,
    CASE WHEN h.customer_id IS NULL THEN 1 ELSE 0 END  AS churned
FROM calibration c
CROSS JOIN cutoff
LEFT JOIN holdout_purchasers h ON c.customer_id = h.customer_id
ORDER BY c.customer_id;