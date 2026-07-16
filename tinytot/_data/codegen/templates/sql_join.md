# Sql Join

## sql
```sql
-- INNER JOIN: only rows with matches in both tables
SELECT u.id, u.name, o.order_date, o.total
FROM users u
INNER JOIN orders o ON u.id = o.user_id
WHERE o.total > 100
ORDER BY o.order_date DESC;

-- LEFT JOIN: all users, with orders if they exist
SELECT u.name, COUNT(o.id) AS order_count
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.id, u.name;

-- Self-join: find employees and their managers
SELECT e.name AS employee, m.name AS manager
FROM employees e
LEFT JOIN employees m ON e.manager_id = m.id;
```
