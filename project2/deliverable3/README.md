
# Persona Feedback Simulation App

A **Streamlit-based app** for generating realistic persona feedback using the OpenAI API.  
This version includes production-ready improvements such as modular design, authentication support, cloud storage, and monitoring hooks.

---

## Features

- **Persona management**: Create, edit, and simulate personas.
- **OpenAI API integration**: Generate realistic feedback automatically.
- **Database support**: Optional Supabase or SQLite backend.
- **Secure API key handling**: Avoid exposing secrets.
- **Modular codebase**: Separate app, utilities, and database logic.
- **Deployment ready**: Works on Streamlit Cloud or GitHub Codespaces.
- **Monitoring hooks**: Metrics and logging for production use.

---

## Project Structure

```
project/
│
├─ app.py                  # Main Streamlit app
├─ utils/
│  ├─ response.py          # Response generation functions
│  ├─ personas.py          # Persona management
│  └─ helpers.py           # Misc helper functions
├─ database/
│  ├─ db.py                # Database connection and queries
│  └─ models.py            # Persona data models
├─ tests/
│  ├─ test_app.py          # Unit tests
│  └─ conftest.py          # Test fixtures
├─ requirements.txt        # Python dependencies
└─ README.md               # This file
```

---

## Setup & Installation

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/persona-feedback-app.git
cd persona-feedback-app
```

2. **Create a virtual environment**

```bash
python -m venv venv
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate     # Windows
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Set your OpenAI API key**

```bash
export OPENAI_API_KEY="your_api_key_here"   # macOS/Linux
setx OPENAI_API_KEY "your_api_key_here"     # Windows
```

---

## Running the App

```bash
streamlit run app.py
```

- Open the browser link provided by Streamlit.
- Create or select personas, input features, and generate feedback.

---

## Testing

Unit tests use **pytest** and can be run with:

```bash
pytest
```

- Tests cover:
  - Response generation (small, empty, large input)
  - Persona management
  - Concurrency handling

**Tip:** You can mock OpenAI responses for offline testing.

---

## Deployment

- **Streamlit Cloud**: Push your repo and configure the secrets (API keys) in the app settings.
- **GitHub Codespaces**: Works in the dev container with all dependencies installed.
- **Optional database**: Use SQLite for local testing or Supabase for cloud storage.

---

## Contributing

1. Fork the repository.
2. Create a feature branch.
3. Commit your changes.
4. Open a pull request.

---

## License

MIT License © 2025 [Your Name]

---

## Contact

Brittany D’Erasmo – [your.email@example.com]  
GitHub: [https://github.com/yourusername](https://github.com/yourusername)
