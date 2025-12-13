import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('electron', {
  platform: process.platform,

  // Bird tracking IPC methods
  birdTracking: {
    start: (inputPath: string) =>
      ipcRenderer.invoke('bird-tracking:start', inputPath),

    stop: () =>
      ipcRenderer.invoke('bird-tracking:stop'),

    onFrameData: (callback: (data: any) => void) => {
      ipcRenderer.on('bird-tracking:frame-data', (_event, data) => callback(data));
      return () => ipcRenderer.removeAllListeners('bird-tracking:frame-data');
    },

    onCompleted: (callback: (results: any) => void) => {
      ipcRenderer.on('bird-tracking:completed', (_event, results) => callback(results));
      return () => ipcRenderer.removeAllListeners('bird-tracking:completed');
    },

    onError: (callback: (error: string) => void) => {
      ipcRenderer.on('bird-tracking:error', (_event, error) => callback(error));
      return () => ipcRenderer.removeAllListeners('bird-tracking:error');
    }
  }
});
