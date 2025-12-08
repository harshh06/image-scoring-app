// frontend/src/services/api.ts

import axios from "axios";

// Get the backend URL from environment variables, defaulting to localhost
const API_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

// --- TYPE DEFINITIONS (Matching your FastAPI output) ---

// Defines the shape of the four scores and the total
export interface ScoreData {
  "Pancreatic Architecture": number;
  "Glandular Atrophy": number;
  "Pseudotubular Complexes": number;
  Fibrosis: number;
  Total: number;
}

// Defines the complete response object from the FastAPI endpoint
export interface ProcessedResult {
  status: string;
  filename: string;
  serial_number: string;
  scores: ScoreData;
  display_url: string; // URL to the generated thumbnail
}

// --- API FUNCTIONS ---

/**
 * Uploads a single TIFF file to the FastAPI backend for AI processing.
 * @param file The File object selected by the user.
 * @returns A Promise resolving to the ProcessedResult (scores, thumbnail URL).
 */
export const uploadImage = async (file: File): Promise<ProcessedResult> => {
  // Use FormData to send the file correctly as 'multipart/form-data'
  const formData = new FormData();
  formData.append("file", file);

  console.log(`[API] Starting upload for: ${file.name}: ${API_URL}`);

  // We use Axios to handle the POST request
  const response = await axios.post(`${API_URL}/api/upload-image/`, formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
    // Optional: Add an onUploadProgress listener here if you want a percentage bar
    // onUploadProgress: (progressEvent) => {
    //   const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
    //   console.log(`${file.name} Upload Progress: ${percentCompleted}%`);
    // }
  });

  return response.data;
};
