-- Initialize the RFQ Platform database
CREATE DATABASE rfq_platform;
CREATE USER rfq_user WITH ENCRYPTED PASSWORD 'rfq_password';
GRANT ALL PRIVILEGES ON DATABASE rfq_platform TO rfq_user;