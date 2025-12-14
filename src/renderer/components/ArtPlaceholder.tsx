import React, { useRef, useState, useEffect } from 'react';
import { useTracking } from '../hooks/useTracking';
import { useCanvasRenderer } from '../hooks/useCanvasRenderer';
import { VideoPlayer } from './VideoPlayer';
import { TrackingOverlay } from './TrackingOverlay';
import { TrackingStats } from './TrackingStats';
import { ProcessingIndicator } from './ProcessingIndicator';
import { TrackingStats as TrackingStatsType } from '../types/tracking.types';

interface ArtPlaceholderProps {
  onVideoNameChange?: (filename: string) => void;
}

/**
 * Main container component for bird tracking visualization
 * Orchestrates video playback, tracking, and overlay rendering
 */
export const ArtPlaceholder: React.FC<ArtPlaceholderProps> = ({ onVideoNameChange }) => {
  // Refs for video and canvas elements (shared with hooks)
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Local UI state
  const [currentStats, setCurrentStats] = useState<TrackingStatsType>({ current: 0, total: 0 });
  const [selectedBirdId, setSelectedBirdId] = useState<number | null>(null);
  const videoFileName = 'birdsExample.mp4';

  // Use tracking hook for IPC management
  const {
    trackingDataMap,
    videoMetadata,
    isProcessing,
    isProcessed,
    startTracking,
    error
  } = useTracking();

  // Use canvas renderer hook for animation loop
  useCanvasRenderer({
    canvasRef,
    videoRef,
    videoMetadata,
    trackingDataMap,
    selectedBirdId,
    isProcessed,
    onStatsUpdate: setCurrentStats
  });

  // Notify parent of video filename
  useEffect(() => {
    if (onVideoNameChange) {
      onVideoNameChange(videoFileName);
    }
  }, [videoFileName, onVideoNameChange]);

  // Handle video metadata loaded (sync canvas size)
  const handleMetadataLoaded = (video: HTMLVideoElement) => {
    if (canvasRef.current) {
      canvasRef.current.width = video.videoWidth;
      canvasRef.current.height = video.videoHeight;
    }
  };

  // Handle start tracking
  const handleStartTracking = async () => {
    await startTracking(videoFileName);
  };

  return (
    <div className="art-container">
      <div className="art-metadata-row">
        <TrackingStats
          stats={currentStats}
          selectedBirdId={selectedBirdId}
          onSelectBird={setSelectedBirdId}
        />
        <div className="art-metadata-center">
          <h2 className="art-title">Berlin Karl-Marx-Allee</h2>
        </div>
        <div className="art-metadata-right">
          <span className="art-category">Autumn</span>
        </div>
      </div>

      <div className="art-placeholder">
        <VideoPlayer
          ref={videoRef}
          videoSrc="../../birdsExample.mp4"
          isProcessing={isProcessing}
          isProcessed={isProcessed}
          onStartTracking={handleStartTracking}
          onMetadataLoaded={handleMetadataLoaded}
        />

        <TrackingOverlay ref={canvasRef} />

        <ProcessingIndicator
          isProcessing={isProcessing}
          isProcessed={isProcessed}
        />

        {isProcessed && (
          <div className="stats-overlay">
            Current Birds: {currentStats.current} | Total: {currentStats.total} |
          </div>
        )}

        {error && (
          <div className="error-overlay">
            Error: {error}
          </div>
        )}
      </div>
    </div>
  );
};
