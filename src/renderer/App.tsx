import React from 'react';
import { TitleBar } from './components/TitleBar';
import { Navigation } from './components/Navigation';
import { HeroSection } from './components/HeroSection';
import { ArtPlaceholder } from './components/ArtPlaceholder';
import './styles/global.css';

export const App: React.FC = () => {
  return (
    <div className="app">
      <TitleBar />
      <div className="main-content">
        <Navigation />
        <HeroSection />
        <ArtPlaceholder />
      </div>
    </div>
  );
};
