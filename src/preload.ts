import { contextBridge, ipcRenderer } from 'electron';

// IPC channel constants - DO NOT import from config due to Electron preload sandboxing
// These values must match those in src/config/app.config.ts
const BIRD_TRACKING_CHANNELS = {
  START: 'bird-tracking:start',
  STOP: 'bird-tracking:stop',
  FRAME_DATA: 'bird-tracking:frame-data',
  COMPLETED: 'bird-tracking:completed',
  ERROR: 'bird-tracking:error',
} as const;

contextBridge.exposeInMainWorld('electron', {
  platform: process.platform,

  // Bird tracking IPC methods
  birdTracking: {
    start: (inputPath: string) =>
      ipcRenderer.invoke(BIRD_TRACKING_CHANNELS.START, inputPath),

    stop: () =>
      ipcRenderer.invoke(BIRD_TRACKING_CHANNELS.STOP),

    onFrameData: (callback: (data: any) => void) => {
      ipcRenderer.on(BIRD_TRACKING_CHANNELS.FRAME_DATA, (_event, data) => callback(data));
      return () => ipcRenderer.removeAllListeners(BIRD_TRACKING_CHANNELS.FRAME_DATA);
    },

    onCompleted: (callback: (results: any) => void) => {
      ipcRenderer.on(BIRD_TRACKING_CHANNELS.COMPLETED, (_event, results) => callback(results));
      return () => ipcRenderer.removeAllListeners(BIRD_TRACKING_CHANNELS.COMPLETED);
    },

    onError: (callback: (error: string) => void) => {
      ipcRenderer.on(BIRD_TRACKING_CHANNELS.ERROR, (_event, error) => callback(error));
      return () => ipcRenderer.removeAllListeners(BIRD_TRACKING_CHANNELS.ERROR);
    }
  }
});
