-- QuantumLeap Investment Portal Seed Data
-- Baseline seed queries for demonstration & testing

-- Default demo user: alex_investor (Password: Password123!)
-- SHA256 of "Password123!": 5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8 (or salt-based)
INSERT OR IGNORE INTO users (id, username, email, password_hash, full_name)
VALUES (1, 'alex_investor', 'alex.investor@quantumleap.io', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'Alex Vance');

-- Investment Accounts for Alex Vance
INSERT OR IGNORE INTO accounts (id, user_id, account_number, account_type, name, balance, currency)
VALUES (1, 1, 'QL-INV-1001', 'Individual Brokerage', 'Growth & Tech Opportunities', 48500.75, 'USD');

INSERT OR IGNORE INTO accounts (id, user_id, account_number, account_type, name, balance, currency)
VALUES (2, 1, 'QL-IRA-2002', 'Roth IRA', 'Retirement Horizon 2055', 72450.00, 'USD');

INSERT OR IGNORE INTO accounts (id, user_id, account_number, account_type, name, balance, currency)
VALUES (3, 1, 'QL-HYSA-3003', 'High-Yield Cash', 'Quantum High-Yield Reserve (4.8% APY)', 15200.50, 'USD');

INSERT OR IGNORE INTO accounts (id, user_id, account_number, account_type, name, balance, currency)
VALUES (4, 1, 'QL-TRAD-4004', 'Traditional IRA', 'Tax-Advantaged Core Index', 31800.25, 'USD');

-- Initial Transactions for Account 1 (Brokerage)
INSERT OR IGNORE INTO transactions (id, account_id, type, amount, description, balance_after)
VALUES (1, 1, 'DEPOSIT', 50000.00, 'Initial Portfolio Funding via Wire', 50000.00);

INSERT OR IGNORE INTO transactions (id, account_id, type, amount, description, balance_after)
VALUES (2, 1, 'BUY', -3500.00, 'Purchased 25 shares of VOO Vanguard S&P 500 ETF', 46500.00);

INSERT OR IGNORE INTO transactions (id, account_id, type, amount, description, balance_after)
VALUES (3, 1, 'DIVIDEND', 2000.75, 'Quarterly Dividend Reinvestment Distribution', 48500.75);

-- Initial Transactions for Account 2 (Roth IRA)
INSERT OR IGNORE INTO transactions (id, account_id, type, amount, description, balance_after)
VALUES (4, 2, 'DEPOSIT', 70000.00, 'Annual Maximum IRA Contribution Rollover', 70000.00);

INSERT OR IGNORE INTO transactions (id, account_id, type, amount, description, balance_after)
VALUES (5, 2, 'DIVIDEND', 2450.00, 'Annual Distribution Allocation', 72450.00);

-- Initial Transactions for Account 3 (Cash Reserve)
INSERT OR IGNORE INTO transactions (id, account_id, type, amount, description, balance_after)
VALUES (6, 3, 'DEPOSIT', 15000.00, 'Liquid Emergency Reserve Transfer', 15000.00);

INSERT OR IGNORE INTO transactions (id, account_id, type, amount, description, balance_after)
VALUES (7, 3, 'INTEREST', 200.50, 'Monthly Accrued Interest (4.8% APY)', 15200.50);

-- Initial Transactions for Account 4 (Traditional IRA)
INSERT OR IGNORE INTO transactions (id, account_id, type, amount, description, balance_after)
VALUES (8, 4, 'DEPOSIT', 31800.25, 'Direct 401(k) Custodial Rollover', 31800.25);
