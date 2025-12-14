import React, { useState } from 'react';
import { TitleBar } from './components/TitleBar';
import { Navigation } from './components/Navigation';
import { ArtPlaceholder } from './components/ArtPlaceholder';
import './styles/global.css';

export const App: React.FC = () => {
  const [videoName, setVideoName] = useState<string>('CompVision Bird Tracker');

  return (
    <div className="app">
      <TitleBar videoName={videoName} />
      <div className="main-content">
        <Navigation />
        <ArtPlaceholder onVideoNameChange={setVideoName} />
      </div>
    </div>
  );
};
