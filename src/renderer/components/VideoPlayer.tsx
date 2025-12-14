import React, { forwardRef } from 'react';

interface VideoPlayerProps {
  videoSrc: string;
  isProcessing: boolean;
  isProcessed: boolean;
  onStartTracking: () => Promise<void>;
  onMetadataLoaded: (video: HTMLVideoElement) => void;
}

/**
 * Video player component for displaying and controlling video playback
 * Uses forwardRef to expose video element to parent for canvas synchronization
 */
export const VideoPlayer = forwardRef<HTMLVideoElement, VideoPlayerProps>(
  ({ videoSrc, isProcessing, isProcessed, onStartTracking, onMetadataLoaded }, ref) => {
    // Get the actual DOM element from the ref for internal operations
    const getVideoElement = (): HTMLVideoElement | null => {
      if (ref && 'current' in ref) {
        return ref.current;
      }
      return null;
    };

    // Handle video click - play/pause or start tracking
    const handleVideoClick = async () => {
      const video = getVideoElement();
      if (!video) return;

      // If already processed, just toggle play/pause
      if (isProcessed) {
        if (video.paused) {
          video.play();
        } else {
          video.pause();
        }
        return;
      }

      // If currently processing, toggle play/pause but don't restart tracking
      if (isProcessing) {
        if (video.paused) {
          video.play();
        } else {
          video.pause();
        }
        return;
      }

      // First click: start tracking and play video
      video.play();
      await onStartTracking();
    };

    // Handle video metadata loaded - notify parent for canvas sizing
    const handleLoadedMetadata = () => {
      const video = getVideoElement();
      if (video) {
        onMetadataLoaded(video);
      }
    };

    return (
      <video
        ref={ref}
        className="art-video"
        loop
        muted
        playsInline
        onClick={handleVideoClick}
        onLoadedMetadata={handleLoadedMetadata}
      >
        <source src={videoSrc} type="video/mp4" />
      </video>
    );
  }
);

VideoPlayer.displayName = 'VideoPlayer';
