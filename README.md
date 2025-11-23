# CompVision

A minimalist portfolio desktop application built with Electron and TypeScript, featuring a matte design aesthetic inspired by contemporary visual artist portfolios.

## Features

- **macOS-style title bar** with native traffic light controls
- **Dual tab interface** (Agents/Editor)
- **Matte color scheme** with light gray backgrounds and subtle shadows
- **Portfolio layout** with navigation, hero section, and art showcase
- **Orange gradient placeholder** for generative art displays

## Tech Stack

- **Electron** - Desktop application framework
- **TypeScript** - Type-safe JavaScript
- **React** - UI component library
- **Webpack** - Module bundler
- **CSS** - Custom styling (no framework dependencies)

## Getting Started

### Prerequisites

- Node.js (v16 or higher)
- npm

### Installation

```bash
npm install
```

### Development

Run the app in development mode:

```bash
npm start
```

Or run with hot-reload (requires additional setup):

```bash
npm run dev
```

### Build

Build the production version:

```bash
npm run build
```

### Package

Create distributable packages:

```bash
npm run package
```

## Project Structure

```
CompVision/
├── src/
│   ├── main.ts              # Electron main process
│   ├── preload.ts           # Preload script for IPC
│   └── renderer/
│       ├── index.html       # HTML entry point
│       ├── index.tsx        # React entry point
│       ├── App.tsx          # Main App component
│       ├── components/      # React components
│       │   ├── TitleBar.tsx
│       │   ├── Navigation.tsx
│       │   ├── HeroSection.tsx
│       │   └── ArtPlaceholder.tsx
│       └── styles/
│           └── global.css   # Global styles
├── dist/                    # Build output
├── package.json
├── tsconfig.json
└── webpack.renderer.config.js
```

## Design

The application replicates a minimalist portfolio aesthetic with:

- **Title Bar**: White background (#FFFFFF) with macOS traffic lights
- **Main Content**: Light gray matte background (#E8E8E8)
- **Typography**: System fonts with careful spacing and sizing
- **Orange Gradient**: Warm gradient from #FF8C42 to #FFCC99
- **Subtle Interactions**: Hover states and smooth transitions

## License

MIT
