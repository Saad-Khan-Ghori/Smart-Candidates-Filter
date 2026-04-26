-- Default admin (development only). Login: admin@ems.local / admin123
-- Run after 02_seed.sql. Re-run safe: uses email uniqueness.

INSERT INTO Users (email, password_hash, full_name, role)
SELECT 'admin@ems.local', 'scrypt:32768:8:1$rXexmEZCDp9D0ZnB$bfa0cce7b69392950ba7658934eb9672c875c4522c76f112c26e4c616db2495c0572f4efc05fb8f67a3ead80089d2464ce852c2049bbb8d72bf83182b85e5ce6', 'System Admin', 'admin'
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM Users WHERE email = 'admin@ems.local');
