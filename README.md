# Code-Geni-AI-Explainer-and-Code-Generator
![License: MIT](https://img.shields.io/badge/License-MIT-pink.svg)

**CodeGene** is an **AI-powered application** built with **Streamlit** that helps users **explain, generate, and analyze code or content** from multiple input formats — including **text, PDFs, CSVs, and images**.  
It integrates **Ollama (LLMs)**, **OCR**, and **Speech Recognition** to deliver an **interactive and intelligent chat experience**.

---

##  **Key Features**

**AI Chat Interface**
  - Conversational interface powered by **Ollama (LLaMA2)**
  - Understands technical queries and provides contextual code explanations
  - Works with both text and image-based questions

**File Understanding**
  - Supports **Text**, **PDF**, and **CSV** file uploads
  - Automatically extracts, summarizes, and explains file content

**OCR (Image-to-Text)**
  - Upload **screenshots or code images**
  - Uses **Tesseract OCR** to extract embedded text or code for analysis

**Voice-to-Text Interaction**
  - Use your **microphone to speak queries**
  - Converts speech into text via **SpeechRecognition API**

**Smart Tools Section**
  - Includes options for:
    -  **Image Generator (placeholder)**
    -  **Deep Research Assistant (AI-based)**

**Session Management**
  - Each chat is stored with a **unique UUID**
  - “New Chat” and “Recent Chats” handled seamlessly

**Beautiful Custom UI**
  - Built using **Streamlit** and **custom CSS**
  - Features floating input boxes, clean layout, and responsive sidebar

---

##  **Tech Stack**

| **Category** | **Technology Used** |
|---------------|---------------------|
| Frontend | Streamlit + Custom CSS |
| Backend | Python |
| AI Model | Ollama (LLaMA2) |
| Speech-to-Text | SpeechRecognition |
| OCR | Tesseract (pytesseract) |
| File Handling | PyPDF2, pandas |
| Image Processing | Pillow |
| Utilities | io, base64, uuid, traceback |

---

##  **Installation & Setup**

### **1️⃣ Clone the Repository**

- git clone https://github.com/Rondla-Srujana/Code-Geni-AI-Explainer-and-Code-Generator.git
- cd Code-Geni-AI-Explainer-and-Code-Generator

### **2️⃣ Create and Activate Virtual Environment**

- python -m venv venv
- venv\Scripts\activate      # For Windows
- source venv/bin/activate   # For Linux/Mac

### **3️⃣ Configure Tesseract Path**

- pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

### **4️⃣ Configure Tesseract Path**

- streamlit run app.py
- Then open your browser and visit:
- 👉 http://localhost:8501

## **Use Cases**

- Explain or debug uploaded code snippets
- Extract and analyze text/code from images
- Summarize or analyze content from PDF/CSV/Text files
- Perform deep research queries using LLMs
- Chat with AI to learn or generate new code


