This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.

## Project

**Here's the plan:**

---

Project Title: AI-Assisted Image Scoring & Visualization Web Application for Researchers
Author: [Your Name - Masters CS Student, UF]
Date: [Current Date]

---

## 1. Project Overview & Problem Statement

**Problem:** Researchers frequently need to score or analyze numerous images embedded within PDF documents. This manual process is time-consuming, prone to human error, and lacks interactive data exploration capabilities. Images often have associated metadata (e.g., serial numbers) that needs to be extracted alongside the image itself.

**Solution:** Develop a full-stack web application that automates the extraction of images and their corresponding serial numbers from PDF documents, applies custom scoring logic based on four user-defined parameters, visualizes the results interactively, and allows data export.

**Target User:** Researchers, data scientists, quality assurance professionals.

**Key Features:**
1* Secure PDF document upload.
2* Automated extraction of images and associated serial numbers from PDF.
3* Application of user-configurable 4-parameter scoring logic to each image.
4* Tabular display of scored image data (serial number, scores, image thumbnail).
5* Interactive data visualization dashboard (scatter plots, bar charts) for exploring scores.
6* Export of scored data to Excel/CSV format.
7\* Clear, responsive, and intuitive user interface.

## 2. Technical Goals & Learning Objectives (Recruiter Focus)

This project aims to demonstrate proficiency in a modern, in-demand tech stack and complex problem-solving domains:

1* **Full-Stack Development:** Proficiency in both modern frontend (Next.js/React, TypeScript) and robust backend (FastAPI, Python) development.
2* **Data Engineering & Extraction:** Expertise in handling unstructured data (PDFs), image processing, and Optical Character Recognition (OCR).
3* **API Design & Development:** Building efficient, scalable, and well-documented RESTful APIs using FastAPI.
4* **Database Management:** Designing and interacting with a relational database (PostgreSQL) for structured data storage.
5* **Data Visualization:** Creating rich, interactive data visualizations for insightful analysis using Plotly.js.
6* **DevOps & Deployment:** Containerizing the application with Docker and deploying to a cloud platform (AWS/GCP/Azure/Vercel).
7\* **Best Practices:** Implementing secure coding practices, version control (Git), error handling, and a clean, modular code structure.

## 3. Recommended Tech Stack & Justification

This stack is chosen for its modern relevance, performance, and strong community support, making it highly attractive to recruiters.

### Frontend (FE)

- **Framework:** **Next.js (React.js, TypeScript)**
  - **Justification:** Leverages your existing React experience. Next.js adds critical features like Server-Side Rendering (SSR), Static Site Generation (SSG), file-system routing, and API routes, showcasing knowledge of modern web architecture, performance, and scalability. TypeScript enhances code quality and maintainability, a huge plus for recruiters.
- **Styling:** **Tailwind CSS** or **Chakra UI**
  - **Justification:** Tailwind offers utility-first CSS for rapid, consistent styling without writing custom CSS. Chakra UI provides accessible, pre-built React components, speeding up UI development. Both are highly popular and demonstrate modern FE styling practices.
- **Data Table:** **Ag-Grid (React)**
  - **Justification:** Industry-standard, highly performant, and feature-rich grid component for displaying large datasets with filtering, sorting, and pagination.
- **Interactive Charts:** **Plotly.js (React-Plotly.js)**
  - **Justification:** Produces high-quality, interactive, publication-ready data visualizations. Ideal for researchers who need to explore data dynamically.

### Backend (BE)

- **Framework:** **FastAPI (Python 3.x)**
  - **Justification:** Extremely fast performance (built on Starlette and Pydantic), asynchronous support, automatic OpenAPI/Swagger UI documentation (recruiters love well-documented APIs), and strong type hinting. Python is the gold standard for data science and image processing.
- **Image Processing:**
  - **PDF Extraction:** `pdfplumber` or `PyMuPDF` (for embedded images).
  - **OCR (Serial Numbers):** `pytesseract` (Python wrapper for Tesseract OCR) combined with `OpenCV` (for image manipulation like cropping/pre-processing before OCR).
  - **Image Manipulation:** `Pillow` (PIL Fork) for general image operations.
  - **Justification:** These are standard, powerful libraries for robust image and document data extraction, demonstrating significant Computer Vision and data handling skills.
- **Data Handling:** **Pandas**
  - **Justification:** Essential for efficient data manipulation, cleaning, and structuring after extraction and before storage/scoring.
- **Database ORM/Client:** **SQLAlchemy (with Alembic for migrations)**
  - **Justification:** Full-featured ORM for Python, providing an abstraction layer for interacting with PostgreSQL. Alembic manages database schema changes reliably, showcasing robust database management.

### Database

- **Database:** **PostgreSQL**
  - **Justification:** A powerful, open-source, object-relational database known for its reliability, data integrity, and advanced features. Demonstrates strong SQL and relational database management skills, which are highly valued.

### DevOps & Deployment

- **Containerization:** **Docker**
  - **Justification:** Essential for packaging your application (FE, BE, DB) into isolated, portable containers. Demonstrates modern deployment practices, ensuring consistency across environments.
- **Cloud Platform:** **AWS / Google Cloud Platform (GCP) / Microsoft Azure** (choose one, e.g., AWS EC2/ECS/Lambda, RDS for Postgres)
  - **Justification:** Deploying to a major cloud provider shows practical experience with cloud infrastructure, a critical skill in today's tech landscape. Start with a free tier.
