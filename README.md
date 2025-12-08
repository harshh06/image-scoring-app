# 🔬 AI-Powered Histopathology Scoring System

A full-stack, "Human-in-the-Loop" application designed to automate the scoring of histological tissue samples (Pancreas). The system uses a Deep Learning model (ResNet18) to predict fibrosis and atrophy scores, while allowing pathologists to review, edit, and save corrections to a persistent database.

![Project Status](https://img.shields.io/badge/Status-MVP_Complete-success)
![Docker](https://img.shields.io/badge/Docker-Containerized-blue)
![Stack](https://img.shields.io/badge/Tech-Next.js_|_FastAPI_|_PostgreSQL-black)

---

## 🚀 Key Features

- **Automated AI Inference:** Processes large `.tif` / `.tiff` whole-slide images using a trained PyTorch model.
- **Smart Queue System:** Handles sequential file processing to prevent server overload.
- **Human-in-the-Loop Workflow:**
  - **AI Draft:** The model suggests initial scores for 4 metrics (Architecture, Atrophy, Complexes, Fibrosis).
  - **Human Review:** Interactive sidebar allows experts to edit scores manually.
  - **Visual Feedback:** "Auto-Saving" -> "Saved" indicators confirm data persistence.
- **Smart Data Persistence (Upsert):**
  - If a **new** image is uploaded, it is scored and saved.
  - If an **existing** image is re-uploaded, the system **retrieves the saved history** (preserving manual edits) instead of overwriting it with fresh AI predictions.
- **Smart Serial Parsing:** Automatically extracts Group IDs (`S-3602`) and Image IDs (`S-3602-01`) from filenames via Regex.
- **Full Database Export:** Download the entire history of scored images as a CSV file.

---

## 🛠️ Technical Architecture

The application is composed of three isolated Docker containers orchestrated via `docker-compose`.

### 1. Frontend (Client)

- **Framework:** Next.js 15 (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS + Shadcn UI components
- **State Management:** React Hooks (`useState`, `useEffect`) for managing the upload queue and optimistic UI updates
- **Networking:** Axios for API communication

### 2. Backend (API & ML)

- **Framework:** FastAPI (Python 3.9+)
- **AI Engine:** PyTorch (ResNet18 architecture with custom fully connected layer)
- **Image Processing:** Pillow (PIL) for resizing and **Base64** thumbnail generation
- **ORM:** SQLAlchemy for database interactions
- **API Protocol:** RESTful endpoints for uploading, updating, and exporting data

### 3. Database (Storage)

- **Engine:** PostgreSQL 15 (Alpine Linux)
- **Schema:** Single table (`image_scores`) storing filenames, timestamps, parsed serial numbers, and floating-point scores
- **Persistence:** Docker volume (`db_data`) ensures data survives container restarts

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

## 🧠 Engineering Highlights

### 1. Base64 Thumbnails vs. Static Serving

We opted to convert image thumbnails to **Base64 Data URIs** in the backend instead of serving them via a static file URL.

- **Why?** This eliminates complex Docker networking issues (CORS, Proxying, Hostname resolution) when the Frontend container tries to access images inside the Backend container. It makes the app portable and "bulletproof."

### 2. The "Upsert" Logic (History Preservation)

The backend `POST /api/upload-image/` endpoint implements intelligent logic:

- It checks `db.query(...).filter(filename=...)`.
- **Found?** It ignores the new AI inference and returns the **Database Record**. This ensures that if a doctor manually edited "Fibrosis" from 1.0 to 3.0, re-uploading the file loads the corrected 3.0, not the AI's original 1.0.
- **Not Found?** It saves the new AI predictions as a new record.

### 3. Parsing Logic

The system automatically parses filenames to support LIMS grouping:

- **Input:** `S-3602-10X_Image001_ch00.tif`
- **Extracted Serial:** `S-3602-01` (Unique Identifier)
- **Extracted Group:** `S-3602` (Sample ID)

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

- **History Table UI:** A dedicated page to view, search, and filter all historical records without needing to upload files.
- **Authentication:** Login system to track _which_ pathologist made the edits.
- **Active Learning:** An automated pipeline to retrain the PyTorch model using the "Human-Corrected" scores stored in the database.

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Contact

For questions or support, please open an issue in the GitHub repository.
