# Sql Insert

## sql
```sql
-- Insert a single row
INSERT INTO users (name, email, age, created_at)
VALUES ('Alice', 'alice@example.com', 30, NOW());

-- Insert multiple rows
INSERT INTO users (name, email, age)
VALUES
    ('Bob',   'bob@example.com',   25),
    ('Carol', 'carol@example.com', 28),
    ('Dave',  'dave@example.com',  35);

-- Insert from SELECT
INSERT INTO users_archive
SELECT * FROM users
WHERE created_at < '2023-01-01';
```
