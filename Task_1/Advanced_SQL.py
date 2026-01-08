"""
The database loan.db consists of 5 tables:
   1. customers - table containing customer data
   2. loans - table containing loan data pertaining to customers
   3. credit - table containing credit and creditscore data pertaining to customers
   4. repayments - table containing loan repayment data pertaining to customers
   5. months - table containing month name and month ID data

You are required to make use of your knowledge in SQL to query the database object (saved as loan.db) and return the requested information.
Simply fill in the vacant space wrapped in triple quotes per question (each function represents a question)

NOTE:
The database will be reset when grading each section. Any changes made to the database in the previous `SQL` section can be ignored.
Each question in this section is isolated unless it is stated that questions are linked.
Remember to clean your data

"""


def question_1():
    """
    Make use of a JOIN to find the `AverageIncome` per `CustomerClass`
    """

    qry = """
        SELECT
            cr.CustomerClass,
            AVG(TRY_CAST(TRIM(c.Income) AS DOUBLE)) AS AverageIncome
        FROM credit AS cr
        JOIN customers AS c
            USING (CustomerID)
        WHERE TRY_CAST(TRIM(c.Income) AS DOUBLE) IS NOT NULL
        GROUP BY cr.CustomerClass
        ORDER BY cr.CustomerClass
        
        """

    return qry


def question_2():
    """
    Make use of a JOIN to return a breakdown of the number of 'RejectedApplications' per 'Province'.
    Ensure consistent use of either the abbreviated or full version of each province, matching the format found in the customer table.
    """

    qry = """
    
    --1. Normalise the Region field from customers table to a consistent province name using CASE argument
    SELECT
        CASE 
            WHEN UPPER(TRIM(c.Region)) IN ('LP', 'LIMPOPO') THEN 'Limpopo'
            WHEN UPPER(TRIM(c.Region)) IN ('MP', 'MPUMALANGA') THEN 'Mpumalanga'
            WHEN UPPER(TRIM(c.Region)) IN ('GT', 'GAUTENG') THEN 'Gauteng'
            WHEN UPPER(TRIM(c.Region)) IN ('KZN', 'KWAZULU-NATAL', 'KWAZULU NATAL') THEN 'KwaZulu-Natal'
            WHEN UPPER(TRIM(c.Region)) IN ('NW', 'NORTH WEST') THEN 'NorthWest'
            WHEN UPPER(TRIM(c.Region)) IN ('EC', 'EASTERN CAPE') THEN 'EasternCape'
            WHEN UPPER(TRIM(c.Region)) IN ('WC', 'WESTERN CAPE') THEN 'WesternCape'
            WHEN UPPER(TRIM(c.Region)) IN ('NC', 'NORTHERN CAPE') THEN 'NorthernCape'
            WHEN UPPER(TRIM(c.Region)) IN ('FS', 'FREE STATE') THEN 'FreeState'
            ELSE TRIM(c.Region)
        END AS Province,
        COUNT(*) AS RejectedApplications
    FROM customers AS c

    --2. Join customers and loans table on CustomerID to link each customer to their loan applications
    
    JOIN loans AS l USING (CustomerID)
    WHERE UPPER(TRIM(l.ApprovalStatus)) = 'REJECTED'
    GROUP BY Province -- Group by normalised province name
    ORDER BY Province;
    """

    return qry


def question_3():
    """
    Making use of the `INSERT` function, create a new table called `financing` which will include the following columns:
    `CustomerID`,`Income`,`LoanAmount`,`LoanTerm`,`InterestRate`,`ApprovalStatus` and `CreditScore`

    Do not return the new table, just create it.
    """

    qry = """

        --1. Create new table 'financing' 
        CREATE TABLE IF NOT EXISTS financing (
            CustomerID INTEGER,
            Income DOUBLE,
            LoanAmount DOUBLE,
            LoanTerm INTEGER,
            InterestRate DOUBLE,
            ApprovalStatus VARCHAR,
            CreditScore INTEGER
        );

        --2. Populating the financing table by casting from the customers, loans and credit table
        INSERT INTO financing
            SELECT
                c.CustomerID,
                TRY_CAST(TRIM(c.Income) AS DOUBLE) AS Income,
                TRY_CAST(TRIM(l.LoanAmount) AS DOUBLE) AS LoanAmount,
                TRY_CAST(TRIM(l.LoanTerm) AS INTEGER) AS LoanTerm,
                TRY_CAST(TRIM(l.InterestRate) AS DOUBLE) AS InterestRate,
                TRIM(l.ApprovalStatus) AS ApprovalStatus,
                TRY_CAST(TRIM(cr.CreditScore) AS INTEGER) AS CreditScore
            FROM customers AS c
            LEFT JOIN credit AS cr USING (CustomerID) -- Join to get credit score from credit table
            LEFT JOIN loans AS l USING (CustomerID); -- Join to get loan details from loan table

        SELECT * FROM financing
    """

    return qry


# Question 4 and 5 are linked


