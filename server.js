const express = require('express');
const multer = require('multer'); // For handling file uploads
const path = require('path');
const { exec } = require('child_process'); // To execute Python scripts
const dotenv = require('dotenv'); // To load .env file

dotenv.config(); // Load environment variables from .env file

const app = express();
const port = process.env.PORT || 3000;

// Configure Multer for file uploads (preserve extension so Python can detect type)
const storage = multer.diskStorage({
    destination: (req, file, cb) => cb(null, path.join(__dirname, 'uploads')),
    filename: (req, file, cb) => {
        const unique = `${Date.now()}-${Math.round(Math.random() * 1e9)}`;
        const ext = path.extname(file.originalname) || '';
        cb(null, `${unique}${ext}`);
    },
});
const upload = multer({ storage });

// Serve static frontend files from 'public' folder
// Make sure you have a 'public' folder in your project root, and 'index.html' inside it.
app.use(express.static(path.join(__dirname, 'public')));

// Create uploads directory if it doesn't exist
const uploadsDir = path.join(__dirname, 'uploads');
if (!require('fs').existsSync(uploadsDir)) {
    require('fs').mkdirSync(uploadsDir);
}

// Set up Python environment path (CRUCIAL for deployment)
// These paths are relative to the project root where server.js runs.
// Using system Python since venv doesn't exist
const PYTHON_EXECUTABLE = process.platform === 'win32' ? 'py' : 'python3';
const PYTHON_WORKER_SCRIPT = path.join(__dirname, 'logic.py'); // Assuming logic.py is your Python worker

// --- API Endpoint 1: Query Pre-built Knowledge Base (handled by Python worker) ---
app.post('/api/process', express.json(), (req, res) => {
    const query = req.body.query;
    if (!query) {
        return res.status(400).json({ error: 'Bad Request: Missing query.' });
    }

    // Execute Python script for pre-built KB
    const command = `${PYTHON_EXECUTABLE} ${PYTHON_WORKER_SCRIPT} --query "${query}" --mode test_prebuilt_kb`; // Mode updated to test_prebuilt_kb
    console.log(`Executing Python: ${command}`);

    // Pass GOOGLE_API_KEY from Node.js env to Python env
    exec(command, { env: { ...process.env, GOOGLE_API_KEY: process.env.GOOGLE_API_KEY } }, (error, stdout, stderr) => {
        if (error) {
            console.error(`Python script execution error: ${error}`);
            console.error(`Python stderr: ${stderr}`);
            return res.status(500).json({ error: 'Internal Server Error during Python execution.', details: stderr });
        }
        try {
            const result = JSON.parse(stdout);
            res.json(result);
        } catch (parseError) {
            console.error(`Error parsing Python stdout: ${parseError}`);
            console.error(`Python stdout: ${stdout}`);
            res.status(500).json({ error: 'Internal Server Error: Could not parse Python response.', details: stdout });
        }
    });
});

// --- API Endpoint 2: File Upload and On-the-Fly Processing (handled by Python worker) ---
app.post('/api/process-upload', upload.single('file'), (req, res) => {
    const query = req.body.query;
    const file = req.file;

    if (!file || !query) {
        return res.status(400).json({ error: 'Bad Request: Missing file or query.' });
    }

    const tempFilePath = file.path; // Multer saves the file to a temp path

    // Execute Python script for on-the-fly processing
    const command = `${PYTHON_EXECUTABLE} ${PYTHON_WORKER_SCRIPT} --query "${query}" --file "${tempFilePath}" --mode test_on_the_fly`; // Mode updated to test_on_the_fly
    console.log(`Executing Python: ${command}`);

    exec(command, { env: { ...process.env, GOOGLE_API_KEY: process.env.GOOGLE_API_KEY } }, (error, stdout, stderr) => {
        // Clean up temporary file created by Multer
        require('fs').unlink(tempFilePath, (unlinkErr) => {
            if (unlinkErr) console.error(`Error deleting temp file: ${unlinkErr}`);
        });

        if (error) {
            console.error(`Python script execution error: ${error}`);
            console.error(`Python stderr: ${stderr}`);
            return res.status(500).json({ error: 'Internal Server Error during Python execution.', details: stderr });
        }
        try {
            const result = JSON.parse(stdout);
            res.json(result);
        } catch (parseError) {
            console.error(`Error parsing Python stdout: ${parseError}`);
            console.error(`Python stdout: ${stdout}`);
            res.status(500).json({ error: 'Internal Server Error: Could not parse Python response.', details: stdout });
        }
    });
});

app.listen(port, () => {
    console.log(`Node.js server listening on port ${port}`);
    console.log(`Frontend served from http://localhost:${port}`);
});