import React, { useRef, useState, useEffect } from 'react';

interface TrackingData {
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

interface VideoMetadata {
  fps: number;
  width: number;
  height: number;
}

export const ArtPlaceholder: React.FC = () => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isProcessed, setIsProcessed] = useState(false);
  const [trackingDataMap, setTrackingDataMap] = useState<Map<number, TrackingData>>(new Map());
  const [videoMetadata, setVideoMetadata] = useState<VideoMetadata | null>(null);
  const [currentStats, setCurrentStats] = useState({ current: 0, total: 0 });
  const [selectedBirdId, setSelectedBirdId] = useState<number | null>(null);

  // Notify backend when selected bird changes
  useEffect(() => {
    if (isProcessing || isProcessed) {
      (window as any).electron?.birdTracking?.setSelectedBird?.(selectedBirdId);
    }
  }, [selectedBirdId, isProcessing, isProcessed]);
  const animationFrameRef = useRef<number>();

  useEffect(() => {
    // Setup tracking frame data listener
    const removeFrameDataListener = (window as any).electron?.birdTracking?.onFrameData((data: TrackingData) => {
      setTrackingDataMap(prev => {
        const newMap = new Map(prev);
        newMap.set(data.frame, data);
        return newMap;
      });
    });

    // Setup completion listener
    const removeCompletedListener = (window as any).electron?.birdTracking?.onCompleted((results: any) => {
      setIsProcessing(false);
      setIsProcessed(true);
      setVideoMetadata({
        fps: results.fps,
        width: results.width,
        height: results.height
      });
    });

    // Setup error listener
    const removeErrorListener = (window as any).electron?.birdTracking?.onError((error: string) => {
      console.error('Tracking error:', error);
      setIsProcessing(false);
    });

    return () => {
      if (removeFrameDataListener) removeFrameDataListener();
      if (removeCompletedListener) removeCompletedListener();
      if (removeErrorListener) removeErrorListener();
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, []);

  // Canvas rendering loop
  useEffect(() => {
    if (!isProcessed || !videoRef.current || !canvasRef.current || !videoMetadata) {
      return;
    }

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');

    if (!ctx) return;

    const renderFrame = () => {
      if (!video.paused && !video.ended) {
        // Calculate current frame number
        const currentFrame = Math.floor(video.currentTime * videoMetadata.fps);

        // Get tracking data for this frame
        const trackingData = trackingDataMap.get(currentFrame);

        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        if (trackingData) {
          // Update stats
          setCurrentStats({
            current: trackingData.stats.current_birds,
            total: trackingData.stats.total_birds
          });

          // Draw bounding boxes and IDs
          trackingData.objects.forEach(bird => {
            // Determine color based on selection
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

            // Background rectangle
            ctx.fillStyle = color;
            ctx.fillRect(bird.x, bird.y - textHeight - 4, textMetrics.width + 8, textHeight + 4);

            // Text
            ctx.fillStyle = '#FFFFFF';
            ctx.fillText(text, bird.x + 4, bird.y - 6);

            // Draw centroid
            ctx.fillStyle = '#FF0000';
            ctx.beginPath();
            ctx.arc(bird.cx, bird.cy, 4, 0, 2 * Math.PI);
            ctx.fill();
          });
        }
      }

      animationFrameRef.current = requestAnimationFrame(renderFrame);
    };

    renderFrame();

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [isProcessed, trackingDataMap, videoMetadata, selectedBirdId]);

  const handleVideoClick = async () => {
    if (videoRef.current) {
      // If already processed, just play/pause
      if (isProcessed) {
        if (videoRef.current.paused) {
          videoRef.current.play();
        } else {
          videoRef.current.pause();
        }
        return;
      }

      // If currently processing, toggle play/pause but don't restart
      if (isProcessing) {
        if (videoRef.current.paused) {
          videoRef.current.play();
        } else {
          videoRef.current.pause();
        }
        return;
      }

      // First click: start tracking
      setIsProcessing(true);
      videoRef.current.play();

      try {
        await (window as any).electron.birdTracking.start('birdsExample.mp4');
      } catch (error) {
        console.error('Failed to start tracking:', error);
        setIsProcessing(false);
      }
    }
  };

  const handleLoadedMetadata = () => {
    // Set canvas dimensions to match video
    if (videoRef.current && canvasRef.current) {
      canvasRef.current.width = videoRef.current.videoWidth;
      canvasRef.current.height = videoRef.current.videoHeight;
    }
  };

  return (
    <div className="art-container">
      <div className="art-metadata-row">
        <div className="art-metadata-left">
        Select ID: <input
              type="number"
              value={selectedBirdId ?? ''}
              onChange={(e) => setSelectedBirdId(e.target.value ? Number(e.target.value) : null)}
              placeholder="ID"
              style={{
                width: '60px',
                marginLeft: '8px',
                padding: '4px 8px',
                fontSize: '14px',
                borderRadius: '4px',
                border: '1px solid rgba(255, 255, 255, 0.3)',
                backgroundColor: 'rgba(0, 0, 0, 0.3)',
                color: '#ffffff',
                outline: 'none'
              }}
            />
        </div>
        <div className="art-metadata-center">
          <h2 className="art-title">Berlin Karl-Marx-Allee</h2>
        </div>
        <div className="art-metadata-right">
          <span className="art-category">Autumn</span>
        </div>
      </div>

      <div className="art-placeholder">
        <video
          ref={videoRef}
          className="art-video"
          loop
          muted
          playsInline
          onClick={handleVideoClick}
          onLoadedMetadata={handleLoadedMetadata}
        >
          <source src="../../birdsExample.mp4" type="video/mp4" />
        </video>

        <canvas
          ref={canvasRef}
          className="tracking-canvas"
        />

        {isProcessing && !isProcessed && (
          <div className="processing-overlay">
            Processing...
          </div>
        )}

        {isProcessed && (
          <div className="stats-overlay">
            Current Birds: {currentStats.current} | Total: {currentStats.total} |
          </div>
        )}
      </div>
    </div>
  );
};
