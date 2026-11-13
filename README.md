# 🚀 SentiAI Pro - AI-Based Sentiment Analysis Web Application

A full-stack, enterprise-grade AI-powered Sentiment Analysis Web Application built with **Python 3**, **Flask**, **Natural Language Processing (NLP)**, **Hugging Face Transformers**, **NLTK**, **MongoDB / PyMongo**, and **Chart.js**.

The system automatically parses and classifies customer reviews, social feedback, and text streams into **Positive**, **Negative**, or **Neutral** sentiment categories with calibrated confidence scores, and presents rich interactive visual reports.

---

## 🌟 Key Features

- **Multi-Class Sentiment Classification**: Classifies text into 3 distinct classes (**Positive**, **Negative**, **Neutral**) with confidence percentages and probability breakdowns.
- **Dual-Engine AI Pipeline**:
  - **Hugging Face Transformers**: Deep neural sequence modeling using pre-trained transformer pipelines (e.g., `cardiffnlp/twitter-roberta-base-sentiment-latest`).
  - **NLTK VADER**: Fast, offline, rule-and-lexicon-based sentiment engine calibrated for customer feedback and conversational reviews.
- **Interactive Analytics Dashboard**:
  - Key KPI Metric Cards (Total reviews, % Positive, % Negative, % Neutral, Net Sentiment Score).
  - **Chart.js** Doughnut Chart for sentiment distribution.
  - **Chart.js** Bar Chart for volume comparisons.
  - **Chart.js** Timeline Chart for sentiment trends over time.
- **Single Text Analysis**:
  - Real-time text analysis with character counter.
  - One-click benchmark test sentences for instant verification.
  - Visual sentiment badge, confidence percentage, 3-way score bar, and extracted keyword tags.
- **Batch CSV Analysis**:
  - Drag-and-drop CSV dataset upload.
  - Automatic review/text column detection (or custom column selection).
  - Bulk inference for hundreds of rows.
  - Downloadable enriched CSV reports with predicted sentiment and scores.
  - Pre-bundled sample dataset (`sample_reviews.csv`) for testing.
- **History & Database Persistence**:
  - Persistent document storage in **MongoDB** with PyMongo.
  - Intelligent **Local Storage fallback** mode if MongoDB is offline, allowing immediate execution without database errors.
  - Full search and filtering by sentiment and text.
  - Individual record deletion and complete history purge with confirmation modal.
  - One-click CSV export of all analysis history.
- **Modern Responsive UI**:
  - Bootstrap 5 responsive layout with sidebar navigation.
  - Mobile collapsible menu, sleek glassmorphism styling, and custom hover states.

---

## 🛠️ Technology Stack

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Backend** | Python 3.11+, Flask | RESTful web framework with modular Blueprints |
| **Frontend** | HTML5, CSS3, JavaScript, Bootstrap 5 | Modern responsive dashboard interface |
| **Visualization** | Chart.js 4.4 | Interactive doughnut, bar, and timeline charts |
| **AI / NLP** | NLTK (VADER), Transformers | Lexicon and neural sentiment classification |
| **Data Processing** | Pandas | High-throughput CSV parsing and batch analysis |
| **Database** | MongoDB, PyMongo | Document-based persistence with offline JSON fallback |

---

## 📁 Project Structure

```
sentiment-analyzer/
│
├── app.py                     # Main Flask application entrypoint & factory
├── config.py                  # Central configuration module (.env loader)
├── requirements.txt           # Python dependency specifications
├── .env                       # Environment configuration file
├── .env.example               # Template for environment variables
├── .gitignore                 # Git ignore rules
├── README.md                  # Comprehensive documentation and setup guide
│
├── models/                    # AI and NLP modules
│   ├── __init__.py
│   └── sentiment_model.py     # NLP preprocessing, VADER & Hugging Face engine
│
├── database/                  # Data layer & database connectivity
│   ├── __init__.py
│   └── db.py                  # PyMongo client & local JSON fallback service
│
├── routes/                    # Modular Flask route blueprints
│   ├── __init__.py
│   ├── dashboard.py           # Home, Dashboard, About, and Stats API
│   ├── analysis.py            # Single & Batch CSV sentiment endpoints
│   └── history.py             # History view, search, delete, and CSV export
│
├── templates/                 # Jinja2 HTML templates
│   ├── base.html              # Base shell with sidebar, topbar, and toasts
│   ├── index.html             # Home page with hero, quick demo, and features
│   ├── dashboard.html         # Analytics dashboard with Chart.js charts
│   ├── analyze.html           # Single text analysis with gauges & samples
│   ├── bulk_analysis.html     # Batch CSV upload, preview table, and export
│   ├── history.html           # Searchable history table with filter & delete
│   ├── about.html             # Project details and NLP methodology
│   ├── 404.html               # 404 Not Found error page
│   └── 500.html               # 500 Server Error page
│
├── static/                    # Static assets
│   ├── css/
│   │   └── style.css          # Custom styling, themes, badges, and layout
│   └── js/
│       ├── main.js            # General UI interactions and toast notifications
│       └── dashboard.js       # Chart.js charts and live refresh logic
│
├── sample_data/               # Test datasets
│   └── sample_reviews.csv     # Pre-bundled customer reviews dataset
│
├── data/                      # Local JSON storage fallback (auto-created)
│   └── sentiment_records.json
│
└── uploads/                   # Temporary directory for batch CSV results
```

---

## ⚙️ Installation & Setup

