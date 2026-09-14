# 🔬 AI-Powered Histopathology Scoring System

> **Accelerating medical diagnosis through AI-assisted pathology analysis**  
> A production-ready full-stack application that streamlines pancreatic tissue scoring while preserving expert oversight through a Human-in-the-Loop workflow.

[![Live Demo](https://img.shields.io/badge/🚀_Live_Demo-Vercel-black?style=for-the-badge)](https://image-scoring-app.vercel.app)
[![Backend API](https://img.shields.io/badge/🔧_API_Docs-Hugging_Face-yellow?style=for-the-badge)](https://harshsonii-histopathology-scoring.hf.space/docs)
[![Status](https://img.shields.io/badge/Status-Production_Ready-success?style=flat-square&logo=git)](https://github.com/harshh06/image-scoring-app)
[![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)

---

## 🎯 Problem Statement

**Manual histopathology scoring is slow, subjective, and creates research bottlenecks.**  
Pathologists manually score tissue samples across multiple metrics (fibrosis, atrophy, architecture, complexes), a process that's time-intensive and subject to inter-observer variability. With hundreds of samples per study, this becomes a significant bottleneck in clinical research.

**This system solves that problem** by providing AI-generated "first draft" scores that pathologists can review, validate, and correct through an intuitive web interface—shifting the workflow from manual data entry to expert verification.

---

## 📸 Application Walkthrough

### 1️⃣ Bulk Upload Interface
![Upload Interface](docs/images/screenshot1.png)
*Drag-and-drop support for processing multiple high-resolution TIFF images simultaneously*

### 2️⃣ Smart Queue Processing
![Queue System](docs/images/screenshot2.png)
*Real-time status tracking prevents server overload during batch uploads*

### 3️⃣ AI-Powered Scoring + Human Review
![Scoring Interface](docs/images/screenshot3.png)
*Interactive sidebar allows pathologists to override AI predictions with visual feedback*

### 4️⃣ Detailed Score Editor
![Score Editor](docs/images/screenshot4.png)
*Editable fields with auto-save functionality preserve all manual corrections*

---

## 🛠️ Tech Stack

### Frontend
![Next.js](https://img.shields.io/badge/Next.js_14-black?style=for-the-badge&logo=next.js)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![Tailwind](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)
![Shadcn/ui](https://img.shields.io/badge/Shadcn/ui-000000?style=for-the-badge&logo=shadcnui&logoColor=white)

### Backend
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)
![Python](https://img.shields.io/badge/Python_3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)

### Infrastructure
![PostgreSQL](https://img.shields.io/badge/PostgreSQL_15-336791?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Vercel](https://img.shields.io/badge/Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)
![Hugging Face](https://img.shields.io/badge/Hugging_Face-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black)

---

## 🚀 Key Features

### 🤖 Dual-Scoring AI Inference
- **ResNet18-based CNNs** fine-tuned on annotated pancreatic tissue samples
- **Dual-Model Support**: Seamlessly switch between Chronic Pancreatitis (CP) and Acute Pancreatitis (AP) scoring modes from the frontend dashboard.
- Processes high-resolution `.tif` / `.tiff` whole-slide images (50+ MB each)
- Predicts pathology metrics dynamically based on the active mode:
  - **CP Mode**: *Architecture, Atrophy, Complexes, Fibrosis*
  - **AP Mode**: *Edema, Necrosis, Inflammation*
- **Average inference time:** ~2 seconds per image on CPU

### 🔄 Client-Side Sequential Queue
A smart batch processing system designed to protect server resources by managing flow control directly in the browser.
* **Memory-Safe Batching:** The frontend acts as a buffer, holding files in client-side memory and releasing them to the server strictly one-by-one (FIFO). This prevents server-side RAM exhaustion even when uploading 100+ high-res TIFFs.
* **Stateless Flow:** By processing images in a serial stream, the backend remains stateless, avoiding the storage bottlenecks and crashes common in free-tier cloud deployments.
* **Granular Status Tracking:**
  * `Pending`: Secured in browser memory.
  * `Processing`: Active transfer and AI inference.
  * `Completed`: Result stored in DB and visualized.
* **Non-Blocking UI:** Users can immediately review and edit scores for completed images while the rest of the queue processes in the background.

### 👨‍⚕️ Human-in-the-Loop Workflow
1. **AI Draft:** Model generates initial scores automatically
2. **Expert Review:** Interactive sidebar displays predictions alongside tissue preview
3. **Manual Override:** Click any score field to edit with instant visual feedback
4. **Auto-Save:** Changes persist to database immediately with "Saving..." → "Saved ✓" indicator

### 💾 Intelligent Data Persistence (Upsert Logic)
- **New Images:** Scored by AI and saved to PostgreSQL automatically
- **Re-uploaded Images:** System detects existing records and **retrieves saved history** instead of overwriting with fresh AI predictions
- **Why this matters:** Preserves all manual corrections made by pathologists (e.g., if a doctor changed "Fibrosis" from AI's `1.0` to `3.0`, re-uploading loads the corrected `3.0`)
- **Implementation:** ACID-compliant database operations with conflict resolution

### 🏷️ Smart Serial Parsing
- Automatically extracts metadata from complex filenames via Regex:
  - **Input:** `S-3602-10X_Image001_ch00.tif`
  - **Extracted Serial:** `S-3602-01` (Unique Identifier)
  - **Extracted Group:** `S-3602` (Sample ID for grouping)

### 📊 Full Database Export
- One-click CSV download of entire scoring history
- Includes timestamps, filenames, serial numbers, and all 4 pathology scores
- Compatible with Excel, R, Python for downstream analysis

---

## 🏗️ System Architecture

The application follows a **microservices architecture** with three isolated Docker containers:

```mermaid
graph LR
    A[Next.js Frontend] -->|REST API| B[FastAPI Backend]
    B -->|SQLAlchemy ORM| C[PostgreSQL Database]
    B -->|PyTorch Inference| D[ResNet18 Model]
    C -->|Docker Volume| E[Persistent Storage]
```

### Architecture Highlights

**1. Base64 Image Encoding**  
Instead of serving thumbnails via static URLs, the backend converts images to Base64 Data URIs. This eliminates Docker networking complexity (CORS, proxying) and makes the app 100% portable across deployment environments.

**2. Database Upsert Logic**  
The `POST /api/upload-image/` endpoint implements intelligent deduplication:
- Queries database for existing `filename`
- **If found:** Returns saved record (preserves manual edits)
- **If not found:** Runs AI inference and creates new record

**3. Asynchronous Processing**  
FastAPI handles file uploads asynchronously, enabling concurrent processing without blocking the event loop.

**4. Strict CORS & Redirect Handling**  
Unified trailing-slash handling across frontend/backend prevents 307 redirect loops that commonly plague FastAPI deployments.

---

## 📂 Project Structure

```
image-scoring-app/
├── docker-compose.yml          # Orchestrates FE, BE, DB services
├── frontend/
│   ├── src/
│   │   ├── app/page.tsx        # Main dashboard (queue & state management)
│   │   ├── components/         # UI components (Sidebar, Header, Dropzone)
│   │   └── services/api.ts     # Axios API client + TypeScript types
│   ├── Dockerfile              # Node.js 18 Alpine image
│   └── package.json            # Dependencies (Next.js, Axios, Tailwind)
├── backend/
│   ├── app/
│   │   ├── main.py             # FastAPI routes (Upload, Update, Export)
│   │   ├── models.py           # SQLAlchemy schema (image_scores table)
│   │   ├── database.py         # PostgreSQL connection pooling
│   │   └── utils.py            # AI inference + filename parsing
│   ├── pancreas_model.pth      # Trained PyTorch model (~62 MB)
│   ├── Dockerfile              # Python 3.9 Slim image
│   └── requirements.txt        # Dependencies (FastAPI, PyTorch, Pillow)
└── docs/
    └── images/                 # Screenshots for README
```

---

## ⚡ Quick Start (Docker)

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- Git (with Git LFS for model file)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/harshh06/image-scoring-app.git
   cd image-scoring-app
   ```

2. **Verify model file exists:**
   ```bash
   ls -lh backend/pancreas_model.pth  # Should show ~62MB file
   ```

3. **Start all services:**
   ```bash
   docker compose up --build
   ```
   *First build takes 3-5 minutes to download PyTorch and Node images*

4. **Access the application:**
   - **Frontend (Dashboard):** http://localhost:3000
   - **Backend API Docs:** http://localhost:8000/docs
   - **Database:** `localhost:5432` (User: `appuser`, Password: `your_strong_dev_password`)

### Testing the App

1. Drag 5-10 TIFF files into the upload zone
2. Watch the queue process files sequentially
3. Click a processed image → Edit scores → Observe auto-save indicator
4. Click "Export CSV" to download scoring history

---

## 🧪 Development Workflow

### Local Development (Without Docker)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev  # Runs on http://localhost:3000
```

**Database:**
```bash
docker run -d \
  -e POSTGRES_USER=appuser \
  -e POSTGRES_PASSWORD=your_strong_dev_password \
  -e POSTGRES_DB=scoring_db \
  -p 5432:5432 \
  postgres:15-alpine
```

---

## 🔧 Troubleshooting

### Common Issues

**1. Frontend build fails: "Module not found: 'axios'"**

**Cause:** Docker volume sync issue with `node_modules`

**Fix:**
```bash
docker compose down
docker compose build frontend --no-cache
docker compose up
```

---

**2. "Database connection refused" error**

**Cause:** PostgreSQL container not fully initialized before FastAPI starts

**Fix:** Docker Compose includes a `depends_on` health check, but if it fails:
```bash
docker compose down -v  # ⚠️ WARNING: Deletes all data
docker compose up --build
```

---

**3. AI model not loading (404 error)**

**Cause:** `pancreas_model.pth` missing from `backend/` directory

**Fix:** Verify file exists and is accessible:
```bash
ls -lh backend/pancreas_model.pth
# Expected: -rw-r--r-- 1 user staff 62M Dec 10 12:00 pancreas_model.pth
```

---

**4. Images not displaying in preview**

**Cause:** Base64 encoding failed due to corrupted TIFF file

**Fix:** Check backend logs for PIL errors:
```bash
docker compose logs backend | grep "PIL"
```

---

## 🧠 Model Architecture & Training Details

### Core Architecture

The core of this system utilizes **ResNet18 Convolutional Neural Networks**, adapted for medical regression through transfer learning.

**Base Model:** ResNet18 pretrained on ImageNet (chosen for the optimal balance between feature extraction depth and CPU inference speed).

**Custom Regression Head:** The standard 1000-class classification head was replaced with custom linear layers to predict continuous pathology scores.

---

### 🟢 Model 1: Acute Pancreatitis (AP) Scoring (Enhanced)

- **Architecture:** ResNet18 (pretrained ImageNet) + dropout (`p=0.5`) before regression head.
- **Data Augmentation:** random horizontal/vertical flips, 45° rotation, color jitter (brightness 0.1, contrast 0.1).
- **Regularization:** Dropout layer, early stopping via validation loss.
- **Training Config:** Adam optimizer (`lr=0.0001`), batch size `8`, `35` epochs on Apple Silicon MPS.
- **Metrics:** Best validation MSE ≈ 0.028, final test MSE ≈ 0.023.
- **Experiment Tracking:** [View W&B Interactive Training Report](https://wandb.ai/harshsoni/ap-pancreatitis-scoring/reports/ResNet-18-AP-Tissue-Scoring-Training-Metrics--VmlldzoxNzkzMjc3Ng?accessToken=o5jhhbmggxtr24mxghip4s5qg30mg9avhfp6m81ejthdv6als72eouppispi6j71)

![AP Training Loss Curve](loss_curves.png)

---

### 🔵 Model 2: Chronic Pancreatitis (CP) Scoring (Legacy)

Our original CP model was also trained on ~400-500 expert-annotated pancreatic H&E stained tissue crops, establishing the baseline pipeline.

#### Fine-Tuning Strategy (Partial Unfreezing)
- **Frozen Layers:** Layers 1–3 were frozen to preserve general vision features (edges, textures) learned from ImageNet.
- **Unfrozen Layers:** Layer 4 and the Custom Head were unfrozen for domain-specific fine-tuning, allowing the model to adapt to complex histological patterns like pancreatic fibrosis.

#### Data Normalization
Implemented **Target Scaling**, normalizing expert scores (0–4) to a 0.0–1.0 range during training to stabilize gradients and accelerate convergence.

#### CP Model Performance Metrics
- **Configuration:** Adam Optimizer (`lr=0.001`), Batch Size `16`, `~50` Epochs (with early stopping).
- **Loss Function:** Mean Squared Error (MSE), chosen to minimize the distance between predicted and ground-truth severity scores, treating each pathology metric as a continuous regression target.

---

### Why ResNet18?

#### 1. Anti-Overfitting
Deeper architectures (ResNet50/152) contain significantly more parameters, which pose a high risk of **"memorizing" rather than "learning"** from a 400-sample dataset.

#### 2. Production Latency
ResNet18 maintains a small memory footprint (~45MB–62MB), allowing for **~2s inference times on CPU-only environments** like Hugging Face Spaces.

#### 3. Stateless Inference
By using a lighter model, the system can process images directly in RAM, avoiding the need for expensive GPU clusters or persistent disk storage for temporary files.

---

### Performance Characteristics

| Metric | Value |
|--------|-------|
| **Model Size** | ~62 MB (Optimized for Git LFS/Deployment) |
| **Backbone** | ResNet18 (Transfer Learning) |
| **Inference Time** | ~2.3 seconds per image (CPU) |
| **Batch Logic** | Sequential FIFO Queue (prevents RAM spikes) |
| **Persistence** | Database "Upsert" logic (preserves manual overrides) |


---

## 🚀 Deployment

### Production Deployment (Current Setup)

- **Frontend:** Deployed on [Vercel](https://vercel.com) (Serverless Next.js)
- **Backend:** Deployed on [Hugging Face Spaces](https://huggingface.co/spaces) (FastAPI endpoint)
- **Database:** Managed PostgreSQL on [Railway](https://railway.app) or [Supabase](https://supabase.com)

### Environment Variables

Create a `.env` file in the project root:

```bash
# Database
DATABASE_URL=postgresql://user:password@host:5432/db_name

# Frontend
NEXT_PUBLIC_API_URL=https://your-backend.hf.space

# Backend
CORS_ORIGINS=https://image-scoring-app.vercel.app
MODEL_PATH=/app/pancreas_model.pth
```

### Deployment Challenges Solved

| Challenge | Solution |
|-----------|----------|
| **CORS / Redirect Loops** | Implemented strict trailing-slash handling in FastAPI and unified `NEXT_PUBLIC_API_URL` environment variables to prevent 307 redirects |
| **Deployment Size Limits** | Optimized Docker image size using `slim` Python variants and multi-stage builds to fit within free-tier PaaS limits |

---

## 🔮 Future Roadmap

- [ ] **Batch Processing Dashboard:** Dedicated page to view/search all historical records without re-uploading
- [ ] **User Authentication:** Login system to track which pathologist made specific edits
- [ ] **Active Learning Pipeline:** Automated retraining using human-corrected scores

---

## 📊 Impact & Use Cases

### Research Applications
- **Clinical Trials:** Accelerate tissue sample scoring in drug efficacy studies
- **Biobanking:** Scale pathology annotation for large tissue repositories
- **Quality Control:** Standardize scoring across multiple pathologists

### Workflow Improvement
- **From Manual Entry → Expert Verification:** Pathologists review AI predictions instead of scoring from scratch
- **Audit Trail:** All manual corrections are preserved in the database for quality assurance
- **Data Standardization:** CSV export enables seamless integration with statistical analysis pipelines

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 (Python) and Airbnb style guide (TypeScript)
- Add tests for new features (pytest for backend, Jest for frontend)
- Update documentation in README and code comments
- Ensure Docker builds pass: `docker compose build --no-cache`

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**Harsh Soni** | MSCS Student @ University of Florida  
[![GitHub](https://img.shields.io/badge/GitHub-harshh06-181717?style=flat-square&logo=github)](https://github.com/harshh06)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=flat-square&logo=linkedin)](https://linkedin.com/in/harshh06)

---

## 🙏 Acknowledgments

- **Computing Resources:** Model development on Apple M2 MacBook Air
- **Open Source:** Built with Next.js, FastAPI, PyTorch, and PostgreSQL
- **UI Design:** Shadcn/ui component library

---

<div align="center">

### ⭐ Star this repo if you found it helpful!

**Questions?** Open an [issue](https://github.com/harshh06/image-scoring-app/issues) or reach out on [LinkedIn](https://linkedin.com/in/your-profile)

*Built with Next.js, FastAPI, and PyTorch. Deployed with Vercel & Hugging Face.*

</div>
