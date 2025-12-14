import { useEffect, useRef } from 'react';
import { TrackingData, VideoMetadata, TrackingStats } from '../types/tracking.types';

// Configuration options for the canvas renderer
interface UseCanvasRendererOptions {
  canvasRef: React.RefObject<HTMLCanvasElement>;
  videoRef: React.RefObject<HTMLVideoElement>;
  videoMetadata: VideoMetadata | null;
  trackingDataMap: Map<number, TrackingData>;
  selectedBirdId: number | null;
  isProcessed: boolean;
  onStatsUpdate?: (stats: TrackingStats) => void;
}

/**
 * Custom hook for rendering tracking overlays on a canvas
 * Handles animation loop, bounding box rendering, and frame synchronization
 */
export function useCanvasRenderer(options: UseCanvasRendererOptions): void {
  const {
    canvasRef,
    videoRef,
    videoMetadata,
    trackingDataMap,
    selectedBirdId,
    isProcessed,
    onStatsUpdate
  } = options;

  // Reference for animation frame ID (for cleanup)
  const animationFrameRef = useRef<number>();

  useEffect(() => {
    // Guard clause - don't render if not ready
    if (!isProcessed || !videoRef.current || !canvasRef.current || !videoMetadata) {
      return;
    }

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');

    if (!ctx) return;

    // Main render function called on each animation frame
    const renderFrame = () => {
      if (!video.paused && !video.ended) {
        // Calculate current frame number from video time
        const currentFrame = Math.floor(video.currentTime * videoMetadata.fps);

        // Get tracking data for this frame
        const trackingData = trackingDataMap.get(currentFrame);

        // Clear canvas for new frame
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        if (trackingData) {
          // Update stats via callback
          if (onStatsUpdate) {
            onStatsUpdate({
              current: trackingData.stats.current_birds,
              total: trackingData.stats.total_birds
            });
          }

          // Draw bounding boxes and IDs for each detected bird
          trackingData.objects.forEach(bird => {
            // Determine color based on selection (purple for selected, green for others)
            const isSelected = bird.id === selectedBirdId;
            const color = isSelected ? '#9F00FF' : '#00FF00';

            // Draw bounding box
            ctx.strokeStyle = color;
            ctx.lineWidth = isSelected ? 3 : 2;
            ctx.strokeRect(bird.x, bird.y, bird.w, bird.h);

            // Draw ID label with background
            const text = `ID: ${bird.id}`;
            ctx.font = '14px Arial';
            const textMetrics = ctx.measureText(text);
            const textHeight = 16;

            // Background rectangle for label
            ctx.fillStyle = color;
            ctx.fillRect(bird.x, bird.y - textHeight - 4, textMetrics.width + 8, textHeight + 4);

            // Label text
            ctx.fillStyle = '#FFFFFF';
            ctx.fillText(text, bird.x + 4, bird.y - 6);

            // Draw centroid marker (red dot at center of bird)
            ctx.fillStyle = '#FF0000';
            ctx.beginPath();
            ctx.arc(bird.cx, bird.cy, 4, 0, 2 * Math.PI);
            ctx.fill();
          });
        }
      }

      // Continue animation loop
      animationFrameRef.current = requestAnimationFrame(renderFrame);
    };

    // Start the animation loop
    renderFrame();

    // Cleanup function to cancel animation frame on unmount or dependency change
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [canvasRef, videoRef, isProcessed, trackingDataMap, videoMetadata, selectedBirdId, onStatsUpdate]);
}
