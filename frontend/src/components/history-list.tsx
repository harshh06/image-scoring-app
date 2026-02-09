// frontend/src/components/history-list.tsx

"use client";

import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  ChevronDown,
  ChevronRight,
  FileText,
  Loader2,
  AlertCircle,
  RefreshCw,
  FolderOpen,
  History as HistoryIcon,
  CheckSquare,
  Square,
  Search,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  HistoryItem,
  GroupedHistory,
  fetchHistory,
  groupAndSortHistory,
} from "@/services/api";

// Props for the HistoryList component
interface HistoryListProps {
  onItemSelected: (item: HistoryItem) => void;
  selectedItemId: number | null;
  groupedHistory: GroupedHistory;
  expandedGroups: Set<string>;
  selectedGroups: Set<string>;
  loading: boolean;
  error: string | null;
  setExpandedGroups: (groups: Set<string>) => void;
  setSelectedGroups: (groups: Set<string>) => void;
  loadHistory: () => void;
}

export function HistoryList({
  onItemSelected,
  selectedItemId,
  groupedHistory,
  expandedGroups,
  selectedGroups,
  loading,
  error,
  setExpandedGroups,
  setSelectedGroups,
  loadHistory,
}: HistoryListProps) {
    
  // Search functionality
  const [searchQuery, setSearchQuery] = useState("");

  const toggleGroup = (sampleId: string) => {
    const newSet = new Set(expandedGroups);
    if (newSet.has(sampleId)) {
      newSet.delete(sampleId);
    } else {
      newSet.add(sampleId);
    }
    setExpandedGroups(newSet);
  };

  // Toggle selection of a group for export
  const toggleSelectGroup = (sampleId: string) => {
    const newSet = new Set(selectedGroups);
    if (newSet.has(sampleId)) {
      newSet.delete(sampleId);
    } else {
      newSet.add(sampleId);
    }
    setSelectedGroups(newSet);
  };

  // Remove a group from selection
  const removeSelectedGroup = (sampleId: string) => {
    const newSet = new Set(selectedGroups);
    newSet.delete(sampleId);
    setSelectedGroups(newSet);
  };

  // Count selected items
  const selectedItemCount = Array.from(selectedGroups).reduce((acc, sampleId) => {
    return acc + (groupedHistory[sampleId]?.length || 0);
  }, 0);

  const totalItems = Object.values(groupedHistory).reduce(
    (acc, items) => acc + items.length,
    0
  );

  // Filter and sort sample IDs based on search query
  const allSampleIds = Object.keys(groupedHistory).sort();
  const filteredSampleIds = searchQuery.trim()
    ? allSampleIds.filter((sampleId) =>
        sampleId.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : allSampleIds;

  if (loading) {
    return (
      <Card className="overflow-hidden">
        <div className="border-b border-border bg-muted/30 px-6 py-4">
          <div className="flex items-center gap-2">
            <HistoryIcon className="h-5 w-5 text-primary" />
            <h2 className="text-lg font-semibold text-foreground">
              Scored Images History
            </h2>
          </div>
        </div>
        <div className="flex items-center justify-center py-16">
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <p className="text-sm text-muted-foreground">
              Loading history data...
            </p>
          </div>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="overflow-hidden">
        <div className="border-b border-border bg-muted/30 px-6 py-4">
          <div className="flex items-center gap-2">
            <HistoryIcon className="h-5 w-5 text-primary" />
            <h2 className="text-lg font-semibold text-foreground">
              Scored Images History
            </h2>
          </div>
        </div>
        <div className="flex items-center justify-center py-16">
          <div className="flex flex-col items-center gap-3">
            <AlertCircle className="h-8 w-8 text-destructive" />
            <p className="text-sm text-destructive">{error}</p>
            <Button variant="outline" size="sm" onClick={loadHistory}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          </div>
        </div>
      </Card>
    );
  }

  if (totalItems === 0) {
    return (
      <Card className="overflow-hidden">
        <div className="border-b border-border bg-muted/30 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <HistoryIcon className="h-5 w-5 text-primary" />
              <h2 className="text-lg font-semibold text-foreground">
                Scored Images History
              </h2>
            </div>
            <Button variant="ghost" size="sm" onClick={loadHistory}>
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        </div>
        <div className="flex items-center justify-center py-16">
          <div className="flex flex-col items-center gap-3">
            <FolderOpen className="h-12 w-12 text-muted-foreground/50" />
            <p className="text-sm text-muted-foreground">
              No scored images found
            </p>
            <p className="text-xs text-muted-foreground/70">
              Upload and process images to see them here
            </p>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <Card className="overflow-hidden">
      <div className="border-b border-border bg-muted/30 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2">
              <HistoryIcon className="h-5 w-5 text-primary" />
              <h2 className="text-lg font-semibold text-foreground">
                Scored Images History
              </h2>
              <Badge variant="secondary" className="ml-2">
                {totalItems} images
              </Badge>
            </div>
            <p className="text-sm text-muted-foreground mt-1">
              Grouped by sample ID • Sorted by serial number
            </p>
          </div>
          <Button variant="ghost" size="sm" onClick={loadHistory}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Search Bar */}
      <div className="px-6 py-3 border-b border-border bg-background">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search by sample ID (e.g., S-3618)..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-10 py-2 text-sm border border-border rounded-lg bg-muted/30 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery("")}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
        {searchQuery && (
          <p className="text-xs text-muted-foreground mt-2">
            Showing {filteredSampleIds.length} of {allSampleIds.length} folders
          </p>
        )}
      </div>

      {/* Selected Groups Display */}
      {selectedGroups.size > 0 && (
        <div className="px-6 py-3 border-b border-border bg-primary/5">
          <div className="flex items-center gap-2 mb-2">
            <CheckSquare className="h-4 w-4 text-primary" />
            <span className="text-sm font-medium text-foreground">
              Selected for Export: {selectedGroups.size} folders ({selectedItemCount} images)
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            {Array.from(selectedGroups).sort().map((sampleId) => (
              <Badge
                key={sampleId}
                variant="secondary"
                className="bg-primary/10 text-primary hover:bg-primary/20 cursor-pointer flex items-center gap-1 pr-1"
              >
                <FolderOpen className="h-3 w-3" />
                {sampleId}
                <span className="text-xs text-primary/70 ml-1">
                  ({groupedHistory[sampleId]?.length || 0})
                </span>
                <button
                  onClick={() => removeSelectedGroup(sampleId)}
                  className="ml-1 p-0.5 rounded-full hover:bg-primary/20 transition-colors"
                  title="Remove from selection"
                >
                  <X className="h-3 w-3" />
                </button>
              </Badge>
            ))}
          </div>
        </div>
      )}

      <div className="max-h-[calc(100vh-400px)] overflow-y-auto">
        {filteredSampleIds.length === 0 ? (
          <div className="flex items-center justify-center py-12">
            <div className="flex flex-col items-center gap-3">
              <Search className="h-8 w-8 text-muted-foreground/50" />
              <p className="text-sm text-muted-foreground">
                No folders match "{searchQuery}"
              </p>
            </div>
          </div>
        ) : (
          filteredSampleIds.map((sampleId) => (
            <SampleGroup
              key={sampleId}
              sampleId={sampleId}
              items={groupedHistory[sampleId]}
              isExpanded={expandedGroups.has(sampleId)}
              isSelected={selectedGroups.has(sampleId)}
              onToggle={() => toggleGroup(sampleId)}
              onSelectToggle={() => toggleSelectGroup(sampleId)}
              onItemSelected={onItemSelected}
              selectedItemId={selectedItemId}
            />
          ))
        )}
      </div>
    </Card>
  );
}

