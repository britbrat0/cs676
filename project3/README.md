# Agentic ML App (Streamlit)

An interactive **agentic AI web application** built with **Streamlit**, **scikit-learn**, and **OpenAI**, allowing users to upload datasets, explore them, train machine learning models, and interact with an AI assistant that **executes actions instead of just giving code**.

This app separates **ML tools** (deterministic execution) from an **AI chat assistant** (guidance and explanations), resulting in a fast, user-friendly workflow.

---

## 🚀 Features

### 📁 Dataset Upload
- Upload CSV datasets
- Preview the first rows of the data
- Automatically detect columns and data types

### 📊 Exploratory Data Analysis (EDA)
- Summary statistics
- Correlation matrix
- Histograms for numeric columns
- Scatter plots between numeric variables
- Group-by counts for categorical columns

### 🤖 ML Tools (UI-driven)
- Select a target column from a dropdown
- Automatically infer task type (classification or regression)
- Choose from recommended models
- Train models with one click
- View evaluation metrics (R², accuracy, etc.)
- Compare multiple models

### 🧠 Agentic AI Chat Assistant
- Understands the uploaded dataset context
- Can:
  - Train models
  - Compare models
  - Run EDA actions
  - Explain results and metrics
- Executes **real ML functions** (not just code suggestions)
- Falls back to LLM explanations only when needed
- Optimized for speed using command routing

---

## 🏗 Project Structure

```
project/
│
├── app.py
├── agents/
│   ├── orchestrator.py
│
├── tools/
│   ├── data_tools.py
│   ├── model_tools.py
│   └── training_tools.py
│
├── utils/
│   └── state.py
│
├── requirements.txt
└── README.md
```

---

## 🧰 Tech Stack

- Python 3.10+
- Streamlit
- pandas / numpy
- scikit-learn
- matplotlib
- OpenAI API

---

## 🔑 Environment Setup

```bash
pip install -r requirements.txt
export OPENAI_API_KEY="your_api_key_here"
```

(Streamlit Cloud: set this as a Secrets variable.)

---

## ▶️ Run the App

```bash
streamlit run app.py
```

---

## 🧠 How the Agent Works

The AI assistant uses a **two-stage decision system**:

1. **Command Routing**
   - Executes deterministic ML and EDA actions directly (no LLM call)

2. **LLM Reasoning**
   - Used only for explanations and guidance

This ensures fast responses, low API cost, and true agentic behavior.

---

## 📈 Future Enhancements
- Hyperparameter tuning UI
- Model persistence
- Feature importance visualization
- AutoML support
