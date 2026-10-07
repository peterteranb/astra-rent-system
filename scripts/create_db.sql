-- Usage: psql -U postgres -h localhost -v db_password=YOUR_PASSWORD -f scripts/create_db.sql
CREATE USER astra WITH PASSWORD :'db_password';
ALTER USER astra CREATEDB;
CREATE DATABASE astra_rent OWNER astra;