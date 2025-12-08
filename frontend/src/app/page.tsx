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
        <ImagePreviewSidebar selectedItem={selectedItem} />
      </div>
    </div>
  );
}
