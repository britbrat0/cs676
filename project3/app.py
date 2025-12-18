import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from agents.orchestrator import run_agent

# ---- Initialize session state ----
if "df" not in st.session_state:
    st.session_state.df = None
if "target" not in st.session_state:
    st.session_state.target = None
if "task_type" not in st.session_state:
    st.session_state.task_type = None
if "last_model" not in st.session_state:
    st.session_state.last_model = None

st.set_page_config(page_title="Agentic ML App", layout="wide")
st.title("Agentic ML App with EDA")

# ---- File upload ----
uploaded_file = st.file_uploader("Upload CSV file", type="csv")
if uploaded_file:
    st.session_state.df = pd.read_csv(uploaded_file)
    st.write("Preview of dataset:")
    st.dataframe(st.session_state.df.head())

df = st.session_state.df

# ---- Sidebar for EDA ----
if df is not None:
    st.sidebar.header("Dataset Exploration")
    eda_option = st.sidebar.selectbox(
        "Choose an action",
        [
            "None",
            "Show correlation matrix",
            "Group by column and show counts",
            "Summarize statistics",
            "Filter rows",
            "Histogram",
            "Scatter plot",
            "Boxplot",
            "Value counts",
            "Missing values summary",
            "Pairplot"
        ]
    )

    if eda_option != "None":
        numeric_cols = df.select_dtypes(include="number").columns
        categorical_cols = df.select_dtypes(include="object").columns

        if eda_option == "Show correlation matrix":
            corr = df[numeric_cols].corr()
            st.write("Correlation matrix:")
            st.dataframe(corr)
            fig, ax = plt.subplots()
            sns.heatmap(corr, annot=True, cmap="coolwarm", ax=ax)
            st.pyplot(fig)

        elif eda_option == "Group by column and show counts":
            col = st.selectbox("Select column to group by", df.columns)
            st.write(df.groupby(col).size().reset_index(name="counts"))

        elif eda_option == "Summarize statistics":
            st.write(df.describe(include="all"))

        elif eda_option == "Filter rows":
            col = st.selectbox("Select column to filter", df.columns)
            op = st.selectbox("Operator", [">", "<", ">=", "<=", "==", "!="])
            val = st.text_input("Value to compare")
            if val:
                try:
                    val_cast = float(val)
                except:
                    val_cast = val
                filtered = df.query(f"`{col}` {op} @val_cast")
                st.write(filtered)

        elif eda_option == "Histogram":
            col = st.selectbox("Select numeric column for histogram", numeric_cols)
            bins = st.slider("Number of bins", min_value=5, max_value=100, value=20)
            fig, ax = plt.subplots()
            df[col].hist(bins=bins, ax=ax)
            st.pyplot(fig)

        elif eda_option == "Scatter plot":
            x_col = st.selectbox("X-axis", numeric_cols)
            y_col = st.selectbox("Y-axis", numeric_cols)
            fig, ax = plt.subplots()
            df.plot.scatter(x=x_col, y=y_col, ax=ax)
            st.pyplot(fig)

        elif eda_option == "Boxplot":
            col = st.selectbox("Select numeric column for boxplot", numeric_cols)
            fig, ax = plt.subplots()
            sns.boxplot(y=df[col], ax=ax)
            st.pyplot(fig)

        elif eda_option == "Value counts":
            col = st.selectbox("Select column", df.columns)
            st.write(df[col].value_counts())

        elif eda_option == "Missing values summary":
            st.write(df.isnull().sum())

        elif eda_option == "Pairplot":
            if len(numeric_cols) >= 2:
                fig = sns.pairplot(df[numeric_cols])
                st.pyplot(fig)
            else:
                st.write("Need at least 2 numeric columns for pairplot")

# ---- Chat input for ML agent ----
user_input = st.text_input("Chat with the ML agent", "")
if user_input:
    response = run_agent(user_input)
    st.markdown(response)
