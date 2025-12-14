import React from 'react';

interface ProcessingIndicatorProps {
  isProcessing: boolean;
  isProcessed: boolean;
}

/**
 * Component for displaying processing status overlay
 * Shows "Processing..." message while tracking is in progress
 */
export const ProcessingIndicator: React.FC<ProcessingIndicatorProps> = ({
  isProcessing,
  isProcessed
}) => {
  // Only show when processing but not yet completed
  if (!isProcessing || isProcessed) {
    return null;
  }

  return (
    <div className="processing-overlay">
      Processing...
    </div>
  );
};
