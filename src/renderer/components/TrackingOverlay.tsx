import React, { forwardRef } from 'react';

/**
 * Canvas overlay component for rendering tracking visualizations
 * Uses forwardRef to expose canvas element to parent for rendering operations
 */
export const TrackingOverlay = forwardRef<HTMLCanvasElement>(
  (_props, ref) => {
    return (
      <canvas
        ref={ref}
        className="tracking-canvas"
      />
    );
  }
);

TrackingOverlay.displayName = 'TrackingOverlay';
