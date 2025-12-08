"use client";

import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ImageIcon, Save, Loader2, CheckCircle2 } from "lucide-react";
import Image from "next/image";
import { QueueItem } from "@/app/page";

interface ImagePreviewSidebarProps {
  selectedItem: QueueItem | undefined;
  // New prop to communicate changes back to parent
  onScoreUpdate: (itemId: string, metric: string, value: number) => void;
  scoreUpdating: boolean;
}

export function ImagePreviewSidebar({
  selectedItem,
  onScoreUpdate,
  scoreUpdating,
}: ImagePreviewSidebarProps) {
  const result = selectedItem?.result;
  const scores = result?.scores;

  // Helper to handle input changes safely
  const handleInputChange = (metricKey: string, valueStr: string) => {
    if (!selectedItem) return;

    // Parse the number (handle empty string as 0)
    let val = parseFloat(valueStr);
    if (isNaN(val)) val = 0;

    // Clamp values if you want (e.g., 0 to 4)
    // if (val > 4) val = 4;
    // if (val < 0) val = 0;

    onScoreUpdate(selectedItem.id, metricKey, val);
  };

  const autoSaveText = scoreUpdating ? "Auto-saving..." : "Saved";

  return (
    <aside className="w-96 border-l border-border bg-sidebar flex flex-col h-full shadow-xl z-10">
      {/* HEADER */}
      <div className="border-b border-sidebar-border bg-sidebar-accent/50 px-6 py-4">
        <h2
          className="text-lg font-semibold text-sidebar-foreground truncate"
          title={result?.filename}
        >
          {result ? result.filename : "Image Preview"}
        </h2>
        <p className="text-sm text-sidebar-foreground/60">
          {result
            ? `Serial: ${result.serial_number}`
            : "Select a file to review scores"}
        </p>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* IMAGE AREA */}
        <Card className="border-dashed overflow-hidden bg-muted/20">
          <div className="relative min-h-[300px] flex items-center justify-center">
            {result && result.display_url ? (
              <div className="relative w-full h-[300px]">
                <Image
                  src={result.display_url}
                  alt="Preview"
                  fill
                  className="object-contain"
                />
              </div>
            ) : (
              <div className="flex flex-col items-center gap-2 text-muted-foreground p-8">
                <ImageIcon className="h-10 w-10 opacity-50" />
                <span className="text-sm">No image selected</span>
              </div>
            )}
          </div>
        </Card>

        {/* EDITABLE SCORE AREA */}
        {scores ? (
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
              {Object.entries(scores).map(([key, value]) => {
                // Skip 'Total' in the input list, we calculate it automatically
                if (key === "Total") return null;

                return (
                  <div
                    key={key}
                    className="space-y-1.5 flex justify-between align-center"
                  >
                    <div>
                      <Label className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">
                        {key.replace(/([A-Z])/g, " $1").trim()}
                      </Label>
                    </div>
                    <div className="flex items-center gap-3">
                      {/* The Slider/Input */}
                      <Input
                        type="number"
                        // className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                        step="0.1"
                        min="0"
                        max="4"
                        value={value}
                        onChange={(e) => handleInputChange(key, e.target.value)}
                      />
                    </div>
                  </div>
                );
              })}
            </div>

            {/* TOTAL SCORE CARD */}
            <Card className="p-4 bg-primary/5 border-primary/20">
              <div className="flex justify-between items-center">
                <span className="font-bold text-foreground">Total Score</span>
                <span className="text-2xl font-bold text-primary">
                  {scores.Total.toFixed(2)}
                </span>
              </div>
            </Card>
          </div>
        ) : (
          <div className="text-center text-sm text-muted-foreground py-10">
            {selectedItem?.status === "uploading"
              ? "Processing with AI..."
              : "Select a processed item to edit scores."}
          </div>
        )}
      </div>
    </aside>
  );
}
