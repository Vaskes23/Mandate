import React from 'react';

interface TitleBarProps {
  className?: string;
  videoName?: string;
}

export const TitleBar: React.FC<TitleBarProps> = ({ className = '', videoName = 'CompVision Bird Tracker' }) => {
  return (
    <div className={`title-bar ${className}`}>
      <div className="title-bar-drag-region"></div>

      <div className="site-title">{videoName}</div>

    </div>
  );
};
