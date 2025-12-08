// frontend/src/components/dashboard-header.tsx

import { Button } from "@/components/ui/button";
import { Download, Database, CheckCircle2 } from "lucide-react";
import { ProcessedResult } from "@/services/api";

interface Result {
  file: string;
  id: string;
  status: string;
  result: ProcessedResult;
}

interface DashboardHeaderProps {
  results: Result[];
}

export function DashboardHeader({ results }: DashboardHeaderProps) {
  const handleExport = () => {
    if (results.length === 0) return;

    // 1. Define CSV Headers
    const headers = [
      "Filename",
      "Serial Number",
      "Pancreatic Architecture",
      "Glandular Atrophy",
      "Pseudotubular Complexes",
      "Fibrosis",
      "Total Score",
    ];

    // 2. Convert Data to CSV Rows
    const rows = results.map((r: Result) => {
      const result = r.result;
      return [
        result.filename,
        result.serial_number,
        result.scores["Pancreatic Architecture"],
        result.scores["Glandular Atrophy"],
        result.scores["Pseudotubular Complexes"],
        result.scores["Fibrosis"],
        result.scores.Total,
      ];
    });

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

  const completedCount = results.length;

  return (
    <header className="border-b border-border bg-card">
      <div className="flex h-16 items-center justify-between px-6 lg:px-8">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
            <Database className="h-5 w-5 text-primary-foreground" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-foreground">
              Scientific Data Dashboard
            </h1>
          </div>
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
