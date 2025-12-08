// frontend/src/components/file-status-list.tsx (Modified)

"use client";

import type React from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2, Loader2, AlertCircle, FileText, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { QueueItem } from "@/app/page"; // Import the defined QueueItem interface

// Define props for the list component
interface FileStatusListProps {
  queue: QueueItem[];
  onItemSelected: (id: string) => void;
  selectedItemId: string | null;
}

export function FileStatusList({
  queue,
  onItemSelected,
  selectedItemId,
}: FileStatusListProps) {
  // We only show the list if there are items in the queue
  if (queue.length === 0) return null;

  return (
    <Card className="overflow-hidden">
      <div className="border-b border-border bg-muted/30 px-6 py-4">
        <h2 className="text-lg font-semibold text-foreground">
          Processing Queue ({queue.length} files)
        </h2>
        <p className="text-sm text-muted-foreground">
          Track your uploaded files
        </p>
      </div>

      <div className="divide-y divide-border max-h-96 overflow-y-auto">
        {/* Iterate over the REAL queue data */}
        {queue.map((item) => (
          <FileStatusItem
            key={item.id}
            item={item}
            isSelected={item.id === selectedItemId}
            onClick={() => onItemSelected(item.id)}
          />
        ))}
      </div>
    </Card>
  );
}

// Update the item component to use the real QueueItem type
function FileStatusItem({
  item,
  isSelected,
  onClick,
}: {
  item: QueueItem;
  isSelected: boolean;
  onClick: () => void;
}) {
  const getStatusIcon = () => {
    switch (item.status) {
      case "completed":
        return <CheckCircle2 className="h-5 w-5 text-green-500" />;
      case "uploading":
        return <Loader2 className="h-5 w-5 animate-spin text-primary" />;
      case "pending":
        return <div className="h-2 w-2 bg-gray-300 rounded-full" />;
      case "error":
        return <AlertCircle className="h-5 w-5 text-destructive" />;
    }
  };

  const getStatusBadge = () => {
    switch (item.status) {
      case "completed":
        return (
          <Badge
            variant="outline"
            className="border-green-500/50 text-green-600 dark:text-green-400"
          >
            Done
          </Badge>
        );
      case "uploading":
        return (
          <Badge variant="outline" className="border-blue-500/50 text-blue-500">
            Uploading...
          </Badge>
        );
      case "pending":
        return (
          <Badge variant="outline" className="border-gray-500/50 text-gray-500">
            Pending
          </Badge>
        );
      case "error":
        return (
          <Badge
            variant="outline"
            className="border-destructive/50 text-destructive"
          >
            Failed
          </Badge>
        );
    }
  };

  const file = item.file;
  const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
  const totalScore = item.result ? item.result.scores.Total : "N/A";

  return (
    <div
      className={`group flex items-center gap-4 px-6 py-4 transition-colors cursor-pointer ${
        isSelected ? "bg-primary/10" : "hover:bg-muted/50"
      }`}
      onClick={onClick}
    >
      <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
        <FileText className="h-5 w-5 text-muted-foreground" />
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-3">
          <p className="truncate font-medium text-foreground">{file.name}</p>
          {getStatusBadge()}
        </div>
        <div className="mt-1 flex items-center gap-3 text-sm text-muted-foreground">
          <span>{sizeMB} MB</span>
        </div>

        {item.status === "error" && (
          <p className="text-xs text-destructive mt-1 truncate">
            Error: {item.error}
          </p>
        )}
      </div>

      <div className="text-right">
        <span className="text-sm font-bold text-gray-900 dark:text-gray-100">
          Score: {totalScore}
        </span>
        {getStatusIcon()}
      </div>
    </div>
  );
}
