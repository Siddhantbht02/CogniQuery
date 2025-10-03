# CogniQuery: Intelligent Query Processing Platform

## 💡 Project Overview

CogniQuery is a sophisticated, full-stack platform engineered to deliver highly accurate and contextually relevant answers to user queries using advanced Large Language Models (LLMs). The project is built with a clear separation of concerns, utilizing a decoupled architecture to ensure scalability, performance, and maintainability.

The system is designed to transform simple search interactions into a cognitive process, allowing users to interact with a knowledge source (or the web) in a deeply conversational and insightful manner.

## 🏗️ Core Architecture

- **Frontend (Client)**: Built with pure JavaScript, HTML, and CSS for a lightweight, fast, and responsive user interface. Handles user input, displays results, and manages API communication.
- **Backend (API Server)**: Built with Python (utilizing a framework like Flask or FastAPI) to manage environment variables, handle heavy processing, route requests, and interface directly with the LLM APIs (e.g., Gemini, OpenAI).

## ✨ Features

### AI & Functionality
- **Intelligent Q&A**: Processes natural language questions and generates comprehensive, coherent responses.
- **Streaming Capability** (Planned): Designed to support response streaming from the backend to the frontend for a fast, modern user experience.
- **Contextual Memory**: Can be extended to maintain conversational context across multiple turns for enhanced interaction.

### System & Development
- **RESTful API**: Cleanly defined endpoints in the Python backend for predictable data exchange.
- **Cross-Origin Resource Sharing (CORS)**: Properly configured to allow seamless communication between the frontend (running on one port) and the backend (running on another).
- **Easy Deployment**: Structure is optimized for deployment on services like Vercel (frontend) and a dedicated server or container service (backend).

## 🛠️ Technology Stack & Dependencies

### Backend (`/backend`)

| Component | Assumption/Framework | Role |
|-----------|---------------------|------|
| Language | Python (3.10+) | Core business logic and LLM interaction |
| Web Framework | Flask / FastAPI | Serving the RESTful API endpoints |
| LLM Integration | google-genai / openai / requests | Communicating with the LLM service |
| Environment | python-dotenv | Securely loading API keys and configurations |

### Frontend (`/frontend`)

| Component | Details | Role |
|-----------|---------|------|
| Language | JavaScript | Handling DOM manipulation and API calls (fetch) |
| Styling | HTML5 / CSS3 | Presentation and responsiveness |
| Package Manager | npm / yarn | Managing minor client-side dependencies (if any) |

## 🚀 Getting Started

Follow these steps to get a local copy of the project up and running.

### Prerequisites

Ensure you have the following installed:
- Python (3.10 or higher)
- Node.js (which includes npm)
- An API Key for your preferred Large Language Model (e.g., Gemini API Key)

### 1. Clone the Repository

```bash
git clone https://github.com/Siddhantbht02/CogniQuery.git
cd CogniQuery
```

### 2. Backend Setup & Run

The backend handles the connection to the AI model.

```bash
cd backend

# 1. Create and activate a virtual environment (Recommended)
python3 -m venv venv
source venv/bin/activate  # Use 'venv\Scripts\activate' on Windows

# 2. Install dependencies (Assuming a Flask/FastAPI setup)
pip install -r requirements.txt
# Expected content of requirements.txt: flask, python-dotenv, requests, etc.

# 3. Configure Environment Variables
# Create a file named .env in the /backend directory and add your key:
echo 'AI_API_KEY="YOUR_LLM_API_KEY_HERE"' > .env
echo 'FLASK_RUN_PORT=5000' >> .env 

# 4. Run the Backend Server (e.g., using Flask)
flask run --port 5000 
# The server should start on http://127.0.0.1:5000
```

### 3. Frontend Setup & Run

The frontend is a standard JavaScript application that relies on a local server or extension to run.

```bash
cd ../frontend

# 1. Install dependencies (if using a package.json for build tools)
npm install

# 2. Run the Frontend 
# If a build script is defined:
npm start

# If running as plain HTML/JS (simplest method):
# You can open the index.html file directly in your browser, 
# or use a simple live server extension in your IDE (like VS Code's Live Server).
# Ensure the JavaScript is configured to call the backend at http://127.0.0.1:5000.
```

## ⚙️ API Endpoints (Backend)

The main interaction point between the client and the server is the query endpoint.

| Method | Endpoint | Description | Expected Body | Response Data |
|--------|----------|-------------|---------------|---------------|
| POST | `/api/query` | Submits a new query to the LLM for processing | `{ "query": "string" }` | `{ "response": "string", "sources": [] }` |
| GET | `/api/status` | Simple health check for the server | None | `{ "status": "ok" }` |

## 🗺️ Project Structure

The repository is organized into two primary directories:

```
CogniQuery/
├── backend/
│   ├── venv/                       # Python Virtual Environment
│   ├── .env                        # Environment variables (IGNORED by Git)
│   ├── app.py                      # Main Python server application
│   └── requirements.txt            # Python dependencies
│
├── frontend/
│   ├── index.html                  # Main application entry point
│   ├── style.css                   # Application styling
│   ├── script.js                   # Main application logic (fetch calls)
│   └── package.json                # Frontend dependencies/scripts (if any)
│
└── README.md                       # You are here!
```

## 🛣️ Roadmap & Future Enhancements

- **Streaming Responses**: Implement server-sent events (SSE) or WebSockets to stream the LLM response in real-time.
- **History/Memory**: Integrate a database (e.g., Firestore, Redis) to track conversation history.
- **RAG (Retrieval-Augmented Generation)**: Allow users to upload documents and query their custom knowledge base.
- **User Authentication**: Implement user sign-in for personalized history and settings.

## 🤝 Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

## 🧑 Contact

**Your Name**: Siddhantbht02 (GitHub)

**Project Link**: [https://github.com/Siddhantbht02/CogniQuery](https://github.com/Siddhantbht02/CogniQuery)

---

⭐ If you found this project helpful, please consider giving it a star on GitHub!
