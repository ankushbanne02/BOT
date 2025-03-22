const { app, BrowserWindow, ipcMain } = require("electron");
const { spawn } = require("child_process");

let win;

app.whenReady().then(() => {
    win = new BrowserWindow({
        width: 600,
        height: 400,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false
        }
    });

    win.loadFile("index.html");
});

ipcMain.on("start-listening", (event) => {
    const pythonProcess = spawn("python", ["AWS.py"]);

    let rawData = "";

    pythonProcess.stdout.on("data", (data) => {
        rawData += data.toString().trim();
    });

    pythonProcess.stderr.on("data", (data) => {
        console.error("Python Error:", data.toString());  // Log Python errors
    });

    pythonProcess.on("close", (code) => {
        console.log("Raw Python Output:", rawData);  // Log raw output

        try {
            const result = JSON.parse(rawData);  // Parse JSON safely
            event.reply("speech-result", result.text || result.error);
        } catch (err) {
            console.error("JSON Parse Error:", err, "Raw Output:", rawData);
            event.reply("speech-result", "Invalid response from Python");
        }
    });
});
