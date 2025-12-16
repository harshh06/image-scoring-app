// frontend/src/app/page.tsx
"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
// Import the API service function
import { uploadImage, ProcessedResult } from "@/services/api";
// Import components
import { DashboardHeader } from "@/components/dashboard-header";
import { FileDropzone } from "@/components/file-dropzone";
import { FileStatusList } from "@/components/file-status-list";
import { ImagePreviewSidebar } from "@/components/image-preview-sidebar";
import axios from "axios";

// Define the shape of a queued item (Exported for use in FileStatusList)
export interface QueueItem {
  id: string;
  file: File;
  status: "pending" | "uploading" | "completed" | "error";
  error?: string;
  result?: ProcessedResult;
}

export default function DashboardPage() {
  const [queue, setQueue] = useState<QueueItem[]>([]);
  // isProcessing acts as a global lock to ensure only one upload runs at a time
  const [isProcessing, setIsProcessing] = useState(false);
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);
  const [scoreUpdating, setScoreUpdating] = useState<boolean>(false);

  // Memoized lists for displaying data
  const results = useMemo(() => queue.filter((item) => item.result), [queue]);
  const selectedItem = useMemo(
    () => queue.find((item) => item.id === selectedItemId),
    [queue, selectedItemId]
  );

  // --- 1. Handle File Selection: Add files to the queue ---
  const handleFileSelect = (fileList: FileList) => {
    const newFiles = Array.from(fileList)
      .filter(
        (file) =>
          // Filter only TIFF files as required by the backend
          file.name.toLowerCase().endsWith(".tif") ||
          file.name.toLowerCase().endsWith(".tiff")
      )
      .map((file) => ({
        id: Math.random().toString(36).substring(2, 9), // Generate unique ID
        file,
        status: "pending" as const,
      }));

    setQueue((prev) => [...prev, ...newFiles]);
  };

  // --- 2. The Sequential Processor (The Core Logic) ---
  const processQueue = useCallback(async () => {
    // 🔒 If already busy, or queue is empty, exit.
    if (isProcessing) return;

    // Find the index of the next pending item
    const nextItemIndex = queue.findIndex((item) => item.status === "pending");

    if (nextItemIndex === -1) return; // All items processed or finished

    // --- A. Acquire Lock & Update Status ---
    setIsProcessing(true);

    // Set the status to 'uploading' immediately
    setQueue((prev) => {
      const newQ = [...prev];
      newQ[nextItemIndex].status = "uploading";
      return newQ;
    });

    const item = queue[nextItemIndex];
    const itemId = item.id;

    try {
      // --- B. API Call: This is the critical, time-consuming step ---
      const result = await uploadImage(item.file);

      // --- C. Success: Release Lock & Update Queue ---
      setQueue((prev) => {
        const newQ = [...prev];
        const index = newQ.findIndex((q) => q.id === itemId);
        if (index > -1) {
          newQ[index].status = "completed";
          newQ[index].result = result;
        }
        return newQ;
      });
      // Automatically select the completed item to show its preview/scores
      setSelectedItemId(itemId);
    } catch (err) {
      // --- D. Error Handling ---
      setQueue((prev) => {
        const newQ = [...prev];
        const index = newQ.findIndex((q) => q.id === itemId);
        if (index > -1) {
          newQ[index].status = "error";
          newQ[index].error =
            err instanceof Error
              ? err.message
              : "Processing failed (check backend logs).";
        }
        return newQ;
      });
      console.error(`Error processing file ${item.file.name}:`, err);
    } finally {
      // --- E. Release Lock ---
      setIsProcessing(false);
    }
  }, [queue, isProcessing]);

  const handleScoreUpdate = async (
    itemId: string,
    metric: string,
    value: number
  ) => {
    // 1. Optimistic Update (Update UI immediately)
    setQueue((prev) => {
      const newQueue = [...prev];
      const index = newQueue.findIndex((item) => item.id === itemId);

      if (index === -1 || !newQueue[index].result) return prev;

      const scores = newQueue[index].result!.scores;
      // @ts-ignore
      scores[metric] = value;
      scores.Total =
        scores["Pancreatic Architecture"] +
        scores["Glandular Atrophy"] +
        scores["Pseudotubular Complexes"] +
        scores["Fibrosis"];
      scores.Total = Math.round(scores.Total * 100) / 100;

      return newQueue;
    });

    // 2. Background API Call to Save to DB
    const item = queue.find((q) => q.id === itemId);
    if (!item?.result?.db_id) return; // Can't save if we don't have a DB ID

    try {
      // Use the NEXT_PUBLIC_BACKEND_URL from env or localhost
      const API_URL =
        process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

      setScoreUpdating(true);

      await axios.put(`${API_URL}/api/scores/${item.result.db_id}`, {
        [metric]: value,
      });
      console.log(`Saved ${metric} update to DB`);
    } catch (err) {
      console.error("Failed to save score update:", err);
      setScoreUpdating(false);
    } finally {
      setTimeout(() => setScoreUpdating(false), 1000);
      // Optional: Revert UI change here if you want strict consistency
    }
  };

  // --- 3. Trigger the Processor ---
  // Reruns whenever the queue or processing status changes
  useEffect(() => {
    // Add a slight delay (100ms) to prevent excessive rapid firing during state updates
    const timer = setTimeout(() => {
      processQueue();
    }, 100);

    return () => clearTimeout(timer); // Cleanup timer if component unmounts
  }, [queue, isProcessing, processQueue]);

  return (
    <div className="flex h-screen flex-col bg-background">
      {/* Pass results for the export button to access the data */}
      <DashboardHeader results={results} />

      <div className="flex flex-1 overflow-hidden">
        {/* Main Content Area */}
        <main className="flex-1 overflow-y-auto">
          <div className="container mx-auto p-6 lg:p-8">
            <div className="space-y-6">
              {/* Dropzone receives the file handler and disabled state */}
              <FileDropzone
                onFilesAccepted={handleFileSelect}
                disabled={isProcessing}
              />

              {/* Status List receives the queue state */}
              <FileStatusList
                queue={queue}
                onItemSelected={setSelectedItemId}
                selectedItemId={selectedItemId}
              />
            </div>
          </div>
        </main>

        {/* Fixed Right Sidebar */}
        <ImagePreviewSidebar
          selectedItem={selectedItem}
          onScoreUpdate={handleScoreUpdate}
          scoreUpdating={scoreUpdating}
        />
      </div>
    </div>
  );
}
