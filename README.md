# 📄 LLM Document Processing System (RAG)

[![Python](https://img.shields.io/badge/Python-3.9+-blue?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-orange?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Google Gemini API](https://img.shields.io/badge/Google%20Gemini%20API-Enabled-purple?style=flat-square&logo=google&logoColor=white)](https://ai.google.dev/)
[![Deployed On Render](https://img.shields.io/badge/Deployed%20On-Render-4078c0?style=flat-square&logo=render&logoColor=white)](https://render.com/) <!-- Or Vercel -->

An intelligent system leveraging Large Language Models (LLMs) to extract, process, and retrieve relevant information from unstructured documents based on natural language queries. This project implements a Retrieval-Augmented Generation (RAG) architecture for accurate and explainable insights.

## ✨ Features

*   **Natural Language Querying:** Understands plain English queries for complex information retrieval.
*   **Multi-Document Type Support:** Processes PDFs, DOCX, and TXT files using `PyMuPDF` and `python-docx`.
*   **Semantic Search:** Utilizes Google's embedding models (`text-embedding-004`) and FAISS for contextual information retrieval, not just keyword matching.
*   **LLM-Powered Reasoning:** Employs the Google Gemini 1.5 Pro model for intelligent decision-making and response generation.
*   **Explainable AI:** Provides structured JSON responses including a clear decision (Approved/Rejected), calculated amounts (if applicable), and justifications with direct references to supporting clauses from the source documents.
*   **Dynamic Document Processing:** Supports on-the-fly processing of uploaded documents for instant query results, or uses a pre-built knowledge base for fixed document sets.
*   **Scalable API:** Deployed as a web API using Flask and Gunicorn, ready for integration into downstream applications.
*   **User-Friendly Frontend:** A simple web interface for interactive querying and clear result display.

## 💡 How It Works (Architecture)

This system is built on the **Retrieval-Augmented Generation (RAG)** paradigm to combine the strengths of information retrieval with large language models.

1.  **Document Ingestion:** Documents (PDFs, DOCX, TXT) are read and processed into raw text.
2.  **Text Chunking:** The extracted text is split into smaller, semantically coherent chunks using a custom chunking strategy.
3.  **Embedding Generation:** Each text chunk is converted into a numerical vector (embedding) using Google's `text-embedding-004` model.
4.  **Vector Store (FAISS):** These embeddings are stored in a FAISS index, which enables rapid similarity search.
    *   **Optimization for Deployment:** The knowledge base (embeddings and chunks) is **pre-built and committed** to the repository to ensure fast serverless function cold starts.
5.  **Query Processing:**
    *   The user's natural language query is first used by an LLM (Gemini) to generate multiple "hypothetical questions" to improve retrieval (Multi-Query Retrieval).
    *   The original query and these hypothetical questions are then embedded.
6.  **Semantic Retrieval:** The system performs a similarity search in the FAISS index to find the most relevant document chunks based on the combined query embeddings.
7.  **LLM Generation:** The retrieved relevant chunks, along with the original user query, are fed into the Google Gemini 1.5 Pro model.
8.  **Structured Output:** The LLM, guided by a strict prompt, evaluates the information and generates a structured JSON response containing the decision, amount, and justification with supporting clauses.

## 🚀 Getting Started (Local Development)

Follow these steps to set up and run the project on your local machine.

### Prerequisites

*   **Python 3.9+:** (Recommended: Python 3.9 or 3.10 for optimal `faiss-cpu` compatibility).
*   **pip:** Python package installer (comes with Python).
*   **Node.js & npm:** Required for running the frontend testing script (`send_requests.js`). Download from [nodejs.org](https://nodejs.org/).
*   **Git:** Version control system.
*   **VS Code:** Recommended IDE.

### 1. Clone the Repository

Open your terminal (e.g., VS Code Terminal, Git Bash, PowerShell) and clone the project:

```bash
git clone https://github.com/Siddhantbht02/VScodeVercelGemini.git
cd VScodeVercelGemini # Navigate into your project folder
