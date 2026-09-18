# Vernacular Answer-Sheet Auto-Grader

A professional, production-grade web application to auto-grade handwritten Devanagari/Hindi exam answers using OCR and semantic similarity against reference answers.

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy ORM (async), Pydantic v2
- **Database**: PostgreSQL (Dockerized)
- **Frontend**: React 18, TypeScript, Vite, TailwindCSS
- **OCR**: Tesseract with Hindi (Devanagari) trained data
- **Scoring**: Sentence-Transformers (multilingual embeddings) + cosine similarity
- **Orchestration**: Docker & Docker Compose
- **Testing**: Pytest (backend), Vitest (frontend)

## 🚀 How to Run the Application

The easiest way to run the application is using Docker. This will automatically set up the frontend, backend, and the database.

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) installed on your system.
- [Docker Compose](https://docs.docker.com/compose/install/) installed.

### Step-by-Step Setup

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd vernacular-grader
   ```

2. **Set up Environment Variables**:
   Copy the example environment file to create your own configuration.
   ```bash
   cp .env.example .env
   ```
   *(Optional)* Open `.env` in a text editor and update the `JWT_SECRET_KEY` or any other settings.

3. **Start the Application**:
   Use Docker Compose to build and start all services (Backend, Frontend, and PostgreSQL).
   ```bash
   docker-compose up --build
   ```
   *Note: The first time you run this, it may take a few minutes to download and build all dependencies.*

4. **Access the Application**:
   Once the containers are running, you can access the following services:
   - **Frontend (Evaluator Dashboard)**: [http://localhost:3000](http://localhost:3000)
   - **Backend API Docs (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)

### 🛑 Managing the Application

Once you have successfully built and run the app for the first time, you don't need to rebuild it every time.

- **Start normally**: `docker-compose up` (starts the app and shows logs in your terminal)
- **Start in background (Detached mode)**: `docker-compose up -d` (starts the app quietly in the background)
- **Stop the app**: Press `Ctrl+C` in the terminal where it's running, or if it's running in the background, run `docker-compose down`.

### 🧑‍🏫 How to Use the App

To start grading answers, follow this workflow:

1. **Create an Evaluator Account**: 
   Since the app doesn't have an open registration page on the UI (for security), you must register via the API docs.
   - Go to [http://localhost:8000/docs#/auth/register_api_v1_auth_register_post](http://localhost:8000/docs#/auth/register_api_v1_auth_register_post)
   - Click **Try it out**, enter a username, email, and password, and click **Execute**.

2. **Log In**: 
   Open the [Evaluator Dashboard](http://localhost:3000) and log in using the credentials you just created.

3. **Manage Students**:
   - Go to the **Students** tab on the sidebar to add, edit, or delete students. Ensure students exist with valid Roll Numbers before uploading their answer sheets.

4. **Grade an Exam**:
   - **Create Exam**: Go to the Exams tab and click "Create New Exam".
   - **Upload Batch**: Open the exam, click the "Batch Upload" tab, and upload student answer sheets (`.jpg` or `.pdf`). The system uses the file name to identify the student roll number (e.g., `101.jpg` belongs to student `101`).
   - **Process Batch**: Click "Process Batch". The app triggers background jobs to run OCR to extract Devanagari handwriting and uses the semantic engine to score it automatically.
   - **Review**: Go to the "Review & Results" tab to review side-by-side results and manually override the AI score if needed.

5. **Generate Reports**:
   - Go to the **Reports** tab to view the final results of all processed answer sheets. Click "Export to CSV" to download the final grades.

## OCR Engine

The OCR module uses **Tesseract OCR** with the Hindi (`hin`) trained data for Devanagari handwriting recognition.

### Hindi Tessdata Setup

- **In Docker** (automatic): The Dockerfile installs `tesseract-ocr-hin` via apt.
- **Manual**: `apt-get install tesseract-ocr tesseract-ocr-hin`, or download `hin.traineddata` from [tessdata_best](https://github.com/tesseract-ocr/tessdata_best) and place in your tessdata directory.

### Swapping OCR Engines

The engine uses an abstract `OCREngine` base class. To add a transformer-based OCR model (e.g. TrOCR, PaddleOCR):
1. Create a new class inheriting from `OCREngine` in `app/ocr/engine.py`.
2. Implement the `extract_text()` method.
3. Update `get_ocr_engine()` to return your new engine.

### Accuracy Caveats

Tesseract's handwriting recognition for Devanagari has moderate accuracy. CER/WER will vary significantly based on handwriting quality. Formal evaluation is planned for a later phase.

## Scoring Engine

The scoring module uses **multilingual sentence embeddings** to compare student answers against reference answers semantically.

### Embedding Model

Uses `paraphrase-multilingual-mpnet-base-v2` from sentence-transformers (~420MB, 768-dim embeddings, 50+ languages including Hindi). The model is loaded once as a singleton and cached.

To swap models, set the `SCORING_MODEL_NAME` environment variable (any sentence-transformers compatible model works).

### Similarity-to-Marks Threshold Curve

Raw cosine similarity is mapped to marks using a piecewise-linear function:
- Below `SCORING_LOW_THRESHOLD` (default 0.3) → 0 marks
- Above `SCORING_HIGH_THRESHOLD` (default 0.8) → full marks
- Between → linear interpolation

These thresholds are configurable via environment variables. Tune them based on empirical correlation with human-assigned scores (formal evaluation planned for a later phase).

### Keyword Matching

If rubric keywords are provided, each keyword is **semantically matched** (not substring-matched) against the student text using the same embedding model. This means "प्रकाश संश्लेषण" will match "photosynthesis" across languages.

## Roadmap

This project is being built in phases:
- [x] Phase 1: Foundational Scaffolding (API, DB, Frontend shell, Docker)
- [x] Phase 2: OCR Module Integration
- [x] Phase 3: Semantic Scoring Engine
- [x] Phase 4: Evaluator Dashboard
- [ ] Phase 5: Production Deployment
