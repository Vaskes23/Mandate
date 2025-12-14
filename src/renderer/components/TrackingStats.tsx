import React from 'react';
import { TrackingStats as TrackingStatsType } from '../types/tracking.types';

interface TrackingStatsProps {
  stats: TrackingStatsType;
  selectedBirdId: number | null;
  onSelectBird: (id: number | null) => void;
}

/**
 * Component for displaying tracking statistics and bird ID selection
 * Shows current/total bird counts and provides ID input for highlighting specific birds
 */
export const TrackingStats: React.FC<TrackingStatsProps> = ({
  stats,
  selectedBirdId,
  onSelectBird
}) => {
  return (
    <div className="art-metadata-left">
      Select ID:
      <input
        type="number"
        value={selectedBirdId ?? ''}
        onChange={(e) => onSelectBird(e.target.value ? Number(e.target.value) : null)}
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
  );
};