def question_4():
    """
    Using a `CROSS JOIN` and the `months` table, create a new table called `timeline` that sumarises Repayments per customer per month.
    Columns should be: `CustomerID`, `MonthName`, `NumberOfRepayments`, `AmountTotal`.
    Repayments should only occur between 6am and 6pm London Time.
    Null values to be filled with 0.

    Hint: there should be 12x CustomerID = 1.
    """

    qry = """

    CREATE TABLE IF NOT EXISTS timeline AS --Create the timeline table if it does not exist yet

    --1. Clean Raw Repayment Data
    WITH cleaned AS (
        SELECT
            r.CustomerID,
            EXTRACT(MONTH FROM r.RepaymentDate) AS MonthID, -- Extract month number ofrom repayment date
            TRY_CAST(TRIM(r.Amount) AS DOUBLE) AS Amount,
            EXTRACT(HOUR FROM r.RepaymentDate) AS Hour24
        FROM repayments r
    ),

    --2. Filter Repayments to business hours
    filtered AS (
        SELECT
            CustomerID,
            MonthID,
            COUNT(*) AS NumberOfRepayments, -- Count repayments per customer per month
            SUM(Amount) AS AmountTotal      -- Sum repayments per customer per month
        FROM cleaned
        WHERE Hour24 BETWEEN 6 AND 18       -- Only include repayments between 6am and 6pm London time
        GROUP BY CustomerID, MonthID
    )

    --3. Use Cross Join to generate a full timeline that ensures 12 months per customer
    SELECT
        c.CustomerID,
        m.MonthName,
        COALESCE(f.NumberOfRepayments, 0) AS NumberOfRepayments, -- Replace NULL with 0 for outstanding months
        COALESCE(f.AmountTotal, 0) AS AmountTotal                -- Replace NULL with 0 for outsanding amounts
    FROM customers c
    CROSS JOIN months m 
    LEFT JOIN filtered f -- Join aggregated repayment data
           ON f.CustomerID = c.CustomerID
          AND f.MonthID    = m.MonthID
    ORDER BY c.CustomerID, m.MonthID;

    SELECT * FROM timeline
    """

    return qry


def question_5():
    """
    Make use of conditional aggregation to pivot the `timeline` table such that the columns are as follows:
    `CustomerID`, `JanuaryRepayments`, `JanuaryTotal`,...,`DecemberRepayments`, `DecemberTotal`,...etc
    MonthRepayments columns (e.g JanuaryRepayments) should be integers

    Hint: there should be 1x CustomerID = 1
    """

    qry = """

    --1. Define a common table expression 'payments' to be used for question 5 
    WITH payments AS (
    SELECT *
    FROM (
        SELECT 
            CustomerID,
            MonthName,

            -- Ensure that NumberOfRepayments is treated as an integer
            CAST(NumberOfRepayments AS INTEGER) AS NumberOfRepayments,
            AmountTotal
        FROM timeline
    )

    --2.  Pivot the data so that each MonthName becomes a set of columns
    PIVOT (

        -- Aggregate NumberOfRepayments for each month and label as Repayments
        SUM(CAST(NumberOfRepayments AS INTEGER)) AS Repayments,

        -- Aggregate AmountTotal for each month and label as Total
        SUM(CAST(AmountTotal AS INTEGER)) AS Total

        -- Define the months that need to pivot into columns (Jan - Dec)
        FOR MonthName IN (
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
            )
        )
    )

    --3. Return CustomerID and all of the pivoted monthly columns, ensuring that Repayments are integers
    SELECT CustomerID,
    
        -- Ensure that all Repayments are represented as integers by using CAST
    
        CAST(January_Repayments AS INTEGER)   AS January_Repayments,
        January_Total,
    
        CAST(February_Repayments AS INTEGER)  AS February_Repayments,
        February_Total,
    
        CAST(March_Repayments AS INTEGER)     AS March_Repayments,
        March_Total,
    
        CAST(April_Repayments AS INTEGER)     AS April_Repayments,
        April_Total,
    
        CAST(May_Repayments AS INTEGER)       AS May_Repayments,
        May_Total,
    
        CAST(June_Repayments AS INTEGER)      AS June_Repayments,
        June_Total,
    
        CAST(July_Repayments AS INTEGER)      AS July_Repayments,
        July_Total,
    
        CAST(August_Repayments AS INTEGER)    AS August_Repayments,
        August_Total,
    
        CAST(September_Repayments AS INTEGER) AS September_Repayments,
        September_Total,
    
        CAST(October_Repayments AS INTEGER)   AS October_Repayments,
        October_Total,
    
        CAST(November_Repayments AS INTEGER)  AS November_Repayments,
        November_Total,
    
        CAST(December_Repayments AS INTEGER)  AS December_Repayments,
        December_Total
        
    FROM payments
    ORDER BY CustomerID
    """

    return qry


# QUESTION 6 and 7 are linked, Do not be concerned with timezones or repayment times for these question.


