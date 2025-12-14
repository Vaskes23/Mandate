import path from 'path';

export const pathsConfig = {
  scriptsDir: 'scripts',
  venv: {
    unix: 'scripts/venv/bin/python3',
    windows: 'scripts/venv/Scripts/python.exe',
  },
};

export const pythonConfig = {
  scriptName: 'bird_tracker.py',
  ipcFlag: '--ipc',
  shutdownTimeoutMs: 5000,
};

/**
 * Window configuration for Electron BrowserWindow
 */
export const windowConfig = {
  width: 1600,
  height: 900,
  titleBarStyle: 'hiddenInset' as const,
  trafficLightPosition: { x: 10, y: 10 },
  backgroundColor: '#FFFFFF',
  webPreferences: {
    nodeIntegration: false,
    contextIsolation: true,
  },
};

/**
 * IPC channel names (single source of truth)
 */
export const ipcChannels = {
  birdTracking: {
    start: 'bird-tracking:start',
    stop: 'bird-tracking:stop',
    frameData: 'bird-tracking:frame-data',
    completed: 'bird-tracking:completed',
    error: 'bird-tracking:error',
  },
} as const;

/**
 * Application metadata
 */
export const appMetadata = {
  name: 'CompVision Bird Tracker',
  version: '1.0.0',
};

/**
 * Get the platform-specific Python interpreter path
 * @param isDev - Whether running in development mode
 * @returns Absolute path to Python interpreter
 */
export function getPythonPath(isDev: boolean = true): string {
  const isWindows = process.platform === 'win32';
  const venvPath = isWindows ? pathsConfig.venv.windows : pathsConfig.venv.unix;

  if (isDev) {
    // In development, scripts are relative to the project root
    return path.join(__dirname, '..', '..', venvPath);
  } else {
    // In production, scripts are in app.asar or extraResources
    return path.join(process.resourcesPath, venvPath);
  }
}

/**
 * Get the path to the Python script
 * @param isDev - Whether running in development mode
 * @returns Absolute path to bird_tracker.py
 */
export function getScriptPath(isDev: boolean = true): string {
  const scriptPath = path.join(pathsConfig.scriptsDir, pythonConfig.scriptName);

  if (isDev) {
    return path.join(__dirname, '..', '..', scriptPath);
  } else {
    return path.join(process.resourcesPath, scriptPath);
  }
}