- **Frontend Deployment:** **Vercel** or **Netlify**
  - **Justification:** Excellent for deploying Next.js applications directly from Git, providing continuous deployment (CI/CD) pipelines, and fast global CDN. Demonstrates modern FE deployment workflow.

## 4. Project Phases & Deliverables

### Phase 0: Setup & Planning (1-2 Days)

- **Deliverables:**
  - Project repository initialized on GitHub/GitLab.
  - Basic README.md with project overview.
  - Initial `package.json` (FE) and `requirements.txt` (BE).
  - `Dockerfile` drafts for FE & BE services.

### Phase 1: Backend - PDF & Image Data Extraction (3-5 Days)

- **Goals:**
  - Develop API endpoint for secure PDF upload.
  - Implement logic to extract all embedded images from the PDF.
  - Implement OCR logic to identify and extract serial numbers associated with each image.
  - Structure extracted data into a clean format (e.g., list of dictionaries, Pandas DataFrame).
- **Key Tasks:**
  - FastAPI endpoint: `/upload-pdf` (POST) to receive PDF.
  - `pdfplumber`/`PyMuPDF` for image extraction.
  - `OpenCV` for image pre-processing (if needed for OCR).
  - `pytesseract` for OCR on serial number regions.
  - Error handling for corrupted PDFs or failed extractions.
- **Deliverables:**
  - FastAPI service capable of processing a PDF and returning structured data (image_id, serial_number, base64_image_data).
  - Unit tests for extraction logic.

### Phase 2: Backend - Scoring & Database Integration (3-5 Days)

- **Goals:**
  - Implement the 4-parameter scoring logic.
  - Design PostgreSQL database schema to store image data, serial numbers, and scores.
  - Develop API endpoints to store and retrieve scored data.
- **Key Tasks:**
  - Database schema: `images` table (id, serial_number, score_param1, ..., score_param4, image_path/url).
  - FastAPI endpoint: `/score-images` (POST) that accepts extracted image data, applies scoring, and stores in DB.
  - FastAPI endpoint: `/get-scores` (GET) to retrieve all scored data.
  - FastAPI endpoint: `/get-image/{id}` (GET) to retrieve a specific image.
  - `SQLAlchemy` ORM integration.
  - `Alembic` for database migrations.
- **Deliverables:**
  - Functional FastAPI endpoints for scoring and data management.
  - PostgreSQL database with designed schema.
  - Unit tests for scoring logic and DB operations.

### Phase 3: Frontend - UI & Interaction (5-7 Days)

- **Goals:**
  - Build a responsive user interface for PDF upload, score display, and data visualization.
  - Integrate with backend APIs.
  - Enable data export functionality.
- **Key Tasks:**
  - Next.js app setup (routing, layouts).
  - PDF upload component with progress indicator.
  - Display scored data using `Ag-Grid`, including image thumbnails.
  - Develop interactive dashboard using `Plotly.js` (e.g., scatter plot of two selected parameters, bar chart of average scores).
  - Implement client-side export to Excel/CSV.
  - User authentication/authorization (optional, but a plus).
- **Deliverables:**
  - Fully functional, responsive web application.
  - Interactive data table and visualization dashboard.
  - Seamless integration with backend APIs.

### Phase 4: Deployment & Documentation (2-3 Days)

- **Goals:**
  - Containerize the entire application (FE, BE, DB).
  - Deploy the application to cloud platforms.
  - Comprehensive documentation.
- **Key Tasks:**
  - Write `Dockerfile` for Next.js app.
  - Write `Dockerfile` for FastAPI app.
  - Write `docker-compose.yml` to orchestrate all services locally.
  - Deploy Frontend to Vercel/Netlify.
  - Deploy Backend (FastAPI + PostgreSQL) to AWS/GCP/Azure.
  - Update `README.md` with:
    - Detailed setup instructions (local & deployment).
    - API documentation (from FastAPI's auto-generated docs).
    - Project architecture diagram.
    - Discussion of technical challenges and solutions.
    - Future enhancements.
- **Deliverables:**
  - Deployed, accessible web application.
  - Containerized application (Docker images).
  - Comprehensive project documentation.

## 5. Future Enhancements (Ideas for Expansion)

- **User Authentication/Authorization:** Allow multiple users to manage their own projects.
- **Advanced Image Processing:**
  - Image quality assessment (e.g., blur detection).
  - Feature extraction using more sophisticated CV models.
  - Object detection for serial numbers instead of fixed region OCR.
- **Customizable Scoring Rules:** Allow users to define their own scoring functions or rules through the UI.
- **Version Control for Scores:** Track different scoring runs or configurations.
- **Real-time Updates:** Use WebSockets for real-time progress updates during PDF processing.
- **Automated Retraining/Calibration:** If scoring uses ML, allow for model updates.
- **Advanced Export Options:** Generate custom PDF reports.

## 6. Tools & Resources

- **Version Control:** Git, GitHub
- **IDE:** VS Code (with relevant extensions for Python, JavaScript, Docker, etc.)
- **API Testing:** Postman, Insomnia, or FastAPI's built-in Swagger UI.
- **Learning Resources:**
  - Next.js Docs, React Docs
  - FastAPI Docs
  - PostgreSQL Docs
  - Plotly.js Docs
  - Docker Docs
  - Google AI Studio (for Gemini API keys)

---
