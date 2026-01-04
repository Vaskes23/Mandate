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
  isProcessing: boolean;
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
    isProcessing,
    onStatsUpdate
  } = options;

  // Reference for animation frame ID (for cleanup)
  const animationFrameRef = useRef<number>();

  useEffect(() => {
    // Guard clause - render when we have canvas, video, and either processing or processed
    // This allows rendering to start as soon as we have tracking data
    const hasTrackingData = trackingDataMap.size > 0;
    if (!videoRef.current || !canvasRef.current || (!isProcessing && !isProcessed)) {
      return;
    }

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');

    if (!ctx) return;

    // Get FPS - use metadata if available, otherwise estimate from video or default to 60
    const fps = videoMetadata?.fps || 60;

    // Calculate scale factors for coordinate transformation
    // Canvas internal dimensions may differ from CSS display size
    const getScaleFactors = () => {
      const displayWidth = canvas.clientWidth || canvas.width;
      const displayHeight = canvas.clientHeight || canvas.height;
      // If canvas size matches video, scale is 1:1
      // Otherwise we need to scale coordinates
      return {
        scaleX: canvas.width / (video.videoWidth || canvas.width),
        scaleY: canvas.height / (video.videoHeight || canvas.height)
      };
    };

    // Main render function called on each animation frame
    const renderFrame = () => {
      // Always continue the loop, but only draw when video is playing
      if (!video.paused && !video.ended) {
        // Calculate current frame number from video time
        const currentFrame = Math.floor(video.currentTime * fps);

        // Get tracking data for this frame (or try nearby frames)
        let trackingData = trackingDataMap.get(currentFrame);

        // If no exact match, try nearby frames (handles timing drift)
        if (!trackingData && hasTrackingData) {
          for (let offset = 1; offset <= 2; offset++) {
            trackingData = trackingDataMap.get(currentFrame - offset) ||
                          trackingDataMap.get(currentFrame + offset);
            if (trackingData) break;
          }
        }

        // Clear canvas for new frame
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Get scale factors
        const { scaleX, scaleY } = getScaleFactors();

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
            const colorStatus = (bird as any).color_status || 'pending';

            // Skip birds that passed color analysis (they're false positives)
            if (colorStatus === 'passed') {
              return;
            }

            // Apply scale factors to coordinates
            const x = bird.x * scaleX;
            const y = bird.y * scaleY;
            const w = bird.w * scaleX;
            const h = bird.h * scaleY;
            const cx = bird.cx * scaleX;
            const cy = bird.cy * scaleY;

            // Determine color: purple for selected, green for suspicious (real birds)
            const isSelected = bird.id === selectedBirdId;
            let color = '#00FF00'; // Green for suspicious/pending (real birds)
            if (isSelected) {
              color = '#9F00FF'; // Purple for selected
            }

            // Draw bounding box
            ctx.strokeStyle = color;
            ctx.lineWidth = isSelected ? 3 : 2;
            ctx.strokeRect(x, y, w, h);

            // Draw ID label with background
            const text = `ID: ${bird.id}`;
            ctx.font = '12px Arial';
            const textMetrics = ctx.measureText(text);
            const textHeight = 14;

            // Background rectangle for label
            ctx.fillStyle = color;
            ctx.fillRect(x, y - textHeight - 2, textMetrics.width + 6, textHeight + 2);

            // Label text
            ctx.fillStyle = '#FFFFFF';
            ctx.fillText(text, x + 3, y - 4);

            // Draw centroid marker (red dot at center of bird)
            ctx.fillStyle = '#FF0000';
            ctx.beginPath();
            ctx.arc(cx, cy, 3, 0, 2 * Math.PI);
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
  }, [canvasRef, videoRef, isProcessed, isProcessing, trackingDataMap, videoMetadata, selectedBirdId, onStatsUpdate]);
}
