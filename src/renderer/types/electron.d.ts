/**
 * TypeScript definitions for Electron IPC exposed via preload.ts
 */

interface BirdTrackingProgress {
  frame: number;
  currentBirds: number;
  totalBirds: number;
}

interface BirdTrackingResults {
  total_frames: number;
  processed_frames: number;
  max_simultaneous_birds: number;
  total_unique_birds: number;
}

interface BirdTrackingAPI {
  start: (inputPath: string, outputPath: string) => Promise<{ success: boolean; error?: string }>;
  stop: () => Promise<{ success: boolean; error?: string }>;
  onProgress: (callback: (data: BirdTrackingProgress) => void) => () => void;
  onCompleted: (callback: (results: BirdTrackingResults) => void) => () => void;
  onError: (callback: (error: string) => void) => () => void;
}

declare global {
  interface Window {
    electron: {
      platform: string;
      birdTracking: BirdTrackingAPI;
    };
  }
}

export {};