// Component for each sample group
interface SampleGroupProps {
  sampleId: string;
  items: HistoryItem[];
  isExpanded: boolean;
  isSelected: boolean;
  onToggle: () => void;
  onSelectToggle: () => void;
  onItemSelected: (item: HistoryItem) => void;
  selectedItemId: number | null;
}

function SampleGroup({
  sampleId,
  items,
  isExpanded,
  isSelected,
  onToggle,
  onSelectToggle,
  onItemSelected,
  selectedItemId,
}: SampleGroupProps) {
  return (
    <div className={`border-b border-border last:border-b-0 ${isSelected ? 'bg-primary/5' : ''}`}>
      {/* Group Header */}
      <div className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-primary/5 to-transparent">
        {/* Selection Checkbox */}
        <button
          onClick={(e) => {
            e.stopPropagation();
            onSelectToggle();
          }}
          className="p-1 rounded hover:bg-primary/10 transition-colors"
          title={isSelected ? "Deselect for export" : "Select for export"}
        >
          {isSelected ? (
            <CheckSquare className="h-5 w-5 text-primary" />
          ) : (
            <Square className="h-5 w-5 text-muted-foreground hover:text-primary" />
          )}
        </button>

        {/* Expand/Collapse Button */}
        <button
          onClick={onToggle}
          className="flex-1 flex items-center gap-3 hover:bg-primary/5 rounded px-2 py-1 transition-all duration-200"
        >
          {isExpanded ? (
            <ChevronDown className="h-4 w-4 text-primary shrink-0" />
          ) : (
            <ChevronRight className="h-4 w-4 text-primary shrink-0" />
          )}
          <FolderOpen className="h-4 w-4 text-primary shrink-0" />
          <span className="font-semibold text-foreground">{sampleId}</span>
          <Badge
            variant="outline"
            className={`ml-auto border-primary/30 ${isSelected ? 'bg-primary/10 text-primary' : 'text-primary'}`}
          >
            {items.length} {items.length === 1 ? "image" : "images"}
          </Badge>
        </button>
      </div>

      {/* Group Items */}
      {isExpanded && (
        <div className="divide-y divide-border/50">
          {items.map((item) => (
            <HistoryItemRow
              key={item.id}
              item={item}
              isSelected={item.id === selectedItemId}
              onClick={() => onItemSelected(item)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// Component for each history item row
interface HistoryItemRowProps {
  item: HistoryItem;
  isSelected: boolean;
  onClick: () => void;
}

function HistoryItemRow({ item, isSelected, onClick }: HistoryItemRowProps) {
  const formattedDate = new Date(item.updated_at).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <div
      className={`group flex items-center gap-4 px-6 py-4 pl-14 transition-all duration-200 cursor-pointer ${
        isSelected
          ? "bg-primary/10 border-l-2 border-l-primary"
          : "hover:bg-muted/50"
      }`}
      onClick={onClick}
    >
      <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted shrink-0">
        <FileText className="h-5 w-5 text-muted-foreground" />
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-3">
          <p className="truncate font-medium text-foreground" title={item.filename}>
            {item.filename}
          </p>
          <Badge
            variant="outline"
            className="shrink-0 border-muted-foreground/30 text-muted-foreground text-xs"
          >
            {item.serial_number}
          </Badge>
        </div>
        <div className="mt-1 flex items-center gap-3 text-sm text-muted-foreground">
          <span>{formattedDate}</span>
        </div>
      </div>

      <div className="text-right shrink-0">
        <span className="text-sm font-bold text-foreground">
          Score: {item.score_total?.toFixed(2) || "N/A"}
        </span>
      </div>
    </div>
  );
}
