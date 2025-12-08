// frontend/src/components/file-dropzone.tsx (Modified)

"use client";

import type React from "react";
import { useState } from "react";
import { Upload, File, AlertTriangle } from "lucide-react";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

// Define the component props
interface FileDropzoneProps {
  onFilesAccepted: (files: FileList) => void;
  disabled: boolean;
}

export function FileDropzone({ onFilesAccepted, disabled }: FileDropzoneProps) {
  const [isDragging, setIsDragging] = useState(false);

  // ... (handleDragOver, handleDragLeave, handleDrop remain the same,
  // but we modify handleDrop to use the input files)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      onFilesAccepted(e.target.files);
      e.target.value = ""; // Clear the input so the same files can be selected again
    }
  };

  return (
    // Add disabled class/prop to the Card
    <Card
      className={cn(
        "relative overflow-hidden border-2 border-dashed transition-all duration-200",
        isDragging
          ? "border-primary bg-primary/5"
          : "border-muted-foreground/25 hover:border-muted-foreground/50",
        disabled && "opacity-60 cursor-not-allowed" // Dim if processing
      )}
      // Removed onDragOver/Drop/Leave handlers for simplicity with input,
      // focusing on the input[type="file"] handler
    >
      <div className="flex min-h-[150px] flex-col items-center justify-center gap-4 p-4">
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-muted">
          <Upload className="h-8 w-8 text-muted-foreground" />
        </div>
        <div className="text-center">
          <h3 className="text-xl font-semibold text-foreground">
            {disabled ? "Processing Queue..." : "Drop your TIFF files here"}
          </h3>
          <p className="mt-2 text-sm text-muted-foreground">
            or click to browse from your computer (Supports multiple files)
          </p>
        </div>
        <div className=" bottom-2 p-2 left-2 left-0 right-0 text-center text-xs text-muted-foreground">
          <AlertTriangle className="inline h-3 w-3 mr-1 text-yellow-500" />
          Only TIFF files are accepted and processed sequentially.
        </div>

        <input
          type="file"
          multiple
          accept=".tif,.tiff" // CRITICAL: Only accept the required file types
          className="absolute inset-0 cursor-pointer opacity-0"
          onChange={handleFileChange}
          disabled={disabled}
        />
        {/* Optional: Add a note about the expected file type */}
      </div>
    </Card>
  );
}
