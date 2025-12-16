# 🔬 AI-Powered Histopathology Scoring System

A full-stack, "Human-in-the-Loop" application designed to automate the scoring of histological tissue samples (Pancreas). The system utilizes a Deep Learning model (ResNet18) to predict fibrosis and atrophy scores, while empowering pathologists to review, edit, and save corrections to a persistent database.

![Status](https://img.shields.io/badge/Status-MVP_Complete-success?style=flat-square&logo=git)
![Docker](https://img.shields.io/badge/Docker-Containerized-blue?style=flat-square&logo=docker)
![Frontend](https://img.shields.io/badge/Frontend-Next.js_15-black?style=flat-square&logo=next.js)
![Backend](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi)
![Database](https://img.shields.io/badge/Database-PostgreSQL-336791?style=flat-square&logo=postgresql)

---

## 🚀 Key Features

- **🤖 Automated AI Inference:** Processes large `.tif` / `.tiff` whole-slide images using a custom trained PyTorch model.
- **🔄 Smart Queue System:** Manages sequential file processing to prevent server overload during bulk uploads.
- **👨‍⚕️ Human-in-the-Loop Workflow:**
  - **AI Draft:** The model generates initial scores for 4 metrics: _Architecture, Atrophy, Complexes, and Fibrosis_.
  - **Human Review:** An interactive sidebar allows experts to override AI scores manually.
  - **Visual Feedback:** Real-time "Auto-Saving" → "Saved" indicators confirm data persistence.
- **💾 Smart Data Persistence (Upsert):**
  - **New Images:** Scored by AI and saved immediately.
  - **Re-uploaded Images:** The system detects existing records and **retrieves the saved history** (preserving previous manual edits) instead of overwriting them with fresh AI predictions.
- **🏷️ Smart Serial Parsing:** Automatically extracts Group IDs (e.g., `S-3602`) and Unique Image IDs (e.g., `S-3602-01`) from complex filenames via Regex.
- **📊 Full Database Export:** One-click download of the entire scoring history as a CSV file.

---

## 🛠️ Technical Architecture

The application is composed of three isolated Docker containers orchestrated via `docker-compose`.

### 1. Frontend (Client)

- **Framework:** Next.js 15 (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS + Shadcn UI components
- **State Management:** React Hooks (`useState`, `useEffect`) for optimistic UI updates.
- **Networking:** Axios for API communication.

### 2. Backend (API & ML)

- **Framework:** FastAPI (Python 3.9+)
- **AI Engine:** PyTorch (ResNet18 architecture with custom fully connected layer).
- **Image Processing:** Pillow (PIL) for resizing and **Base64** thumbnail generation.
- **ORM:** SQLAlchemy for database interactions.

### 3. Database (Storage)

- **Engine:** PostgreSQL 15 (Alpine Linux)
- **Schema:** Single table (`image_scores`) storing filenames, timestamps, parsed serial numbers, and floating-point scores.
- **Persistence:** Docker volume (`db_data`) ensures data survives container restarts.

---

## 📂 Project Structure

```
image-scoring-app/
├── docker-compose.yml       # Orchestrates FE, BE, and DB services
├── backend/
│   ├── app/
│   │   ├── main.py          # API Endpoints (Upload, Update, Export)
│   │   ├── models.py        # SQLAlchemy Database Schema
│   │   ├── database.py      # DB Connection Logic
│   │   └── utils.py         # AI Inference & Image Parsing Logic
│   ├── Dockerfile           # Python environment setup
│   ├── pancreas_model.pth   # Trained PyTorch Model weights
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── app/page.tsx     # Main Dashboard Logic (Queue & State)
│   │   ├── components/      # UI Components (Sidebar, Header, Dropzone)
│   │   └── services/api.ts  # Type definitions & Axios calls
│   ├── Dockerfile           # Node.js environment setup
│   ├── next.config.js       # Configuration (Port 3000)
│   └── package.json         # JS dependencies
└── .env                     # Environment variables (Gitignored)
```

---

## 🧠 Engineering Highlights

### 1. Base64 Thumbnails vs. Static Serving

We opted to convert image thumbnails to **Base64 Data URIs** in the backend instead of serving them via a static file URL.

- **Why?** This eliminates complex Docker networking issues (CORS, Proxying, Hostname resolution) when the Frontend container tries to access images inside the Backend container. It makes the app portable and "bulletproof."

### 2. The "Upsert" Logic (History Preservation)

The backend `POST /api/upload-image/` endpoint implements intelligent logic:

1. It queries the database for `filename`.
2. **If Found:** It ignores the new AI inference and returns the **Database Record**. This ensures that if a doctor manually edited "Fibrosis" from `1.0` to `3.0`, re-uploading the file loads the corrected `3.0`, not the AI's original `1.0`.
3. **If Not Found:** It runs the model and saves the new AI predictions as a new record.

### 3. Parsing Logic

The system automatically parses filenames to support LIMS grouping:

- **Input:** `S-3602-10X_Image001_ch00.tif`
- **Extracted Serial:** `S-3602-01` (Unique Identifier)
- **Extracted Group:** `S-3602` (Sample ID)

---

## ⚡ Quick Start Guide

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Running)
- Git

### Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/your-username/image-scoring-app.git
   cd image-scoring-app
   ```

2. **Verify the Model:**
   Ensure your trained model file `pancreas_model.pth` is placed inside the `backend/` directory.

3. **Start the Application:**
   Run the following command to build and start all services:

   ```bash
   docker compose up --build
   ```

   _First-time build may take a few minutes to download PyTorch and Node images._

4. **Access the App:**

   - **Frontend (Dashboard):** http://localhost:3000
   - **Backend (Docs):** http://localhost:8000/docs
   - **Database:** `localhost:5432` (User: `appuser`, Password: `your_strong_dev_password`)

---

## 🔧 Troubleshooting

**1. "Module not found: Can't resolve 'axios'"**

- **Fix:** The frontend container's `node_modules` might be out of sync.
  ```bash
  docker compose build frontend
  docker compose up -d
  ```

**2. Database Connection Failed**

- **Fix:** Ensure the `db` service is healthy. Docker Compose is configured to wait for the DB to start, but if it fails, try resetting the volume:
  ```bash
  docker compose down -v  # WARNING: Deletes all data
  docker compose up
  ```

**3. "AI Model not loaded" Error**

- **Fix:** Verify `pancreas_model.pth` exists in the `backend/` folder **before** building the image.

---

## 🔮 Future Roadmap

- [ ] **History Table UI:** A dedicated page to view, search, and filter all historical records without needing to upload files.
- [ ] **Authentication:** Login system to track _who_ made specific edits.
- [ ] **Active Learning:** An automated pipeline to retrain the PyTorch model using the "Human-Corrected" scores stored in the database.

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
