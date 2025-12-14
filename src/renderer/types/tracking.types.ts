// Tracking-related type definitions
// Extracted from ArtPlaceholder.tsx for shared use across components and hooks

export interface TrackingData {
  frame: number;
  objects: Array<{
    id: number;
    x: number;
    y: number;
    w: number;
    h: number;
    cx: number;
    cy: number;
  }>;
  stats: {
    current_birds: number;
    total_birds: number;
  };
}

export interface VideoMetadata {
  fps: number;
  width: number;
  height: number;
}

export interface TrackingStats {
  current: number;
  total: number;
}