def question_6():
    """
    The `customers` table was created by merging two separate tables: one containing data for male customers and the other for female customers.
    Due to an error, the data in the age columns were misaligned in both original tables, resulting in a shift of two places upwards in
    relation to the corresponding CustomerID.

    Create a table called `corrected_customers` with columns: `CustomerID`, `Age`, `CorrectedAge`, `Gender`
    Utilize a window function to correct this mistake in the new `CorrectedAge` column.
    Null values can be input manually - i.e. values that overflow should loop to the top of each gender.

    Also return a result set for this table (ie SELECT * FROM corrected_customers)
    """

    qry = """
    
    --1. Create new table corrected_customers
    
    CREATE OR REPLACE TABLE corrected_customers AS
    WITH numbered AS (
        SELECT
            CustomerID,
            Age,
            Gender,
            ROW_NUMBER() OVER (PARTITION BY Gender ORDER BY CustomerID) AS rn,
            COUNT(*)    OVER (PARTITION BY Gender) AS cnt
        FROM customers
    ),
    source AS (
        -- Same ordering and partitioning to supply ages by position
        SELECT
            Gender,
            Age,
            ROW_NUMBER() OVER (PARTITION BY Gender ORDER BY CustomerID) AS rn
        FROM customers
    )
    SELECT
        n.CustomerID,
        n.Age,
        -- For each row, take the Age from two rows ahead within the same gender,
        -- wrapping around to the first rows when we overflow the end.
        s.Age AS CorrectedAge,
        n.Gender
    FROM numbered n
    JOIN source s
      ON s.Gender = n.Gender
     AND s.rn = ((n.rn + 2 - 1) % n.cnt) + 1  -- 1-based modular arithmetic: rn -> rn+2 with wrap
    ORDER BY n.Gender, n.CustomerID;
    
    -- Return the result set
    SELECT *
    FROM corrected_customers
    ORDER BY Gender, CustomerID;
    """

    return qry


def question_7():
    """
    Create a column in corrected_customers called 'AgeCategory' that categorizes customers by age.
    Age categories should be as follows:
        - `Teen`: CorrectedAge < 20
        - `Young Adult`: 20 <= CorrectedAge < 30
        - `Adult`: 30 <= CorrectedAge < 60
        - `Pensioner`: CorrectedAge >= 60

    Make use of a windows function to assign a rank to each customer based on the total number of repayments per age group. Add this into a "Rank" column.
    The ranking should not skip numbers in the sequence, even when there are ties, i.e. 1,2,2,2,3,4 not 1,2,2,2,5,6
    Customers with no repayments should be included as 0 in the result.

    Return columns: `CustomerID`, `Age`, `CorrectedAge`, `Gender`, `AgeCategory`, `Rank`
    """

    qry = """

    -- 1. Calculate Total Repayments per Customer
    
    WITH repayments_per_customer AS (
        SELECT
            r.CustomerID,

            -- Sum all of the repayment amounts for each customer; treat NULL as 0
            CAST(SUM(COALESCE(r.Amount, 0)) AS INTEGER) AS TotalRepayments
        FROM repayments AS r
        GROUP BY r.CustomerID
    ),

    --2. Categorise Customers by CorrectedAge and join the repayment totals
    
    categorized AS (
        SELECT
            c.CustomerID,
            c.Age,
            c.CorrectedAge,
            c.Gender,

            -- Assign AgeCategory based on the given age categories
            CASE
                WHEN c.CorrectedAge IS NULL THEN NULL
                WHEN c.CorrectedAge < 20 THEN 'Teen'
                WHEN c.CorrectedAge >= 20 AND c.CorrectedAge < 30 THEN 'Young Adult'
                WHEN c.CorrectedAge >= 30 AND c.CorrectedAge < 60 THEN 'Adult'
                WHEN c.CorrectedAge >= 60 THEN 'Pensioner'
            END AS AgeCategory,

            -- Include total repayments; if no repayments exist, default to 0
            COALESCE(r.TotalRepayments, 0) AS TotalRepayments
        FROM corrected_customers AS c

        -- Apply LEFT JOIN to ensure that customers with no repayments are still included
        LEFT JOIN repayments_per_customer AS r
          ON r.CustomerID = c.CustomerID
    ),

    --3. Apply dense ranking within each AgeCategory
    ranked AS (
        SELECT
            CustomerID,
            Age,
            CorrectedAge,
            Gender,
            AgeCategory,

            -- Ranking Customers by TotalRepayments within each AgeCategory
            --DENSE_RANK ensures that there are no gaps in the ranking sequence
            
            DENSE_RANK() OVER (
                PARTITION BY AgeCategory
                ORDER BY TotalRepayments DESC
            ) AS Rank
        FROM categorized
    )

    --4. Return the final result set with the requested columns
    SELECT
        CustomerID,
        Age,
        CorrectedAge,
        Gender,
        AgeCategory,
        Rank
    FROM ranked

    --Order results
    ORDER BY Gender, AgeCategory, CustomerID;


    """

    return qry
