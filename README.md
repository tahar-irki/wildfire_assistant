
# ForestGuard AI 🌲🔥

### Smart Forest Fire Chatbot Using Fine-Tuning and RAG

ForestGuard AI is an intelligent chatbot designed to provide
information about forest fires, prevention, detection, safety
procedures, and post-fire recovery.

The project uses a fine-tuned Large Language Model (LLM)
combined with Retrieval-Augmented Generation (RAG) to provide
domain-specific and context-aware answers.

## 🎯 Project Objectives

- Develop a specialized forest-fire assistant.
- Fine-tune Qwen2.5-0.5B-Instruct using LoRA.
- Build a forest-fire knowledge base using official documents.
- Implement a RAG pipeline for knowledge retrieval.
- Develop a chatbot interface.
- Evaluate the performance of the original and fine-tuned models.

## 🧠 AI Architecture

The project combines:

1. **Qwen2.5-0.5B-Instruct**
   - Pretrained language model.
   - Used as the foundation of the chatbot.

2. **LoRA Fine-Tuning**
   - Specializes the model for forest-fire questions.
   - Reduces the number of trainable parameters.

3. **Retrieval-Augmented Generation (RAG)**
   - Retrieves information from external forest-fire documents.
   - Provides relevant context to the language model.

## 🛠️ Technologies

- Python
- PyTorch
- Hugging Face Transformers
- PEFT / LoRA
- TRL
- Sentence Transformers
- FAISS
- FastAPI
- Vue.js / Streamlit (frontend choice to be finalized)

## 📁 Project Structure

```text
backend/
    model/
    rag/
    api/

frontend/
data/
documents/
notebooks/
tests/
docs/
```

## ⚙️ Installation

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/ForestGuard-AI.git
cd ForestGuard-AI
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies once requirements.txt is prepared:

```bash
pip install -r backend/requirements.txt
```

## 👥 Team

- Member 1: Deep Learning and Model Training
- Member 2: Dataset Engineering and RAG
- Member 3: Frontend Development and Integration

## 📊 Evaluation

The project will compare:

- Original Qwen2.5-0.5B-Instruct
- Fine-tuned Qwen2.5-0.5B-Instruct
- Fine-tuned Qwen combined with RAG

## ⚠️ Disclaimer

ForestGuard AI is an educational information assistant.
It does not replace official emergency services or
professional firefighting instructions.

## 📌 Project Status

Under Development 🚧
