# Week 3 Internship Documentation

**Program:** Tachyon - AIML Internship Training Program v4.0  
**Week:** Week 3  
**Topic:** Gen AI Fundamentals + Basic RAG & Q&A Bot on GCP  
**Week Owner:** Gaurav  
**Project:** VoltStream Smart Energy Monitoring Application  

## 1. Week 3 Overview

In Week 3, I focused on understanding the fundamentals of Generative AI and applying them in the VoltStream application. The main goal was to build a working AI chatbot using the Gemini API and implement a basic Retrieval-Augmented Generation based Q&A flow for energy-efficiency documents.

The completed work includes:

- Configuring the Gemini API key in the backend environment.
- Creating a `/api/v1/chat` endpoint that sends user questions to Gemini and returns natural-language answers.
- Building a chatbot interface in the React frontend.
- Creating a document-based Q&A flow using PDF/text content, chunking, embeddings, ChromaDB storage, retrieval, and grounded answers.
- Testing the chatbot with both general questions and energy-related questions.
- Learning the core concepts of LLMs, tokenization, embeddings, vector databases, semantic search, and RAG.

## 2. Learning Objectives Completed

### 2.1 Large Language Models

I learned that a Large Language Model is an AI model trained on a large amount of text data. It can understand user prompts and generate natural-language responses. In this project, Gemini is used as the LLM to answer user questions in the chatbot.

### 2.2 Transformers

I understood that transformer models are the foundation of modern LLMs. They use attention mechanisms to understand relationships between words and context in a sentence. This allows the model to generate meaningful and context-aware answers.

### 2.3 Tokenization

Tokenization is the process of splitting text into smaller units called tokens. These tokens may be words, parts of words, or characters. LLMs process tokens instead of raw text.

Example:

```text
Input: What is solar energy?
Tokens: What | is | solar | energy | ?
```

### 2.4 Embeddings

An embedding vector is a numerical representation of text that captures its meaning, so similar text has similar vectors.

In this project, document chunks are converted into vectors so that the system can find the most relevant document parts for a user question.

### 2.5 Foundation Models

Foundation models are large AI models trained on broad datasets and can be adapted to many tasks such as chatbots, summarization, Q&A, and code generation. Gemini is an example of a foundation model.

### 2.6 Prompt Engineering

I learned and practiced the following prompt engineering patterns:

- **Zero-shot prompting:** Asking a question directly without examples.
- **Few-shot prompting:** Giving examples before asking the model to answer.
- **Chain-of-thought style prompting:** Asking the model to reason step by step when needed.
- **Role-based prompting:** Giving the model a role, such as "You are VoltSenseBot, a helpful assistant."

### 2.7 Vector Databases

I learned that a vector database stores embedding vectors and allows semantic search. Instead of matching only keywords, it searches based on meaning. In this project, ChromaDB is used for storing and retrieving document chunks.

### 2.8 Semantic Search

Semantic search finds content based on meaning rather than exact keyword matching.

Example:

```text
Question: How can I reduce electricity usage at night?
Relevant document text: Reduce standby loads and schedule high-power appliances during solar production hours.
```

Even if the exact words are different, semantic search can still find the relevant answer.

## 3. Mandatory Resources Completed

The following learning resources were completed during Week 3:

1. Introduction to Generative AI - Google Skills Boost
2. DeepLearning.AI - Vector Databases & Embeddings Applications
3. ChromaDB Getting Started
4. DeepLearning.AI - Building Apps with Vector Databases

These resources helped me understand how Gen AI applications are built and how document-based Q&A systems use embeddings and vector search.

## 4. Work Completed in VoltStream Project

## 4.1 Gemini API Key Configuration

The Gemini API key was configured in the project `.env` file.

Environment variables used:

```env
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=models/gemini-2.5-flash
```

The backend loads the environment variables using `python-dotenv`.

Relevant backend file:

```text
backend/main.py
```

The Gemini configuration is handled in:

```text
backend/ai_service.py
```

## 4.2 Chatbot Endpoint

A FastAPI endpoint was created for chatbot messages.

Endpoint:

```http
POST /api/v1/chat
```

Request body:

```json
{
  "message": "Who is Modi?"
}
```

Response body:

```json
{
  "answer": "Narendra Modi is the current Prime Minister of India."
}
```

This confirms that the chatbot works like a Gemini-powered assistant and can answer general questions as well as energy-related questions.

## 4.3 Chatbot Backend Logic

The backend uses the `google-generativeai` package to call Gemini.

Main function:

```text
generate_chat_response(message)
```

This function:

1. Receives the user message.
2. Applies small corrections only for energy-related typos.
3. Configures Gemini using the API key.
4. Sends the prompt to the Gemini model.
5. Returns the generated answer.

The chatbot prompt tells Gemini to answer directly and correctly on any topic, while also giving practical energy guidance when the question is related to energy, solar, devices, or billing.

## 4.4 Chatbot Frontend UI

The React frontend contains a chatbot screen called VoltSenseBot.

Relevant file:

```text
frontend/src/components/AIAssistant.jsx
```

Frontend features completed:

- User can type a question.
- The message is sent to `/api/v1/chat`.
- The chatbot displays Gemini's answer.
- The UI shows a loading state while the bot is thinking.
- The user can stop generation.
- The user can edit and regenerate a previous prompt.
- The document upload button was removed from the chatbot to keep the chat interface simple.

## 4.5 RAG Q&A Bot

A basic RAG Q&A system was implemented for energy-efficiency documents.

RAG pipeline:

```text
PDF/Text document -> extract text -> split into chunks -> create embeddings -> store in ChromaDB -> retrieve relevant chunks -> generate grounded answer
```

The system uses:

- Reference documents stored in `backend/data`.
- Text chunking for splitting documents.
- Embedding vectors for semantic search.
- ChromaDB for vector storage.
- A Q&A endpoint for document-based answers.

Endpoint:

```http
POST /api/v1/qa
```

Request body:

```json
{
  "question": "What is the recommended panel angle for maximum solar output?"
}
```

Expected behavior:

- If the answer is found in the document, the bot returns the answer.
- If the answer is not found, the bot returns:

```text
I don't have that information.
```

This satisfies the requirement that the Q&A bot should not hallucinate for out-of-scope document questions.

## 5. API Endpoints Implemented

| Endpoint | Method | Purpose |
|---|---:|---|
| `/api/v1/chat` | POST | Gemini-powered general chatbot |
| `/api/v1/qa` | POST | Document-based Q&A |
| `/api/v1/qa/document` | GET | Returns indexed document status |
| `/health` | GET | Backend health check |

## 6. Midweek Check-In

### 6.1 Gemini API Key Configured

The Gemini API key was added to the `.env` file and loaded by the backend. The chatbot endpoint successfully returns responses from Gemini.

### 6.2 `/chat` Endpoint Returning Responses

The `/api/v1/chat` endpoint was tested using a general question.

Test question:

```text
Who is Modi?
```

Output:

```text
Narendra Modi is the current Prime Minister of India.
```

This confirms that the chatbot is working correctly.

### 6.3 Embedding Vector Definition

An embedding vector is a list of numbers that represents the meaning of text so that similar text can be searched and compared by meaning.

## 7. End-of-Week Checkpoint

### Demo 1: Live Chat Endpoint

The chatbot was tested using the `/api/v1/chat` endpoint.

Example request:

```json
{
  "message": "What is solar energy?"
}
```

Example response:

```text
Solar energy is energy from sunlight that can be converted into electricity using solar panels.
```

This demonstrates that Gemini is successfully connected and returning natural-language responses.

### Demo 2: Q&A Bot Script / Endpoint

The document Q&A flow was tested using an energy-efficiency question.

Example:

```text
What is the recommended panel angle for maximum solar output?
```

If the information is available in the indexed document, the bot answers from the document. If the information is not available, it returns:

```text
I don't have that information.
```

This proves that the RAG bot is grounded in the document and avoids answering out-of-scope questions.

## 8. Technical Architecture

## 8.1 Backend

Technology used:

- Python
- FastAPI
- Gemini API
- ChromaDB
- pypdf
- SQLite
- python-dotenv

Main files:

```text
backend/main.py
backend/api.py
backend/ai_service.py
backend/data_models.py
backend/data/
```

Backend responsibilities:

- Load environment variables.
- Configure Gemini API.
- Expose chatbot and Q&A endpoints.
- Process documents.
- Generate embeddings.
- Store and query vector data.
- Return answers to frontend.

## 8.2 Frontend

Technology used:

- React
- Vite
- JavaScript
- CSS
- Lucide icons

Main files:

```text
frontend/src/components/AIAssistant.jsx
frontend/src/api.js
frontend/src/styles.css
```

Frontend responsibilities:

- Display chatbot UI.
- Accept user input.
- Call backend API.
- Show bot responses.
- Show loading state.
- Allow prompt editing and regeneration.

## 9. Testing Performed

### 9.1 Backend Compilation Test

The backend code was compiled successfully.

Command:

```bash
python -m compileall backend
```

### 9.2 Frontend Build Test

The frontend build was tested successfully.

Command:

```bash
npm run build
```

Result:

```text
Build completed successfully.
```

### 9.3 Chat API Test

Endpoint:

```http
POST /api/v1/chat
```

Question:

```text
Who is Modi?
```

Response:

```text
Narendra Modi is the current Prime Minister of India.
```

### 9.4 Energy Question Test

Question:

```text
What is a solar panel?
```

Response:

```text
A solar panel is a device that converts sunlight into electricity using photovoltaic cells.
```

### 9.5 Typo Handling Test

Question:

```text
What is solr panel?
```

The backend interprets `solr` as `solar` for energy-related questions and returns a correct solar panel answer.

## 10. Problems Faced and Fixes

### Problem 1: General Questions Were Getting Changed Incorrectly

Earlier, the chatbot tried to correct every user question using energy document words. Because of this, a question like:

```text
Who is Modi?
```

was incorrectly changed to:

```text
Who is Most?
```

### Fix

The correction logic was changed so that typo correction only runs for energy-related questions. General questions are now sent directly to Gemini without modification.

### Problem 2: Chatbot UI Had Document Upload Button

The chatbot UI had a document upload button, but it was not required for the normal chatbot flow.

### Fix

The document upload button and related frontend upload logic were removed from the chatbot UI.

## 11. Final Deliverables

Completed deliverables for Week 3:

- Gemini API key configured.
- `/api/v1/chat` endpoint implemented.
- Gemini-powered chatbot working.
- React chatbot UI implemented.
- Chatbot answers general and energy-related questions.
- Basic RAG Q&A bot implemented.
- Document chunking and vector search implemented.
- ChromaDB used for document retrieval.
- Q&A bot returns grounded answers.
- Out-of-scope document questions return `I don't have that information.`
- Frontend build verified.
- Backend functionality verified.
- Weekly documentation prepared.

## 12. Conclusion

Week 3 helped me understand how Generative AI applications are built using LLMs, prompts, embeddings, vector databases, and RAG pipelines. I successfully applied these concepts in the VoltStream project by creating a Gemini-powered chatbot and a document-based Q&A system.

The final chatbot can answer normal user questions using Gemini and can also provide practical energy-related guidance. The Q&A bot can retrieve relevant information from indexed documents and return grounded answers, which is an important part of building reliable AI applications.

