WITH rfm AS (
    SELECT 
        u.user_id,
        u.name,

        MAX(t.created_at) AS last_transaction,
        COUNT(t.transaction_id) AS frequency,
        SUM(t.amount) AS monetary,

        NTILE(5) OVER (ORDER BY MAX(t.created_at) DESC) AS recency_score,
        NTILE(5) OVER (ORDER BY COUNT(t.transaction_id)) AS frequency_score,
        NTILE(5) OVER (ORDER BY SUM(t.amount)) AS monetary_score

    FROM {{ ref('fct_transactions') }} t
    JOIN accounts a ON t.account_id = a.account_id
    JOIN users u ON a.user_id = u.user_id

    GROUP BY u.user_id, u.name
)

SELECT *,
    (recency_score + frequency_score + monetary_score) AS rfm_score,

    CASE
        WHEN (recency_score + frequency_score + monetary_score) >= 13 THEN 'VIP'
        WHEN (recency_score + frequency_score + monetary_score) >= 9 THEN 'Ativo'
        WHEN recency_score <= 2 THEN 'Risco de Churn'
        ELSE 'Regular'
    END AS segment

FROM rfm