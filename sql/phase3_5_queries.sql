-- =========================================================================
-- Phase 3.5 — SQL & Cloud Database
-- RetainScope: UK Retail Customer Intelligence Platform
--
-- These queries independently reproduce (and extend) the Phase 3 findings
-- using pure SQL against the AWS RDS PostgreSQL database, rather than
-- pandas/scipy. Run against the `retainscope` database.
-- =========================================================================


-- -------------------------------------------------------------------------
-- Query 1: Per-customer RFM (Recency, Frequency, Monetary)
-- Demonstrates: CTE, aggregate functions, BOOL_OR for a "has ever done X" flag
-- -------------------------------------------------------------------------
WITH customer_rfm AS (
    SELECT
        customer_id,
        MAX(invoice_date)::date          AS last_purchase_date,
        COUNT(DISTINCT invoice)          AS frequency,
        SUM(line_value)                  AS monetary,
        BOOL_OR(is_cancellation)         AS has_returned
    FROM transactions
    WHERE customer_id IS NOT NULL
    GROUP BY customer_id
)
SELECT
    customer_id,
    (SELECT MAX(invoice_date)::date FROM transactions) - last_purchase_date AS recency_days,
    frequency,
    monetary,
    has_returned
FROM customer_rfm
ORDER BY monetary DESC;


-- -------------------------------------------------------------------------
-- Query 2: Returners vs. non-returners — median spend comparison
-- Reproduces the Phase 3 headline finding (returners spend ~4x more)
-- independently in SQL. Result: median £469 (never returned) vs
-- £1,883 (has returned) — matches the Phase 3 pandas/scipy result exactly.
-- Demonstrates: CTE, GROUP BY, PERCENTILE_CONT for median (no built-in
-- MEDIAN() function in standard SQL)
-- -------------------------------------------------------------------------
WITH customer_rfm AS (
    SELECT
        customer_id,
        SUM(line_value) AS monetary,
        BOOL_OR(is_cancellation) AS has_returned
    FROM transactions
    WHERE customer_id IS NOT NULL
    GROUP BY customer_id
)
SELECT
    has_returned,
    COUNT(*) AS num_customers,
    ROUND(AVG(monetary)::numeric, 2) AS avg_monetary,
    ROUND(
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY monetary)::numeric, 2
    ) AS median_monetary
FROM customer_rfm
GROUP BY has_returned;


-- -------------------------------------------------------------------------
-- Query 3: Rank customers by spend within their own country
-- Demonstrates: JOIN (fact table to dimension table), window function
-- with PARTITION BY (RANK resets per country, rather than one global rank)
-- -------------------------------------------------------------------------
WITH customer_country AS (
    SELECT
        t.customer_id,
        c.country,
        SUM(t.line_value) AS monetary
    FROM transactions t
    JOIN customers c ON t.customer_id = c.customer_id
    GROUP BY t.customer_id, c.country
)
SELECT
    customer_id,
    country,
    monetary,
    RANK() OVER (PARTITION BY country ORDER BY monetary DESC) AS rank_in_country
FROM customer_country
ORDER BY country, rank_in_country;


-- -------------------------------------------------------------------------
-- Query 4: Cumulative monthly revenue
-- Demonstrates: DATE_TRUNC for monthly bucketing, window function with
-- no PARTITION BY (single running total across the whole date range)
-- -------------------------------------------------------------------------
WITH monthly_revenue AS (
    SELECT
        DATE_TRUNC('month', invoice_date)::date AS month,
        SUM(line_value) AS revenue
    FROM transactions
    GROUP BY DATE_TRUNC('month', invoice_date)
)
SELECT
    month,
    revenue,
    SUM(revenue) OVER (ORDER BY month) AS cumulative_revenue
FROM monthly_revenue
ORDER BY month;