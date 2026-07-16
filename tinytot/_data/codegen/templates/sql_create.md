# Sql Create

## sql
```sql
-- Create a users table with common fields
CREATE TABLE IF NOT EXISTS users (
    id         SERIAL PRIMARY KEY,
    name       VARCHAR(255)        NOT NULL,
    email      VARCHAR(255) UNIQUE NOT NULL,
    age        INTEGER             CHECK (age >= 0),
    is_active  BOOLEAN             DEFAULT TRUE,
    created_at TIMESTAMP           DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP           DEFAULT CURRENT_TIMESTAMP
);

-- Add an index on email for fast lookups
CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);

-- Foreign key example (orders referencing users)
-- CREATE TABLE orders (
--     id      SERIAL PRIMARY KEY,
--     user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
--     total   NUMERIC(10, 2) NOT NULL
-- );
```