### 1. Prerequisites
- **Python 3.10 or higher** installed.
- **MongoDB** (Optional): A local MongoDB instance or a free [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) cluster.
  *(Note: SentiAI Pro includes an automatic local storage fallback, so the application runs out-of-the-box even without MongoDB running!)*

### 2. Navigate to the Project Directory
```bash
cd "C:\Users\Chanduru Kumar\.gemini\antigravity\scratch\sentiment-analyzer"
```

### 3. (Recommended) Create and Activate a Virtual Environment
**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**On Windows (Command Prompt):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**On Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables
Copy `.env.example` to `.env` if not already created:
```bash
cp .env.example .env
```

Review or modify `.env` as needed:
```env
# Flask
FLASK_APP=app.py
FLASK_ENV=development
PORT=5000
DEBUG=True

# MongoDB Connection
# For Local MongoDB:
MONGO_URI=mongodb://localhost:27017/sentiment_db
# For MongoDB Atlas:
# MONGO_URI=mongodb+srv://<username>:<password>@cluster0.mongodb.net/sentiment_db?retryWrites=true&w=majority

# NLP Engine Mode
USE_TRANSFORMERS=False
FALLBACK_TO_VADER=True
```

---

## 🗄️ MongoDB Configuration Guide

### Option A: Free Cloud MongoDB Atlas (Recommended)
1. Sign up at [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas).
2. Create a free M0 Shared Cluster.
3. Under **Database Access**, create a user with username and password.
4. Under **Network Access**, add `0.0.0.0/0` (allow access from anywhere) or your current IP.
5. Click **Connect** -> **Drivers** (Python), copy the connection string, and paste it into `.env`:
   ```env
   MONGO_URI=mongodb+srv://myUser:myPassword@cluster0.abcde.mongodb.net/sentiment_db?retryWrites=true&w=majority
   ```

### Option B: Local MongoDB Service
1. Download and install [MongoDB Community Server](https://www.mongodb.com/try/download/community).
2. Start the MongoDB service:
   ```powershell
   net start MongoDB
   ```
3. Set in `.env`:
   ```env
   MONGO_URI=mongodb://localhost:27017/sentiment_db
   ```

### Option C: Seamless Local Storage Fallback
If MongoDB is not installed or unreachable, **SentiAI Pro automatically activates Local Storage Mode** (`data/sentiment_records.json`). The web interface will display a status badge indicating Local Storage mode, and all features (saving, dashboard statistics, history, delete, CSV export) will continue working without any errors.

---

## 🚀 Running the Application

Start the Flask web server:
```bash
python app.py
```

The server will launch at:
👉 **`http://127.0.0.1:5000`**

Open your web browser and navigate to `http://127.0.0.1:5000`.

---

## 🧪 Testing Benchmark Sentences

You can test the application using the following benchmark sentences:

| Category | Input Sentence | Expected Sentiment | Expected Compound |
| :--- | :--- | :---: | :---: |
| **Positive** | `"The product is excellent and the customer service is amazing."` | **Positive** | `+0.8176` |
| **Negative** | `"The product is terrible and I am very disappointed."` | **Negative** | `-0.7574` |
| **Neutral** | `"The product was delivered yesterday."` | **Neutral** | `0.0000` |

### Testing Batch CSV Analysis
1. Navigate to **Bulk Analysis** (`/bulk`).
2. Click **Download Sample Reviews CSV** to download `sample_customer_reviews.csv`.
3. Drag and drop the downloaded CSV file into the upload dropzone.
4. Click **Start Batch Sentiment Analysis**.
5. Observe the batch metrics and preview table.
6. Click **Download Enriched CSV** to receive the analyzed results file.

---

## 📡 REST API Reference

| Endpoint | Method | Description |
| :--- | :---: | :--- |
| `/api/analyze` | `POST` | Analyzes single text string. Body: `{"text": "...", "save": true}` |
| `/api/bulk-analyze` | `POST` | Uploads multipart CSV file and classifies all reviews |
| `/api/stats` | `GET` | Returns aggregated metrics, distribution, and timeline data for Chart.js |
| `/api/history` | `GET` | Returns filtered history records (`?sentiment=positive&search=good`) |
| `/api/history/delete/<id>` | `POST/DELETE` | Deletes an individual record by ID |
| `/api/history/clear` | `POST` | Clears all history records |
| `/download-results/<file>` | `GET` | Downloads batch analysis output CSV |
| `/export-history` | `GET` | Generates and downloads a complete history CSV |
| `/health` | `GET` | System health check (database & NLP model status) |

---

## 🔧 Troubleshooting

### 1. `ModuleNotFoundError`
Make sure all dependencies are installed in your active Python environment:
```bash
pip install -r requirements.txt
```

### 2. NLTK Download Issues
If NLTK data is not downloaded automatically, run:
```bash
python -c "import nltk; nltk.download('vader_lexicon'); nltk.download('punkt'); nltk.download('stopwords')"
```

### 3. Port 5000 Already in Use
Change the port in `.env`:
```env
PORT=5050
```

### 4. Enabling Hugging Face Transformers
To use Hugging Face transformer models instead of VADER:
1. Install PyTorch and Transformers:
   ```bash
   pip install torch transformers
   ```
2. In `.env`, set:
   ```env
   USE_TRANSFORMERS=True
   MODEL_NAME=cardiffnlp/twitter-roberta-base-sentiment-latest
   ```
*(Note: On first run, Hugging Face will download the model weights to the local cache).*

---

## 📄 License
This project is open-source under the MIT License.
