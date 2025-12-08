"use client";

import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ImageIcon } from "lucide-react";
import Image from "next/image"; // For optimized image loading
import { QueueItem } from "@/app/page"; // Import the type

// Define props to receive the selected item
interface ImagePreviewSidebarProps {
  selectedItem: QueueItem | undefined;
}

export function ImagePreviewSidebar({
  selectedItem,
}: ImagePreviewSidebarProps) {
  // Check if an item is selected AND has processed results
  const result = selectedItem?.result;
  const scores = result?.scores;

  return (
    <aside className="w-80 border-l border-border bg-sidebar">
      <div className="flex h-full flex-col">
        <div className="border-b border-sidebar-border bg-sidebar-accent/50 px-6 py-4">
          <h2 className="text-lg font-semibold text-sidebar-foreground">
            {result ? result.filename : "Image Preview"}
          </h2>
          <p className="text-sm text-sidebar-foreground/60">
            {result
              ? `Scores for ${result.serial_number}`
              : "Select a file to preview"}
          </p>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          <Card className="border-dashed">
            <div className="flex min-h-[300px] flex-col items-center justify-center gap-4 p-4 text-center">
              {result && result?.display_url ? (
                <div className="relative w-full h-auto aspect-square rounded-lg overflow-hidden">
                  {/* Display the thumbnail image from the backend */}
                  <Image
                    src={result?.display_url}
                    alt={`Preview of ${result.filename}`}
                    fill
                    style={{ objectFit: "contain" }}
                    className="p-1"
                  />
                </div>
              ) : (
                <div className="flex min-h-[300px] flex-col items-center justify-center gap-4 p-8 text-center">
                  <div className="flex h-16 w-16 items-center justify-center rounded-full bg-muted">
                    <ImageIcon className="h-8 w-8 text-muted-foreground" />
                  </div>
                  <p className="font-medium text-muted-foreground">
                    {selectedItem?.status === "uploading"
                      ? "Loading..."
                      : "No image selected"}
                  </p>
                </div>
              )}
            </div>
          </Card>

          <div className="mt-6 space-y-4">
            <div>
              <h3 className="text-sm font-semibold text-sidebar-foreground mb-3">
                AI Scores
              </h3>
              <div className="space-y-2 text-sm">
                {scores ? (
                  <>
                    {Object.entries(scores).map(([key, value]) => (
                      <div key={key} className="flex justify-between">
                        <span className="text-sidebar-foreground/60">
                          {key.replace(/([A-Z])/g, " $1").trim()}
                        </span>
                        <Badge variant="outline" className="text-xs font-mono">
                          {value.toFixed(2)}
                        </Badge>
                      </div>
                    ))}
                    <div className="border-t border-sidebar-border pt-2 font-bold">
                      <div className="flex justify-between">
                        <span>Total Score</span>
                        <span className="text-sidebar-primary">
                          {scores.Total.toFixed(2)}
                        </span>
                      </div>
                    </div>
                  </>
                ) : (
                  <span className="text-sidebar-foreground/60">
                    — Processing —
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
}
