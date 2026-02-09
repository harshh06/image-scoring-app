// frontend/src/components/history-preview-sidebar.tsx

"use client";

import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Save, Loader2, Calendar, Hash, FileText } from "lucide-react";
import { HistoryItem } from "@/services/api";

interface HistoryPreviewSidebarProps {
  selectedItem: HistoryItem | null;
  onScoreUpdate: (
    itemId: number,
    metric: string,
    value: number
  ) => void;
  scoreUpdating: boolean;
}

// Map from display keys to database field keys
const metricDisplayMap: { display: string; dbField: string }[] = [
  { display: "Pancreatic Architecture", dbField: "score_architecture" },
  { display: "Glandular Atrophy", dbField: "score_atrophy" },
  { display: "Pseudotubular Complexes", dbField: "score_complexes" },
  { display: "Fibrosis", dbField: "score_fibrosis" },
];

export function HistoryPreviewSidebar({
  selectedItem,
  onScoreUpdate,
  scoreUpdating,
}: HistoryPreviewSidebarProps) {
  // Helper to get score value from history item
  const getScoreValue = (dbField: string): number => {
    if (!selectedItem) return 0;
    switch (dbField) {
      case "score_architecture":
        return selectedItem.score_architecture ?? 0;
      case "score_atrophy":
        return selectedItem.score_atrophy ?? 0;
      case "score_complexes":
        return selectedItem.score_complexes ?? 0;
      case "score_fibrosis":
        return selectedItem.score_fibrosis ?? 0;
      default:
        return 0;
    }
  };

  // Helper to handle input changes safely
  const handleInputChange = (dbField: string, valueStr: string) => {
    if (!selectedItem) return;

    // Parse the number (handle empty string as 0)
    let val = parseFloat(valueStr);
    if (isNaN(val)) val = 0;

    // Map database field to API field name
    const apiFieldMap: { [key: string]: string } = {
      score_architecture: "Pancreatic Architecture",
      score_atrophy: "Glandular Atrophy",
      score_complexes: "Pseudotubular Complexes",
      score_fibrosis: "Fibrosis",
    };

    onScoreUpdate(selectedItem.id, apiFieldMap[dbField], val);
  };

  const autoSaveText = scoreUpdating ? "Auto-saving..." : "Saved";

  const formattedDate = selectedItem
    ? new Date(selectedItem.updated_at).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })
    : "";

  return (
    <aside className="w-96 border-l border-border bg-sidebar flex flex-col h-full shadow-xl z-10">
      {/* HEADER */}
      <div className="border-b border-sidebar-border bg-sidebar-accent/50 px-6 py-4">
        <h2
          className="text-lg font-semibold text-sidebar-foreground truncate"
          title={selectedItem?.filename}
        >
          {selectedItem ? selectedItem.filename : "Score Details"}
        </h2>
        <p className="text-sm text-sidebar-foreground/60">
          {selectedItem
            ? `Serial: ${selectedItem.serial_number}`
            : "Select an image to review scores"}
        </p>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* METADATA SECTION */}
        {selectedItem ? (
          <>
            {/* File Info Card */}
            <Card className="p-4 bg-muted/20 border-dashed">
              <div className="flex items-center gap-3 mb-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                  <FileText className="h-6 w-6 text-primary" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-foreground truncate" title={selectedItem.filename}>
                    {selectedItem.filename}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {selectedItem.serial_number}
                  </p>
                </div>
              </div>
              
              <div className="space-y-2 text-sm border-t border-border pt-3">
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Hash className="h-4 w-4" />
                  <span>Sample ID:</span>
                  <span className="font-medium text-foreground">
                    {selectedItem.sample_id}
                  </span>
                </div>
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Calendar className="h-4 w-4" />
                  <span>Last Updated:</span>
                  <span className="font-medium text-foreground">{formattedDate}</span>
                </div>
              </div>
            </Card>

            {/* EDITABLE SCORE AREA */}
            <div className="space-y-5 animate-in fade-in slide-in-from-bottom-4 duration-500">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-sidebar-foreground">
                  Pathology Scores (Editable)
                </h3>
                <Badge
                  variant="outline"
                  className="bg-primary/10 text-primary border-primary/20"
                >
                  {scoreUpdating ? (
                    <Loader2 className="w-3 h-3 animate-spin" />
                  ) : (
                    <Save className="w-3 h-3 mr-1" />
                  )}
                  {autoSaveText}
                </Badge>
              </div>

              <div className="grid gap-4">
                {metricDisplayMap.map(({ display, dbField }) => (
                  <div
                    key={dbField}
                    className="space-y-1.5 flex justify-between align-center"
                  >
                    <div>
                      <Label className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">
                        {display}
                      </Label>
                    </div>
                    <div className="flex items-center gap-3">
                      <Input
                        type="number"
                        step="0.1"
                        min="0"
                        max="4"
                        value={getScoreValue(dbField)}
                        onChange={(e) => handleInputChange(dbField, e.target.value)}
                      />
                    </div>
                  </div>
                ))}
              </div>

              {/* TOTAL SCORE CARD */}
              <Card className="p-4 bg-primary/5 border-primary/20">
                <div className="flex justify-between items-center">
                  <span className="font-bold text-foreground">Total Score</span>
                  <span className="text-2xl font-bold text-primary">
                    {(selectedItem.score_total ?? 0).toFixed(2)}
                  </span>
                </div>
              </Card>
            </div>
          </>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-center text-sm text-muted-foreground py-10">
            <FileText className="h-12 w-12 mb-4 opacity-30" />
            <p>Select an image from the history list</p>
            <p className="text-xs mt-1">to view and edit its scores</p>
          </div>
        )}
      </div>
    </aside>
  );
}
