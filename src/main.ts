import { app, BrowserWindow, ipcMain } from 'electron';
import * as path from 'path';
import { spawn, ChildProcess } from 'child_process';
import { getPythonPath, getScriptPath, ipcChannels, windowConfig, pythonConfig } from './config/app.config';

let mainWindow: BrowserWindow | null = null;
let pythonProcess: ChildProcess | null = null;

// Determine if running in development or production
const isDevelopment = !app.isPackaged;

// Enable hot reload for development (auto-restart when main process files change)
if (isDevelopment && process.env.ELECTRON_DEV) {
  try {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    require('electron-reload')(__dirname, {
      electron: path.join(__dirname, '..', 'node_modules', '.bin', 'electron'),
      hardResetMethod: 'exit',
      forceHardReset: true
    });
  } catch (e) {
    console.log('electron-reload not available:', e);
  }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: windowConfig.width,
    height: windowConfig.height,
    titleBarStyle: windowConfig.titleBarStyle,
    trafficLightPosition: windowConfig.trafficLightPosition,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: windowConfig.webPreferences.nodeIntegration,
      contextIsolation: windowConfig.webPreferences.contextIsolation
    },
    backgroundColor: windowConfig.backgroundColor,
    show: false
  });

  mainWindow.loadFile(path.join(__dirname, 'renderer', 'index.html'));

  mainWindow.once('ready-to-show', () => {
    mainWindow?.show();
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// Bird tracking IPC handlers
function setupBirdTrackingHandlers() {
  // Start bird tracking
  ipcMain.handle(ipcChannels.birdTracking.start, async (_event, inputPath: string) => {
    try {
      // Stop any existing process
      if (pythonProcess) {
        pythonProcess.kill();
        pythonProcess = null;
      }

      // Get Python script path and venv python (platform-specific)
      const scriptPath = getScriptPath(isDevelopment);
      const venvPython = getPythonPath(isDevelopment);

      // Spawn Python process in IPC mode using venv
      pythonProcess = spawn(venvPython, [scriptPath, '--ipc'], {
        cwd: path.join(__dirname, '..', 'scripts')
      });

      // Send start command to Python process with absolute path
      const projectRoot = path.join(__dirname, '..');
      const absoluteInputPath = path.join(projectRoot, inputPath);

      const startCommand = JSON.stringify({
        action: 'start',
        input: absoluteInputPath
      }) + '\n';

      pythonProcess.stdin?.write(startCommand);

      // Handle stdout (JSON messages from Python)
      pythonProcess.stdout?.on('data', (data) => {
        const lines = data.toString().split('\n').filter((line: string) => line.trim());

        lines.forEach((line: string) => {
          try {
            const message = JSON.parse(line);

            if (message.type === 'frame_data') {
              mainWindow?.webContents.send(ipcChannels.birdTracking.frameData, message.data);
            } else if (message.type === 'completed') {
              mainWindow?.webContents.send(ipcChannels.birdTracking.completed, message.results);
            } else if (message.type === 'error') {
              mainWindow?.webContents.send(ipcChannels.birdTracking.error, message.message);
            }
          } catch (e) {
            console.error('Failed to parse Python output:', line, e);
          }
        });
      });

      // Handle stderr (errors)
      pythonProcess.stderr?.on('data', (data) => {
        const error = data.toString();
        console.error('Python error:', error);
        mainWindow?.webContents.send(ipcChannels.birdTracking.error, error);
      });

      // Handle process exit
      pythonProcess.on('close', (code) => {
        console.log(`Python process exited with code ${code}`);
        pythonProcess = null;
      });

      return { success: true };
    } catch (error) {
      console.error('Failed to start bird tracking:', error);
      return { success: false, error: String(error) };
    }
  });

  // Stop bird tracking
  ipcMain.handle(ipcChannels.birdTracking.stop, async () => {
    try {
      if (pythonProcess) {
        // Send stop command via stdin first
        const stopCommand = JSON.stringify({ action: 'stop' }) + '\n';
        pythonProcess.stdin?.write(stopCommand);

        // Wait for graceful shutdown with escalation
        await new Promise<void>((resolve) => {
          const timeout = setTimeout(() => {
            if (pythonProcess && !pythonProcess.killed) {
              console.warn('Python process did not exit gracefully, forcing kill');
              pythonProcess.kill('SIGKILL');
            }
            resolve();
          }, pythonConfig.shutdownTimeoutMs);

          pythonProcess!.once('exit', () => {
            clearTimeout(timeout);
            pythonProcess = null;
            resolve();
          });

          // Try SIGTERM first
          pythonProcess!.kill('SIGTERM');
        });
      }

      return { success: true };
    } catch (error) {
      console.error('Failed to stop bird tracking:', error);
      return { success: false, error: String(error) };
    }
  });
}

app.whenReady().then(() => {
  createWindow();
  setupBirdTrackingHandlers();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  // Cleanup Python process
  if (pythonProcess) {
    pythonProcess.kill();
    pythonProcess = null;
  }

  if (process.platform !== 'darwin') {
    app.quit();
  }
});
