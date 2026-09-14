-- =============================================
-- Cold-Chain Logistics AI Assistant
-- Database Setup
-- =============================================

-- Create database
IF DB_ID('ColdChainLogistics') IS NULL
BEGIN
    CREATE DATABASE ColdChainLogistics;
END
GO

-- Switch to the project database
USE ColdChainLogistics;
GO

-- Create application schema
IF NOT EXISTS (
    SELECT 1
    FROM sys.schemas
    WHERE name = 'FDE_VIEWS'
)
BEGIN
    EXEC('CREATE SCHEMA FDE_VIEWS');
END
GO

-- Verify
SELECT
    DB_NAME() AS CurrentDatabase,
    SCHEMA_NAME(schema_id) AS SchemaName
FROM sys.schemas
WHERE name = 'FDE_VIEWS';
GO