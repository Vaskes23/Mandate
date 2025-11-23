import React from 'react';

interface TitleBarProps {
  className?: string;
}

export const TitleBar: React.FC<TitleBarProps> = ({ className = '' }) => {
  return (
    <div className={`title-bar ${className}`}>
      <div className="title-bar-drag-region"></div>

      <div className="site-title">birdsExample.mp4</div>

    </div>
  );
};
