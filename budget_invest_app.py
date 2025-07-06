import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import openai

# ✅ Set API key securely from Streamlit Cloud secrets
openai.api_key = st.secrets["openai"]["api_key"]

st.set_page_config(page_title="💸 Budget & Investment App", layout="wide")
st.title("💸 Budgeting + Investment Planner (with AI Suggestions, Tax, Investments, Warnings & Target)")

API_KEY = "ZGX1F29EUR1W6A6X"  # Example Alpha Vantage key for stock/bond data

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

# --- Fetch returns
st.sidebar.header("📡 Fetching returns...")
stock_r = get_alpha_vantage_monthly_return("SPY") or 0.01
bond_r = get_alpha_vantage_monthly_return("AGG") or 0.003
st.sidebar.write(f"Stocks monthly return: {stock_r:.2%}")
st.sidebar.write(f"Bonds monthly return: {bond_r:.2%}")

# --- Fixed returns
real_r = 0.004
crypto_r = 0.02
fd_r = 0.003

# --- Compute balances
after_tax_income = income * (1 - tax_rate / 100)
total_exp = housing + food + transport + utilities + entertainment + others
total_inv = stocks + bonds + real_estate + crypto + fixed_deposit
net_flow = after_tax_income - total_exp - total_inv

bal = 0
rows = []
for m in range(1, months + 1):
    bal += net_flow
    stock_val = stocks * ((1 + stock_r)**m - 1) / stock_r if stock_r else stocks * m
    bond_val = bonds * ((1 + bond_r)**m - 1) / bond_r if bond_r else bonds * m
    real_val = real_estate * ((1 + real_r)**m - 1) / real_r if real_r else real_estate * m
    crypto_val = crypto * ((1 + crypto_r)**m - 1) / crypto_r if crypto_r else crypto * m
    fd_val = fixed_deposit * ((1 + fd_r)**m - 1) / fd_r if fd_r else fixed_deposit * m
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

# --- Summary display
st.subheader("📋 Summary")
st.metric("Income (gross)", f"${income:,.2f}")
st.metric("Tax rate", f"{tax_rate}%")
st.metric("After tax income", f"${after_tax_income:,.2f}")
st.metric("Expenses", f"${total_exp:,.2f}")
st.metric("Investments", f"${total_inv:,.2f}")
st.metric("Net Cash Flow", f"${net_flow:,.2f}/mo")

# --- Charts
st.subheader("📈 Net Worth Growth")
fig = px.line(df, x="Month", y=["Balance", "Stocks", "Bonds", "RealEstate", "Crypto", "FixedDeposit", "NetWorth"], markers=True,
              title="Net Worth & Investments Over Time")
fig.add_hline(y=savings_target, line_dash="dash", line_color="red", annotation_text="Target")
st.plotly_chart(fig, use_container_width=True)

st.subheader("🧾 Expense Breakdown")
exp_s = pd.Series({
    "Housing": housing,
    "Food": food,
    "Transport": transport,
    "Utilities": utilities,
    "Entertainment": entertainment,
    "Others": others
})
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

# --- AI suggestions button
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
    - Projected net worth: ${df['NetWorth'].iloc[-1]}
    Please provide a friendly financial summary and advice.
    """
    with st.spinner("Generating AI summary..."):
        try:
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200
            )
            ai_suggestion = response.choices[0].message.content
            st.subheader("🤖 ChatGPT Financial Summary")
            st.write(ai_suggestion)
        except Exception as e:
            st.error(f"OpenAI API error: {e}")
