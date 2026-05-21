-- Auto Generated (Do not modify) 79EF4C9322B6237939712C91540E41FADC3E67C27AEAC0B9C8EC77759F8C5FB4
CREATE VIEW dbo.vw_DimDate AS
SELECT 
    date_key,
    full_date,
    year,
    quarter,
    month,
    month_name,
    day,
    day_of_week,
    day_name,
    week_of_year,
    is_weekend
FROM [LH_Gold].[dbo].[dimdate];