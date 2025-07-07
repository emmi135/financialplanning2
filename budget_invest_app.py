import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import google.generativeai as genai

# ✅ Set Gemini API key securely
genai.configure(api_key=st.secrets["gemini"]["api_key"])

st.set_page_config(page_title="💸 Budget & Investment App", layout="wide")
st.title("💸 Budgeting + Investment Planner (Detailed Warnings + AI Suggestions)")

API_KEY = "ZGX1F29EUR1W6A6X"  # Replace with your Alpha Vantage key

def get_alpha_vantage_monthly_return(symbol):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_MONTHLY_ADJUSTED&symbol={symbol}&apikey={API_KEY}"
    r = requests.get(url)
    if r.status_code != 200:
        return None
    data = r.json()
    ts = data.get("Monthly Adjusted Time Series", {})
    closes = [float(v["5. adjusted close"]) for v in ts.values()]
    if len(closes) < 2:
        return None
    monthly_return = (closes[0] - closes[1]) / closes[1]
    return monthly_return

# --- Inputs
st.sidebar.header("📊 Monthly Income")
income = st.sidebar.number_input("Monthly income (before tax, $)", min_value=0.0, value=5000.0, step=100.0)
tax_rate = st.sidebar.slider("Tax rate (%)", 0, 50, 20)

st.sidebar.header("📌 Expenses")
housing = st.sidebar.number_input("Housing / Rent ($)", 0.0, 5000.0, 1200.0, 50.0)
food = st.sidebar.number_input("Food / Groceries ($)", 0.0, 5000.0, 500.0, 50.0)
transport = st.sidebar.number_input("Transport ($)", 0.0, 5000.0, 300.0, 50.0)
utilities = st.sidebar.number_input("Utilities ($)", 0.0, 5000.0, 200.0, 50.0)
entertainment = st.sidebar.number_input("Entertainment ($)", 0.0, 5000.0, 200.0, 50.0)
others = st.sidebar.number_input("Other expenses ($)", 0.0, 5000.0, 200.0, 50.0)

st.sidebar.header("📈 Investments")
stocks = st.sidebar.number_input("Stocks investment ($)", 0.0, 5000.0, 500.0, 100.0)
bonds = st.sidebar.number_input("Bonds investment ($)", 0.0, 5000.0, 300.0, 100.0)
real_estate = st.sidebar.number_input("Real estate ($)", 0.0, 5000.0, 0.0, 100.0)
crypto = st.sidebar.number_input("Crypto ($)", 0.0, 5000.0, 0.0, 100.0)
fixed_deposit = st.sidebar.number_input("Fixed deposit ($)", 0.0, 5000.0, 0.0, 100.0)

months = st.sidebar.slider("Projection period (months)", 1, 60, 12)
savings_target = st.sidebar.number_input("Savings target at end of period ($)", 0.0, 1_000_000.0, 10000.0, 500.0)

# --- Returns
stock_r = get_alpha_vantage_monthly_return("SPY") or 0.01
bond_r = get_alpha_vantage_monthly_return("AGG") or 0.003
real_r = 0.004
crypto_r = 0.02
fd_r = 0.003

# --- Calculations
after_tax_income = income * (1 - tax_rate / 100)
total_exp = housing + food + transport + utilities + entertainment + others
total_inv = stocks + bonds + real_estate + crypto + fixed_deposit
net_flow = after_tax_income - total_exp - total_inv

bal = 0
rows = []
for m in range(1, months + 1):
    bal += net_flow
    stock_val = stocks * ((1 + stock_r)**m - 1) / stock_r
    bond_val = bonds * ((1 + bond_r)**m - 1) / bond_r
    real_val = real_estate * ((1 + real_r)**m - 1) / real_r
    crypto_val = crypto * ((1 + crypto_r)**m - 1) / crypto_r
    fd_val = fixed_deposit * ((1 + fd_r)**m - 1) / fd_r
    net_worth = bal + stock_val + bond_val + real_val + crypto_val + fd_val
    rows.append({
        "Month": m,
        "Balance": bal,
        "Stocks": stock_val,
        "Bonds": bond_val,
        "RealEstate": real_val,
        "Crypto": crypto_val,
        "FixedDeposit": fd_val,
        "NetWorth": net_worth
    })
