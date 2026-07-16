# Sql Select

## sql
```sql
-- Select all users where age > 30
SELECT *
FROM users
WHERE age > 30;

-- Select specific columns with ordering
SELECT id, name, email, age
FROM users
WHERE age > 30
ORDER BY age DESC
LIMIT 100;

-- Count matching rows
SELECT COUNT(*) AS total
FROM users
WHERE age > 30;
```
