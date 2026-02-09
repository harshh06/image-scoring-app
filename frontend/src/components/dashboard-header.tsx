// frontend/src/components/dashboard-header.tsx

import { Button } from "@/components/ui/button";
import { Download, Database, CheckCircle2, Upload, History } from "lucide-react";

// Unified export data format for both upload and history tabs
export interface ExportDataItem {
  filename: string;
  serial_number: string;
  sample_id: string;
  score_architecture: number;
  score_atrophy: number;
  score_complexes: number;
  score_fibrosis: number;
  score_total: number;
}

export type TabType = "upload" | "history";

interface DashboardHeaderProps {
  exportData: ExportDataItem[];
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
}

export function DashboardHeader({
  exportData,
  activeTab,
  onTabChange,
}: DashboardHeaderProps) {
  const handleExport = () => {
    if (exportData.length === 0) return;

    // 1. Define CSV Headers
    const headers = [
      "Sample ID",
      "Serial Number",
      "Pancreatic Architecture",
      "Glandular Atrophy",
      "Pseudotubular Complexes",
      "Fibrosis",
      "Total Score",
    ];

    // 2. Convert Data to CSV Rows
    const rows = exportData.map((item) => [
      item.sample_id,
      // item.filename,
      item.serial_number,
      item.score_architecture,
      item.score_atrophy,
      item.score_complexes,
      item.score_fibrosis,
      item.score_total,
    ]);

    // 3. Join with commas and newlines
    const csvContent = [
      headers.join(","),
      ...rows.map((row) => row.join(",")),
    ].join("\n");

    // 4. Trigger Download
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute(
      "download",
      `scoring_results_${new Date().toISOString().split("T")[0]}.csv`
    );
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const completedCount = exportData.length;

  return (
    <header className="border-b border-border bg-card">
      <div className="flex h-16 items-center justify-between px-6 lg:px-8">
        <div className="flex items-center gap-6">
          {/* Logo and Title */}
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
              <Database className="h-5 w-5 text-primary-foreground" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-foreground">
                Histopathology Scoring system
              </h1>
            </div>
          </div>

          {/* Tab Navigation */}
          <nav className="flex items-center gap-1 ml-8">
            <Button
              variant={activeTab === "upload" ? "default" : "ghost"}
              size="sm"
              onClick={() => onTabChange("upload")}
              className={`gap-2 transition-all duration-200 ${
                activeTab === "upload"
                  ? "shadow-md"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Upload className="h-4 w-4" />
              Upload
            </Button>
            <Button
              variant={activeTab === "history" ? "default" : "ghost"}
              size="sm"
              onClick={() => onTabChange("history")}
              className={`gap-2 transition-all duration-200 ${
                activeTab === "history"
                  ? "shadow-md"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <History className="h-4 w-4" />
              History
            </Button>
          </nav>
        </div>

        <div className="flex items-center gap-4">
          <span className="text-sm text-muted-foreground flex items-center gap-1">
            <CheckCircle2 className="h-4 w-4 text-green-500" />
            Processed:{" "}
            <span className="font-semibold text-foreground">
              {completedCount}
            </span>
          </span>

          <Button
            className="gap-2"
            disabled={completedCount === 0}
            onClick={handleExport}
          >
            <Download className="h-4 w-4" />
            Export CSV
          </Button>
        </div>
      </div>
    </header>
  );
}
