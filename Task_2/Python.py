import os

import numpy as np
import pandas as pd

"""
To answer the following questions, make use of datasets: 
    'scheduled_loan_repayments.csv'
    'actual_loan_repayments.csv'
These files are located in the 'data' folder. 

'scheduled_loan_repayments.csv' contains the expected monthly payments for each loan. These values are constant regardless of what is actually paid.
'actual_loan_repayments.csv' contains the actual amount paid to each loan for each month.

All loans have a loan term of 2 years with an annual interest rate of 10%. Repayments are scheduled monthly.
A type 1 default occurs on a loan when any scheduled monthly repayment is not met in full.
A type 2 default occurs on a loan when more than 15% of the expected total payments are unpaid for the year.

Note: Do not round any final answers.

"""


def calculate_df_balances(df_scheduled, df_actual):
    """
    This is a utility function that creates a merged dataframe that will be used in the following questions.
    This function will not be graded, do not make changes to it.

    Args:
        df_scheduled (DataFrame): Dataframe created from the 'scheduled_loan_repayments.csv' dataset
        df_actual (DataFrame): Dataframe created from the 'actual_loan_repayments.csv' dataset

    Returns:
        DataFrame: A merged Dataframe with additional calculated columns to help with the following questions.

    """

    df_merged = pd.merge(df_actual, df_scheduled)

    def calculate_balance(group):
        r_monthly = 0.1 / 12
        group = group.sort_values("Month")
        balances = []
        interest_payments = []
        loan_start_balances = []
        for index, row in group.iterrows():
            if balances:
                interest_payment = balances[-1] * r_monthly
                balance_with_interest = balances[-1] + interest_payment
            else:
                interest_payment = row["LoanAmount"] * r_monthly
                balance_with_interest = row["LoanAmount"] + interest_payment
                loan_start_balances.append(row["LoanAmount"])

            new_balance = balance_with_interest - row["ActualRepayment"]
            interest_payments.append(interest_payment)

            new_balance = max(0, new_balance)
            balances.append(new_balance)

        loan_start_balances.extend(balances)
        loan_start_balances.pop()
        group["LoanBalanceStart"] = loan_start_balances
        group["LoanBalanceEnd"] = balances
        group["InterestPayment"] = interest_payments
        return group

    df_balances = (
        df_merged.groupby("LoanID", as_index=False)
        .apply(calculate_balance)
        .reset_index(drop=True)
    )

    df_balances["LoanBalanceEnd"] = df_balances["LoanBalanceEnd"].round(2)
    df_balances["InterestPayment"] = df_balances["InterestPayment"].round(2)
    df_balances["LoanBalanceStart"] = df_balances["LoanBalanceStart"].round(2)

    return df_balances


# Do not edit these directories
root = os.getcwd()

if "Task_2" in root:
    df_scheduled = pd.read_csv("data/scheduled_loan_repayments.csv")
    df_actual = pd.read_csv("data/actual_loan_repayments.csv")
else:
    df_scheduled = pd.read_csv("Task_2/data/scheduled_loan_repayments.csv")
    df_actual = pd.read_csv("Task_2/data/actual_loan_repayments.csv")

df_balances = calculate_df_balances(df_scheduled, df_actual)


def question_1(df_balances):
    """
    Calculate the percent of loans that defaulted as per the type 1 default definition.

    Args:
        df_balances (DataFrame): Dataframe created from the 'calculate_df_balances()' function

    Returns:
        float: The percentage of type 1 defaulted loans (ie 50.0 not 0.5)

    """
    # 1. Flag each loan payments that were missed/underpaid i.e. TRUE if monthly payment is missed/underpaid
    df_balances["missed"] = df_balances["ActualRepayment"] < df_balances["ScheduledRepayment"]

    # 2. Group each loan by loan ID to check if any unpaid payments per loan exist
    loan_default_flag = df_balances.groupby("LoanID")["missed"].any() # If True the loan defaulted if False the loan is clean

    # 3. Convert boolean flag into percentage
    default_rate_percent = loan_default_flag.mean() * 100
    
    return default_rate_percent