df = pd.DataFrame(rows)

# --- Summary
st.subheader("📋 Summary")
st.metric("Income (gross)", f"${income:,.2f}")
st.metric("Tax rate", f"{tax_rate}%")
st.metric("After tax income", f"${after_tax_income:,.2f}")
st.metric("Expenses", f"${total_exp:,.2f}")
st.metric("Investments", f"${total_inv:,.2f}")
st.metric("Net Cash Flow", f"${net_flow:,.2f}/mo")

# --- Overall Expense Warning
expense_ratio = total_exp / after_tax_income if after_tax_income > 0 else 0
if expense_ratio > 0.7:
    st.warning(f"⚠️ Your expenses are {expense_ratio:.0%} of after-tax income. Consider reducing discretionary spending! 😟")
else:
    st.success(f"✅ Your expenses are {expense_ratio:.0%} of after-tax income. Good job managing your costs! 😊")

# --- Detailed expense category warnings
exp_categories = {
    "Housing": housing,
    "Food": food,
    "Transport": transport,
    "Utilities": utilities,
    "Entertainment": entertainment,
    "Others": others
}

for name, amount in exp_categories.items():
    if after_tax_income > 0:
        pct = amount / after_tax_income
        if pct > 0.3:
            st.warning(f"⚠️ {name} is {pct:.0%} of your after-tax income. Consider reducing!")
        elif pct > 0.2:
            st.info(f"ℹ️ {name} is {pct:.0%} of your after-tax income. Monitor this category.")

# --- Investment balance check
if stocks + crypto > (bonds + fixed_deposit + real_estate) * 2:
    st.warning("⚠️ Your portfolio leans heavily toward high-risk investments (stocks + crypto). Consider balancing with safer assets.")
elif bonds + fixed_deposit + real_estate > (stocks + crypto) * 2:
    st.info("ℹ️ Your portfolio is very conservative. Consider adding growth-oriented investments for better returns.")
else:
    st.success("✅ Your investment mix looks reasonably balanced!")

# --- Target check
final_net_worth = df['NetWorth'].iloc[-1]
if final_net_worth >= savings_target:
    st.success(f"🎯 Target achieved! Final net worth: ${final_net_worth:,.2f} 😊")
else:
    st.warning(f"⚠ Below target. Final net worth: ${final_net_worth:,.2f} 😟")

# --- Charts
st.subheader("📈 Net Worth Growth")
fig = px.line(df, x="Month", y=["Balance", "Stocks", "Bonds", "RealEstate", "Crypto", "FixedDeposit", "NetWorth"], markers=True,
              title="Net Worth & Investments Over Time")
fig.add_hline(y=savings_target, line_dash="dash", line_color="red", annotation_text="Target")
st.plotly_chart(fig, use_container_width=True)

st.subheader("🧾 Expense Breakdown")
exp_s = pd.Series(exp_categories)
st.plotly_chart(px.pie(names=exp_s.index, values=exp_s.values, title="Expense Breakdown"), use_container_width=True)

st.subheader("💼 Investment Breakdown")
inv_s = pd.Series({
    "Stocks": stocks,
    "Bonds": bonds,
    "RealEstate": real_estate,
    "Crypto": crypto,
    "FixedDeposit": fixed_deposit
})
st.plotly_chart(px.pie(names=inv_s.index, values=inv_s.values, title="Investment Breakdown"), use_container_width=True)

# --- AI suggestions using Gemini
if st.button("Generate AI Financial Suggestions"):
    prompt = f"""
    I have the following financial data:
    - Gross income: ${income}
    - Tax rate: {tax_rate}%
    - After-tax income: ${after_tax_income}
    - Expenses: ${total_exp}
    - Investments: ${total_inv}
    - Net cash flow: ${net_flow}/mo
    - Savings target: ${savings_target}
    - Projected net worth: ${final_net_worth}
    Please provide advice on whether expenses are too high, investments are balanced, and how to reach my target.
    """
    with st.spinner("Generating AI summary..."):
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            st.subheader("🤖 Gemini Financial Summary")
            st.write(response.text)
        except Exception as e:
            st.error(f"Gemini API error: {e}")
