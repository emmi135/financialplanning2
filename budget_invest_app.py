import streamlit as st
import pandas as pd
import plotly.express as px
import requests

st.set_page_config(page_title="💸 Budget & Investment App", layout="wide")
st.title("💸 Budgeting + Investment Planner (with Tax, Warnings & Savings Target)")

API_KEY = "ZGX1F29EUR1W6A6X"

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

months = st.sidebar.slider("Projection period (months)", 1, 60, 12)
savings_target = st.sidebar.number_input("Savings target at end of period ($)", 0.0, 1_000_000.0, 10000.0, 500.0)

# --- Fetch returns
st.sidebar.header("📡 Fetching returns...")
stock_r = get_alpha_vantage_monthly_return("SPY") or 0.01
bond_r = get_alpha_vantage_monthly_return("AGG") or 0.003
st.sidebar.write(f"Stocks monthly return: {stock_r:.2%}")
st.sidebar.write(f"Bonds monthly return: {bond_r:.2%}")

# --- Compute
after_tax_income = income * (1 - tax_rate / 100)
total_exp = housing + food + transport + utilities + entertainment + others
total_inv = stocks + bonds
net_flow = after_tax_income - total_exp - total_inv

bal = 0
rows = []
for m in range(1, months + 1):
    bal += net_flow
    stock_val = stocks * ((1 + stock_r)**m - 1) / stock_r if stock_r else stocks * m
    bond_val = bonds * ((1 + bond_r)**m - 1) / bond_r if bond_r else bonds * m
    net_worth = bal + stock_val + bond_val
    rows.append({
        "Month": m,
        "Balance": bal,
        "Stocks": stock_val,
        "Bonds": bond_val,
        "NetWorth": net_worth
    })
df = pd.DataFrame(rows)

# --- Display summary
st.subheader("📋 Summary")
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Income (gross)", f"${income:,.2f}")
col2.metric("Tax rate", f"{tax_rate}%")
col3.metric("After tax income", f"${after_tax_income:,.2f}")
col4.metric("Expenses", f"${total_exp:,.2f}")
col5.metric("Investments", f"${total_inv:,.2f}")
st.metric("Net Cash Flow", f"${net_flow:,.2f}/mo")

# --- Expense warnings
expense_warnings = []
if housing > 0.4 * after_tax_income:
    expense_warnings.append("🏠 Housing costs exceed 40% of your after-tax income.")
if food > 0.3 * after_tax_income:
    expense_warnings.append("🍽 Food costs exceed 30% of your after-tax income.")
if entertainment > 0.1 * after_tax_income:
    expense_warnings.append("🎮 Entertainment costs exceed 10% of your after-tax income.")

if expense_warnings:
    st.subheader("⚠ Expense Warnings")
    for warn in expense_warnings:
        st.warning(warn)
else:
    st.success("✅ Your expenses look balanced!")

# --- Investment mix warnings
inv_warnings = []
if total_inv > 0:
    stock_pct = stocks / total_inv
    bond_pct = bonds / total_inv

    if stock_pct > 0.8:
        inv_warnings.append("📈 Portfolio heavily weighted toward stocks (>80%). Consider diversifying.")
    if bond_pct > 0.8:
        inv_warnings.append("💵 Portfolio heavily weighted toward bonds (>80%). Consider balancing.")

if inv_warnings:
    st.subheader("⚠ Investment Mix Warnings")
    for warn in inv_warnings:
        st.warning(warn)
else:
    st.success("✅ Your investment portfolio looks balanced!")

# --- Emoticon for net cash flow
if net_flow > 0:
    st.image("https://i.imgur.com/3GvwNBf.png", width=100, caption="✅ You're saving money!")
else:
    st.image("https://i.imgur.com/8z9uX5j.png", width=100, caption="⚠ You're overspending!")

# --- Savings target check with colored emote box
st.subheader("🎯 Savings Target Check")
final_net = df["NetWorth"].iloc[-1]
gap = savings_target - final_net

st.write(f"Target: ${savings_target:,.2f}")
st.write(f"Projected Net Worth: ${final_net:,.2f}")

if gap > 0:
    st.markdown(
        f"""
        <div style="border: 3px solid red; padding:10px; display: inline-block; border-radius:10px;">
        <img src="https://i.imgur.com/8z9uX5j.png" width="80"><br>
        <b style="color:red;">⚠ You are ${gap:,.2f} below your target.</b>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.markdown(
        f"""
        <div style="border: 3px solid green; padding:10px; display: inline-block; border-radius:10px;">
        <img src="https://i.imgur.com/3GvwNBf.png" width="80"><br>
        <b style="color:green;">✅ You will exceed your target by ${-gap:,.2f}!</b>
        </div>
        """,
        unsafe_allow_html=True
    )

# --- Charts
st.subheader("📈 Net Worth Growth")
fig = px.line(df, x="Month", y=["Balance", "Stocks", "Bonds", "NetWorth"], markers=True,
              title="Balance + Investments + Net Worth Growth")
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
    "Bonds": bonds
})
st.plotly_chart(px.pie(names=inv_s.index, values=inv_s.values, title="Investment Breakdown"), use_container_width=True)
