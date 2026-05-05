INSERT INTO users (name, email) VALUES
('João Silva', 'joao@email.com'),
('Maria Santos', 'maria@email.com'),
('Pedro Costa', 'pedro@email.com');

INSERT INTO accounts (user_id, account_type, balance) VALUES
(1, 'corrente', 5000),
(2, 'poupanca', 12000),
(3, 'corrente', 3000);

INSERT INTO categories (category_name, category_type) VALUES
('Salário', 'income'),
('Alimentação', 'expense'),
('Transporte', 'expense');

INSERT INTO transactions (account_id, category_id, amount, transaction_type, created_at) VALUES
(1, 1, 3000, 'income', NOW() - INTERVAL '30 days'),
(1, 2, -150, 'expense', NOW() - INTERVAL '20 days'),
(2, 1, 5000, 'income', NOW() - INTERVAL '25 days'),
(3, 3, -80, 'expense', NOW() - INTERVAL '10 days');