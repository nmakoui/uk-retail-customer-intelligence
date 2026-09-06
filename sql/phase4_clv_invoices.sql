WITH invoices AS (
    SELECT
        customer_id,
        invoice,
        MIN(invoice_date) AS invoice_date,
        SUM(line_value)   AS invoice_value
    FROM transactions
    WHERE customer_id IS NOT NULL
      AND is_cancellation = FALSE
    GROUP BY customer_id, invoice
)
SELECT customer_id, invoice, invoice_date, invoice_value
FROM invoices
ORDER BY customer_id, invoice_date;