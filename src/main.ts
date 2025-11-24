import { app, BrowserWindow, ipcMain } from 'electron';
import * as path from 'path';
import { spawn, ChildProcess } from 'child_process';

let mainWindow: BrowserWindow | null = null;
let pythonProcess: ChildProcess | null = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1600,
    height: 900,
    titleBarStyle: 'hiddenInset',
    trafficLightPosition: { x: 10, y: 10 },
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true
    },
    backgroundColor: '#FFFFFF',
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
  ipcMain.handle('bird-tracking:start', async (_event, inputPath: string) => {
    try {
      // Stop any existing process
      if (pythonProcess) {
        pythonProcess.kill();
        pythonProcess = null;
      }

      // Get Python script path and venv python
      const scriptPath = path.join(__dirname, '..', 'scripts', 'bird_tracker.py');
      const venvPython = path.join(__dirname, '..', 'scripts', 'venv', 'bin', 'python3');

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
              mainWindow?.webContents.send('bird-tracking:frame-data', message.data);
            } else if (message.type === 'completed') {
              mainWindow?.webContents.send('bird-tracking:completed', message.results);
            } else if (message.type === 'error') {
              mainWindow?.webContents.send('bird-tracking:error', message.message);
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
        mainWindow?.webContents.send('bird-tracking:error', error);
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
  ipcMain.handle('bird-tracking:stop', async () => {
    try {
      if (pythonProcess) {
        // Send stop command
        const stopCommand = JSON.stringify({ action: 'stop' }) + '\n';
        pythonProcess.stdin?.write(stopCommand);

        // Give it time to gracefully exit
        setTimeout(() => {
          if (pythonProcess) {
            pythonProcess.kill();
            pythonProcess = null;
          }
        }, 1000);
      }

      return { success: true };
    } catch (error) {
      console.error('Failed to stop bird tracking:', error);
      return { success: false, error: String(error) };
    }
  });

  // Set selected bird for tracking output
  ipcMain.handle('bird-tracking:set-selected-bird', async (_event, birdId: number | null) => {
    try {
      if (pythonProcess && pythonProcess.stdin) {
        const command = JSON.stringify({
          action: 'set_selected_bird',
          bird_id: birdId
        }) + '\n';
        pythonProcess.stdin.write(command);
      }
      return { success: true };
    } catch (error) {
      console.error('Failed to set selected bird:', error);
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
