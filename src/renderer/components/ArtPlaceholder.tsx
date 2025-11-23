import React, { useRef } from 'react';

export const ArtPlaceholder: React.FC = () => {
  const videoRef = useRef<HTMLVideoElement>(null);

  const handleVideoClick = () => {
    if (videoRef.current) {
      if (videoRef.current.paused) {
        videoRef.current.play();
      } else {
        videoRef.current.pause();
      }
    }
  };

  return (
    <div className="art-container">
      <div className="art-metadata-row">
        <div className="art-metadata-left">
          <span className="art-number">(001)</span>
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
        >
          <source src="../../birdsExample.mp4" type="video/mp4" />
        </video>
      </div>
    </div>
  );
};