def question_2(df_scheduled, df_balances):
    """
    Calculate the percent of loans that defaulted as per the type 2 default definition

    Args:
        df_balances (DataFrame): Dataframe created from the 'calculate_df_balances()' function
        df_scheduled (DataFrame): Dataframe created from the 'scheduled_loan_repayments.csv' dataset

    Returns:
        float: The percentage of type 2 defaulted loans (ie 50.0 not 0.5)

    """
    # 1. Calcualtion of the Scheduled yearly payments (monthly payment * 12)
    scheduled_yearly = df_scheduled.set_index("LoanID")["ScheduledRepayment"] * 12
    
    # 2. Calcualtion of the Actual yearly payments (monthly payment * 12)
    actual_yearly = df_balances.groupby("LoanID")["ActualRepayment"].sum()
    
    # 3. Calculate the amount that was not paid for the year
    unpaid_amount = scheduled_yearly - actual_yearly

    # 4. Apply Type 2 Loan Default Rule - If more than 15% of expected yearly payments are unpaid it returns TRUE
    # unpaid_amount > 15% * expected_yearly - Generate a TRUE/FALSE boolean
    type2_default = unpaid_amount > (0.15 * scheduled_yearly)

    # 5. Compute the percentage of defaulted loans (Convert the boolean to a percentage)
    default_rate_percent = type2_default.mean() * 100

    return default_rate_percent


def question_3(df_balances):
    """
    Calculate the anualized portfolio CPR (As a %) from the geometric mean SMM.
    SMM is calculated as: (Unscheduled Principal)/(Start of Month Loan Balance)
    SMM_mean is calculated as (∏(1+SMM))^(1/12) - 1
    CPR is calcualted as: 1 - (1- SMM_mean)^12

    Args:
        df_balances (DataFrame): Dataframe created from the 'calculate_df_balances()' function

    Returns:
        float: The anualized CPR of the loan portfolio as a percent.

    """
    # Create alias for df_balances
    df = df_balances.copy()

    # 1. Calculate the total pricipal paid in each month
    df["PrincipalPaid"] = df["LoanBalanceStart"] - df["LoanBalanceEnd"]

    # 2. Calcualte the scheduled principal for each month
    df["ScheduledPrincipal"] = df["ScheduledRepayment"] - df["InterestPayment"]

    # 3. Calculate the unscheduled principal ( Excess principal paid above the scheduled principal)
    df["UnscheduledPrincipal"] = (df["PrincipalPaid"] - df["ScheduledPrincipal"]).clip(lower=0)

    # 4. Filter out months where the loan had no balance
    df = df[df["LoanBalanceStart"] > 0]

    # 5. Calcualte the monthly SMM for each loan 
    df["SMM"] = df["UnscheduledPrincipal"] / df["LoanBalanceStart"] 

    # 6. Calculate the SMM mean over all loan-months
    SMM_series = df["SMM"].dropna() #dropna ensures that only valid SMM values are considered

    if SMM_series.empty:
        return 0.0
        
    SMM_mean = ((1 + SMM_series).prod() ** (1/12)) - 1 #Formual given as (Π(1 + SMM) )^(1/12) – 1

    # 7. Calculate annualised CPR by using SMM_Mean
    CPR = 1 - (1 - SMM_mean)**12
    cpr_percent= CPR * 100
    
    return cpr_percent
    
print(question_3(df_balances))

def question_4(df_balances):
    """
    Calculate the predicted total loss for the second year in the loan term.
    Use the equation: probability_of_default * total_loan_balance * (1 - recovery_rate).
    The probability_of_default value must be taken from either your question_1 or question_2 answer.
    Decide between the two answers based on which default definition you believe to be the more useful metric.
    Assume a recovery rate of 80%

    Args:
        df_balances (DataFrame): Dataframe created from the 'calculate_df_balances()' function

    Returns:
        float: The predicted total loss for the second year in the loan term.

    """
    
    # 1. Calculate the expected yearly payment (ScheduledRepayment * 12)
    scheduled_yearly = (df_balances.groupby("LoanID")["ScheduledRepayment"].first() * 12)

    #2. Calculate the actual payments for Year 1 per loan id (Months 1–12)
    actual_yearly = (df_balances[df_balances["Month"] <= 12].groupby("LoanID")["ActualRepayment"].sum())

    #3. Calcualte the unpaid loan amount for the year
    unpaid = scheduled_yearly - actual_yearly

    #4. Use type 2 default as the probability of default
    type2_defaults = unpaid > (0.15 * scheduled_yearly) #Apply Type 2 default rate as per question 2
    probability_of_default = type2_defaults.mean()  # not percent

    #5 .Calculate the Total loan balance entering Year 2
    year2_balances = df_balances[df_balances["Month"] == 13]["LoanBalanceStart"]
    total_loan_balance = year2_balances.sum()

    #6. Loss calculation
    recovery_rate = 0.80
    total_loss = probability_of_default * total_loan_balance * (1 - recovery_rate)

    return total_loss




