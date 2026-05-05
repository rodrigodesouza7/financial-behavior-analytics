SELECT
    t.transaction_id,
    t.account_id,
    a.user_id,               -- 🔥 necessário para analytics
    t.category_id,
    t.amount,
    t.transaction_type,
    t.created_at

FROM {{ ref('stg_transactions') }} t
JOIN accounts a 
    ON t.account_id = a.account_id