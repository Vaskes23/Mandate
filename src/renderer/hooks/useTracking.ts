import { useState, useEffect } from 'react';
import { TrackingData, VideoMetadata } from '../types/tracking.types';

// Return type for the useTracking hook
interface UseTrackingReturn {
  trackingDataMap: Map<number, TrackingData>;
  videoMetadata: VideoMetadata | null;
  isProcessing: boolean;
  isProcessed: boolean;
  startTracking: (filename: string) => Promise<void>;
  error: string | null;
}

/**
 * Custom hook for managing bird tracking IPC communication
 * Handles all communication with the Electron main process for tracking operations
 */
export function useTracking(): UseTrackingReturn {
  // Tracking data state - maps frame numbers to tracking data
  const [trackingDataMap, setTrackingDataMap] = useState<Map<number, TrackingData>>(new Map());
  // Video metadata received on completion
  const [videoMetadata, setVideoMetadata] = useState<VideoMetadata | null>(null);
  // Processing state flags
  const [isProcessing, setIsProcessing] = useState(false);
  const [isProcessed, setIsProcessed] = useState(false);
  // Error state
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Setup tracking frame data listener
    const removeFrameDataListener = (window as any).electron?.birdTracking?.onFrameData(
      (data: TrackingData) => {
        setTrackingDataMap(prev => {
          const newMap = new Map(prev);
          newMap.set(data.frame, data);
          return newMap;
        });
      }
    );

    // Setup completion listener
    const removeCompletedListener = (window as any).electron?.birdTracking?.onCompleted(
      (results: any) => {
        setIsProcessing(false);
        setIsProcessed(true);
        setVideoMetadata({
          fps: results.fps,
          width: results.width,
          height: results.height
        });
      }
    );

    // Setup error listener
    const removeErrorListener = (window as any).electron?.birdTracking?.onError(
      (errorMsg: string) => {
        console.error('Tracking error:', errorMsg);
        setError(errorMsg);
        setIsProcessing(false);
      }
    );

    // Cleanup on unmount
    return () => {
      if (removeFrameDataListener) removeFrameDataListener();
      if (removeCompletedListener) removeCompletedListener();
      if (removeErrorListener) removeErrorListener();
    };
  }, []);

  // Start tracking function
  const startTracking = async (filename: string): Promise<void> => {
    setIsProcessing(true);
    setError(null);

    try {
      await (window as any).electron.birdTracking.start(filename);
    } catch (err) {
      console.error('Failed to start tracking:', err);
      setError(String(err));
      setIsProcessing(false);
    }
  };

  return {
    trackingDataMap,
    videoMetadata,
    isProcessing,
    isProcessed,
    startTracking,
    error
  };
}
