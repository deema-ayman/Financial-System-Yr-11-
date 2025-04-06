import streamlit as st
import datetime
import json
import pandas as pd
import hashlib

# Set page configuration
st.set_page_config(
    page_title="Year 11 Committee Financial System",
    page_icon="💰",
    layout="wide"
)

# Custom CSS for responsiveness
st.markdown(
    """
    <style>
    /* Make the main container more fluid on small screens */
    .block-container {
        padding-left: 2rem;
        padding-right: 2rem;
    }
    @media only screen and (max-width: 768px) {
        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
        /* Optionally adjust sidebar width on mobile */
        [data-testid="stSidebar"] {
            width: 200px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Password configuration with SHA256 hashing
def check_credentials(username, password, user_credentials):
    """Check if username and password match stored credentials"""
    username = username.strip().lower()
    password = password.strip()
    if username in user_credentials:
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        return hashed_password == user_credentials[username]["password_hash"]
    return False

def get_user_role(username, user_credentials):
    """Get the role for a username"""
    username = username.strip().lower()
    if username in user_credentials:
        return user_credentials[username]["role"]
    return None

# User credentials with hashed passwords
# "password" => 5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8
# "viewer"   => d35ca5051b82ffc326a3b0b6574a9a3161dee16b9478a199ee39cd803ce5b799
USER_CREDENTIALS = {
    "admin": {
        "password_hash": "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",  # "password"
        "role": "admin"
    },
    "viewer": {
        "password_hash": "d35ca5051b82ffc326a3b0b6574a9a3161dee16b9478a199ee39cd803ce5b799",  # "viewer"
        "role": "viewer"
    }
}

# Initialize session state variables if they don't exist
if 'transactions' not in st.session_state:
    st.session_state.transactions = []

if 'budget' not in st.session_state:
    st.session_state.budget = {
        "income": {
            "Fundraising Events": {"budget": 0, "actual": 0},
            "Merchandise Sales": {"budget": 0, "actual": 0},
            "Sponsorships": {"budget": 0, "actual": 0},
            "Other Income": {"budget": 0, "actual": 0}
        },
        "expenses": {
            "Event Expenses": {"budget": 0, "actual": 0},
            "Merchandise Production": {"budget": 0, "actual": 0},
            "Marketing/Promotion": {"budget": 0, "actual": 0},
            "Yearbook": {"budget": 0, "actual": 0},
            "Graduation": {"budget": 0, "actual": 0},
            "School Trips": {"budget": 0, "actual": 0},
            "Emergency Reserve": {"budget": 0, "actual": 0},
            "Other Expenses": {"budget": 0, "actual": 0}
        }
    }

if 'events' not in st.session_state:
    st.session_state.events = []

if 'fundraising' not in st.session_state:
    st.session_state.fundraising = []

# Authentication state variables
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if 'user_role' not in st.session_state:
    st.session_state.user_role = None

if 'username' not in st.session_state:
    st.session_state.username = None

# Committee members
committee_members = {
    "Chair": "TBD",
    "Deputy Chair": "TBD",
    "Treasurer": "Deema Abououf",
    "Secretary": "TBD",
    "Events Coordinator": "TBD"
}

# Authorization levels based on the matrix
auth_levels = {
    "Under 100 KD": ["Chair"],
    "Over 100 KD": ["Chair", "School Admin"],
    "New Category": ["Committee Vote"]
}

# Helper functions
def get_balance():
    total_income = sum(t["income"] for t in st.session_state.transactions)
    total_expenses = sum(t["expense"] for t in st.session_state.transactions)
    return total_income - total_expenses

def get_emergency_reserve():
    total_income = sum(t["income"] for t in st.session_state.transactions)
    return total_income * 0.15

def get_required_authorization(amount, category):
    is_new_category = True
    for section in ["income", "expenses"]:
        if category in st.session_state.budget[section]:
            is_new_category = False
            break
    if is_new_category:
        return ["Committee Vote"]
    elif float(amount) > 100:
        return auth_levels["Over 100 KD"]
    else:
        return auth_levels["Under 100 KD"]

def add_transaction(date, description, category, income=0, expense=0, authorized_by="", receipt_num="", notes=""):
    if not description or not category:
        return False, "Description and category are required"
    amount = max(income, expense)
    required_auth = get_required_authorization(amount, category)
    if authorized_by not in required_auth and "Committee Vote" not in required_auth:
        return False, f"This transaction requires authorization from: {', '.join(required_auth)}"
    transaction = {
        "date": date,
        "description": description,
        "category": category,
        "income": float(income),
        "expense": float(expense),
        "authorized_by": authorized_by,
        "receipt_num": receipt_num,
        "notes": notes,
        "timestamp": datetime.datetime.now().isoformat()
    }
    st.session_state.transactions.append(transaction)
    if income > 0:
        if category in st.session_state.budget["income"]:
            st.session_state.budget["income"][category]["actual"] += float(income)
        else:
            st.session_state.budget["income"]["Other Income"]["actual"] += float(income)
    if expense > 0:
        if category in st.session_state.budget["expenses"]:
            st.session_state.budget["expenses"][category]["actual"] += float(expense)
        else:
            st.session_state.budget["expenses"]["Other Expenses"]["actual"] += float(expense)
    return True, "Transaction added successfully"

def generate_monthly_report(month=None, year=None):
    now = datetime.datetime.now()
    month = month or now.month
    year = year or now.year
    monthly_transactions = []
    for t in st.session_state.transactions:
        try:
            t_date = datetime.datetime.fromisoformat(t["timestamp"]).date()
            if t_date.month == month and t_date.year == year:
                monthly_transactions.append(t)
        except (ValueError, KeyError):
            continue
    monthly_income = sum(t["income"] for t in monthly_transactions)
    monthly_expenses = sum(t["expense"] for t in monthly_transactions)
    report = {
        "month": month,
        "year": year,
        "total_income": monthly_income,
        "total_expenses": monthly_expenses,
        "net": monthly_income - monthly_expenses,
        "transactions": monthly_transactions,
        "current_balance": get_balance(),
        "emergency_reserve": get_emergency_reserve(),
        "available_funds": get_balance() - get_emergency_reserve()
    }
    return report

def create_event_budget(event_name, date, location, coordinator, projected_income=0, projected_expenses=0):
    event = {
        "name": event_name,
        "date": date,
        "location": location,
        "coordinator": coordinator,
        "projected_income": float(projected_income),
        "projected_expenses": float(projected_expenses),
        "actual_income": 0,
        "actual_expenses": 0,
        "income_sources": [],
        "expense_items": [],
        "status": "Planning"
    }
    st.session_state.events.append(event)
    return True, "Event budget created successfully"

def add_fundraising_initiative(name, dates, coordinator, goal_amount):
    initiative = {
        "name": name,
        "dates": dates,
        "coordinator": coordinator,
        "goal_amount": float(goal_amount),
        "actual_raised": 0,
        "expenses": 0,
        "net_proceeds": 0,
        "status": "Planning"
    }
    st.session_state.fundraising.append(initiative)
    return True, "Fundraising initiative added successfully"

# Login screen function
def show_login():
    st.title("Year 11 Committee Financial System")
    st.subheader("Login")
    with st.form("login_form"):
        username = st.text_input("Username").strip().lower()
        password = st.text_input("Password", type="password").strip()
        submitted = st.form_submit_button("Login")
        if submitted:
            if check_credentials(username, password, USER_CREDENTIALS):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.session_state.user_role = get_user_role(username, USER_CREDENTIALS)
                st.success(f"Login successful! Welcome {username}.")
                st.rerun()
            else:
                st.error("Incorrect username or password. Please try again.")
    st.markdown("---")
    st.markdown("""
    ### Access Levels:
    - **Admin:** Full access to all features
    - **Viewer:** View dashboard and generate reports only

    Please enter your username and password to login.

    Default accounts:
    - Username: admin (full access)
    - Username: viewer (view-only access)
    """)

# Dashboard function
def show_dashboard():
    st.header("Financial Dashboard")
    col1, col2, col3 = st.columns(3)
    balance = get_balance()
    reserve = get_emergency_reserve()
    available = balance - reserve
    with col1:
        st.metric("Current Balance", f"KD {balance:.2f}")
    with col2:
        st.metric("Emergency Reserve (15%)", f"KD {reserve:.2f}")
    with col3:
        st.metric("Available Funds", f"KD {available:.2f}")
    st.subheader("Recent Transactions")
    if st.session_state.transactions:
        transactions_df = pd.DataFrame(st.session_state.transactions)
        if "timestamp" in transactions_df.columns:
            transactions_df = transactions_df.sort_values(by="timestamp", ascending=False)
        recent_transactions = transactions_df.head(5)
        display_columns = [col for col in ["date", "description", "category", "income", "expense", "authorized_by"]
                           if col in recent_transactions.columns]
        st.dataframe(recent_transactions[display_columns], use_container_width=True)
    else:
        st.info("No transactions recorded yet.")
    st.subheader("Budget Overview")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Income: Budget vs. Actual**")
        income_data = []
        for category, values in st.session_state.budget["income"].items():
            income_data.append({
                "Category": category,
                "Budget": f"KD {values['budget']:.2f}",
                "Actual": f"KD {values['actual']:.2f}",
                "Variance": f"KD {values['actual'] - values['budget']:.2f}"
            })
        if income_data:
            income_df = pd.DataFrame(income_data)
            st.dataframe(income_df, use_container_width=True)
    with col2:
        st.write("**Expenses: Budget vs. Actual**")
        expense_data = []
        for category, values in st.session_state.budget["expenses"].items():
            expense_data.append({
                "Category": category,
                "Budget": f"KD {values['budget']:.2f}",
                "Actual": f"KD {values['actual']:.2f}",
                "Variance": f"KD {values['actual'] - values['budget']:.2f}"
            })
        if expense_data:
            expense_df = pd.DataFrame(expense_data)
            st.dataframe(expense_df, use_container_width=True)
    if st.session_state.user_role == "admin":
        st.subheader("Quick Actions")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Add Transaction", use_container_width=True):
                st.session_state.page = "transactions"
        with col2:
            if st.button("Generate Report", use_container_width=True):
                st.session_state.page = "reports"
        with col3:
            if st.button("Manage Budget", use_container_width=True):
                st.session_state.page = "budget"
    else:
        st.subheader("Quick Actions")
        if st.button("Generate Report", use_container_width=True):
            st.session_state.page = "reports"

# (Other functions – show_transactions, show_budget, show_events, show_reports, show_fundraising, save_data, load_data, logout, show_settings – remain unchanged)
# For brevity, please refer to your full code above which remains the same except for the added CSS and adjustments in login.

# Main app
def main():
    if not st.session_state.authenticated:
        show_login()
        return
    st.sidebar.title("Year 11 Committee")
    st.sidebar.subheader("Financial Management System")
    st.sidebar.info(f"Logged in as: {st.session_state.username.upper()} ({st.session_state.user_role})")
    if st.sidebar.button("Logout"):
        logout()
    if 'page' not in st.session_state:
        st.session_state.page = 'dashboard'
    if st.session_state.user_role == "admin":
        page = st.sidebar.radio("Navigation", 
                               ["Dashboard", "Transactions", "Budget", "Events", 
                                "Fundraising", "Reports", "Settings"],
                               index=["dashboard", "transactions", "budget", "events", 
                                     "fundraising", "reports", "settings"].index(st.session_state.page))
    else:
        page = st.sidebar.radio("Navigation", 
                               ["Dashboard", "Reports"],
                               index=["dashboard", "reports"].index(st.session_state.page)
                               if st.session_state.page in ["dashboard", "reports"] else 0)
    st.session_state.page = page.lower()
    if st.session_state.page == 'dashboard':
        show_dashboard()
    elif st.session_state.page == 'reports':
        show_reports()
    elif st.session_state.user_role == "admin":
        if st.session_state.page == 'transactions':
            show_transactions()
        elif st.session_state.page == 'budget':
            show_budget()
        elif st.session_state.page == 'events':
            show_events()
        elif st.session_state.page == 'fundraising':
            show_fundraising()
        elif st.session_state.page == 'settings':
            show_settings()
    st.sidebar.markdown("---")
    st.sidebar.info(
        "Developed by Deema Abououf\n\n"
        "Treasurer/Finance Manager\n"
        "Year 11 Committee"
    )

if __name__ == '__main__':
    main()
