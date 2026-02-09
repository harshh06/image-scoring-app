// frontend/src/app/page.tsx
"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
// Import the API service functions
import { uploadImage, ProcessedResult, HistoryItem, GroupedHistory, fetchHistory, groupAndSortHistory } from "@/services/api";
// Import components
import { DashboardHeader, TabType } from "@/components/dashboard-header";
import { FileDropzone } from "@/components/file-dropzone";
import { FileStatusList } from "@/components/file-status-list";
import { ImagePreviewSidebar } from "@/components/image-preview-sidebar";
import { HistoryList } from "@/components/history-list";
import { HistoryPreviewSidebar } from "@/components/history-preview-sidebar";
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

  // Tab management
  const [activeTab, setActiveTab] = useState<TabType>("upload");

  // History state
  const [selectedHistoryItem, setSelectedHistoryItem] =
    useState<HistoryItem | null>(null);
  const [historyScoreUpdating, setHistoryScoreUpdating] =
    useState<boolean>(false);

  
  const [groupedHistory, setGroupedHistory] = useState<GroupedHistory>({});
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());
  const [selectedGroups, setSelectedGroups] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Memoized lists for displaying data
  const results = useMemo(() => queue.filter((item) => item.result), [queue]);
  const selectedItem = useMemo(
    () => queue.find((item) => item.id === selectedItemId),
    [queue, selectedItemId]
  );

  // Compute export data based on active tab
  const exportData = useMemo(() => {
    if (activeTab === "upload") {
      // For upload tab, return processed results in compatible format
      return results
        .filter((r) => r.result)
        .map((r) => ({
          filename: r.result!.filename,
          serial_number: r.result!.serial_number,
          sample_id: r.result!.sample_id || "Unknown",
          score_architecture: r.result!.scores["Pancreatic Architecture"],
          score_atrophy: r.result!.scores["Glandular Atrophy"],
          score_complexes: r.result!.scores["Pseudotubular Complexes"],
          score_fibrosis: r.result!.scores["Fibrosis"],
          score_total: r.result!.scores.Total,
        }));
    } else {
      // For history tab, return items from selected groups
      const selectedItems: HistoryItem[] = [];
      selectedGroups.forEach((sampleId) => {
        if (groupedHistory[sampleId]) {
          selectedItems.push(...groupedHistory[sampleId]);
        }
      });
      return selectedItems.map((item) => ({
        filename: item.filename,
        serial_number: item.serial_number,
        sample_id: item.sample_id,
        score_architecture: item.score_architecture,
        score_atrophy: item.score_atrophy,
        score_complexes: item.score_complexes,
        score_fibrosis: item.score_fibrosis,
        score_total: item.score_total,
      }));
    }
  }, [activeTab, results, selectedGroups, groupedHistory]);

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

  // --- History Score Update Handler ---
  const handleHistoryScoreUpdate = async (
    itemId: number,
    metric: string,
    value: number
  ) => {
    if (!selectedHistoryItem) return;

    // 1. Optimistic Update (Update UI immediately)
    const updatedItem = { ...selectedHistoryItem };
    
    // Map metric names to database fields
    const metricToField: { [key: string]: keyof HistoryItem } = {
      "Pancreatic Architecture": "score_architecture",
      "Glandular Atrophy": "score_atrophy",
      "Pseudotubular Complexes": "score_complexes",
      Fibrosis: "score_fibrosis",
    };

    const field = metricToField[metric];
    if (field) {
      // @ts-ignore - we know these are number fields
      updatedItem[field] = value;
      // Recalculate total
      updatedItem.score_total =
        (updatedItem.score_architecture ?? 0) +
        (updatedItem.score_atrophy ?? 0) +
        (updatedItem.score_complexes ?? 0) +
        (updatedItem.score_fibrosis ?? 0);
      updatedItem.score_total =
        Math.round(updatedItem.score_total * 100) / 100;
    }

    setSelectedHistoryItem(updatedItem);

    // 2. Background API Call to Save to DB
    try {
      const API_URL =
        process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

      setHistoryScoreUpdating(true);

      await axios.put(`${API_URL}/api/scores/${itemId}`, {
        [metric]: value,
      });
      console.log(`Saved ${metric} update for history item ${itemId} to DB`);
    } catch (err) {
      console.error("Failed to save score update:", err);
      setHistoryScoreUpdating(false);
    } finally {
      setTimeout(() => setHistoryScoreUpdating(false), 1000);
    }
  };

  // --- Handle History Item Selection ---
  const handleHistoryItemSelect = (item: HistoryItem) => {
    setSelectedHistoryItem(item);
  };

  // Fetch history data on mount
  const loadHistory = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchHistory();
      const grouped = groupAndSortHistory(data);
      setGroupedHistory(grouped);
      // Expand all groups by default
      setExpandedGroups(new Set(Object.keys(grouped)));
    } catch (err) {
      console.error("Failed to fetch history:", err);
      setError(
        err instanceof Error ? err.message : "Failed to load history data"
      );
    } finally {
      setLoading(false);
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

  // Clear selection and reset state when switching tabs
  useEffect(() => {
    if (activeTab === "upload") {
      setSelectedHistoryItem(null);
      // Clear history selections when switching to upload
      setSelectedGroups(new Set());
    } else {
      loadHistory();
      setSelectedItemId(null);
      // Clear selected groups when switching to history (start fresh)
      setSelectedGroups(new Set());
    }
  }, [activeTab]);

  return (
    <div className="flex h-screen flex-col bg-background">
      {/* Pass exportData for the export button to access the data */}
      <DashboardHeader
        exportData={exportData}
        activeTab={activeTab}
        onTabChange={setActiveTab}
      />

      <div className="flex flex-1 overflow-hidden">
        {/* Main Content Area */}
        <main className="flex-1 overflow-y-auto">
          <div className="container mx-auto p-6 lg:p-8">
            <div className="space-y-6">
              {activeTab === "upload" ? (
                <>
                  {/* Upload Tab Content */}
                  <FileDropzone
                    onFilesAccepted={handleFileSelect}
                    disabled={isProcessing}
                  />
                  <FileStatusList
                    queue={queue}
                    onItemSelected={setSelectedItemId}
                    selectedItemId={selectedItemId}
                  />
                </>
              ) : (
                <>
                  {/* History Tab Content */}
                  <HistoryList
                    onItemSelected={handleHistoryItemSelect}
                    selectedItemId={selectedHistoryItem?.id ?? null}
                    groupedHistory={groupedHistory}
                    expandedGroups={expandedGroups}
                    setExpandedGroups={setExpandedGroups}
                    selectedGroups={selectedGroups}
                    setSelectedGroups={setSelectedGroups}
                    loading={loading}
                    error={error}
                    loadHistory={loadHistory}
                  />
                </>
              )}
            </div>
          </div>
        </main>

        {/* Fixed Right Sidebar - switches based on active tab */}
        {activeTab === "upload" ? (
          <ImagePreviewSidebar
            selectedItem={selectedItem}
            onScoreUpdate={handleScoreUpdate}
            scoreUpdating={scoreUpdating}
          />
        ) : (
          <HistoryPreviewSidebar
            selectedItem={selectedHistoryItem}
            onScoreUpdate={handleHistoryScoreUpdate}
            scoreUpdating={historyScoreUpdating}
          />
        )}
      </div>
    </div>
  );
}
