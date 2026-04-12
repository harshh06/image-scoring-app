// frontend/src/services/api.ts

import axios from "axios";

// Get the backend URL from environment variables, defaulting to localhost
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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
  sample_id?: string;
  scores: ScoreData;
  display_url: string; // URL to the generated thumbnail
  db_id: number;
}

// History item from the database
export interface HistoryItem {
  id: number;
  filename: string;
  serial_number: string;
  sample_id: string;
  created_at: string;
  updated_at: string;
  score_architecture: number;
  score_atrophy: number;
  score_complexes: number;
  score_fibrosis: number;
  score_total: number;
}

// Grouped history data by sample_id
export interface GroupedHistory {
  [sample_id: string]: HistoryItem[];
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
  });

  return response.data;
};

/**
 * Fetches all previously scored images from the database.
 * @returns A Promise resolving to an array of HistoryItem objects.
 */
export const fetchHistory = async (): Promise<HistoryItem[]> => {
  console.log(`[API] Fetching history from: ${API_URL}`);
  
  const response = await axios.get(`${API_URL}/api/scores`);
  return response.data;
};

/**
 * Updates a score in the database.
 * @param id The database ID of the record.
 * @param updates The partial update object.
 * @returns A Promise resolving to the updated record.
 */
export const updateScore = async (
  id: number,
  updates: Partial<{
    "Pancreatic Architecture": number;
    "Glandular Atrophy": number;
    "Pseudotubular Complexes": number;
    Fibrosis: number;
  }>
): Promise<HistoryItem> => {
  console.log(`[API] Updating score ${id}:`, updates);
  
  const response = await axios.put(`${API_URL}/api/scores/${id}`, updates);
  return response.data;
};

/**
 * Groups history items by sample_id and sorts each group by serial_number.
 * @param items Array of history items.
 * @returns Grouped and sorted history object.
 */
export const groupAndSortHistory = (items: HistoryItem[]): GroupedHistory => {
  const grouped: GroupedHistory = {};

  // Group by sample_id
  items.forEach((item) => {
    const sampleId = item.sample_id || "Unknown";
    if (!grouped[sampleId]) {
      grouped[sampleId] = [];
    }
    grouped[sampleId].push(item);
  });

  // Sort each group by serial_number
  Object.keys(grouped).forEach((sampleId) => {
    grouped[sampleId].sort((a, b) => {
      // Extract numeric part from serial_number for proper sorting
      // e.g., "S-3618-02" should come before "S-3618-10"
      const aMatch = a.serial_number.match(/-(\d+)$/);
      const bMatch = b.serial_number.match(/-(\d+)$/);
      
      if (aMatch && bMatch) {
        return parseInt(aMatch[1]) - parseInt(bMatch[1]);
      }
      return a.serial_number.localeCompare(b.serial_number);
    });
  });

  return grouped;
};
