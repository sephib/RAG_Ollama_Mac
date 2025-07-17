# RAG_Ollama_Deepseek_Streamlit_Mac
 Local RAG Chatbot leveraging deepseek R1 to run on Mac
 Based on this repo by pruthvirajcyn https://github.com/pruthvirajcyn/RAG_Ollama_Deepseek_Streamlit; https://medium.com/@pruthvirajc/implementing-a-local-rag-chat-bot-with-ollama-streamlit-and-deepseek-r1-a-practical-guide-46b1903f011f

 I use this repo for my local RAG, I will update to latest requirements and try out different models.
 As of today, 20250717, I am going to try nomic v2 embeddings and gemma3n.
 
 To run the application use the following command: streamlit run ./src/UI.py

# Local RAG Chatbot with Ollama, Streamlit, and DeepSeek-R1

Welcome to the Local RAG Chatbot repository! This project demonstrates how to build a fully local Retrieval Augmented Generation (RAG) chatbot using Ollama, Streamlit, and the DeepSeek-R1 model. This setup allows you to create a powerful, privacy-focused conversational AI that operates entirely on your local machine.

## Table of Contents

1.  [Introduction](#introduction)
2.  [Features](#features)
3.  [Prerequisites](#prerequisites)
4.  [Installation](#installation)
5.  [Usage](#usage)
6.  [Customization](#customization)

## 1. Introduction

This repository provides the code and instructions to implement a local RAG chatbot. The chatbot leverages:

* **Ollama:** Ollama is a lightweight, extensible framework for building and running large language models such as llama, mistral, deepseek, etc. on the local machine. IN this project we run the DeepSeek-R1 large language model locally. 
* **Streamlit:** Our project enables communication through a chatbot interface, leveraging Streamlit, a highly intuitive and user-friendly tool for building interactive web applications.
* **DeepSeek-R1:** A powerful open-source language model for generating human-like responses.
* **Retrieval Augmented Generation (RAG):** To enhance the chatbot's responses with relevant information from local documents.

The core idea is to provide a practical guide for users who wish to build a secure and customizable chatbot without relying on external APIs or cloud services.

## 2. Features

* **Local Execution:** Runs entirely on your local machine, ensuring data privacy and security.
* **Document Ingestion:** Allows users to upload and index local documents for RAG.
* **Interactive Chat Interface:** Provides a user-friendly Streamlit interface for interacting with the chatbot.
* **DeepSeek-R1 Integration:** Utilizes the DeepSeek-R1 model for high-quality responses.
* **Customizable Prompting:** Enables users to modify prompts for tailored chatbot behavior.
* **Simple Setup:** Designed for easy installation and configuration.

## 3. Prerequisites

Before getting started, ensure you have the following installed:

* **Python 3.7+:** Python is required for running the application.
* **Ollama:** Download and install Ollama from ([https://ollama.com/]).
* **DeepSeek-R1 Model:** Pull the DeepSeek-R1 model in Ollama by running `ollama pull deepseek-r1`.
* **Pip:** Python package installer.

## 4. Installation

1.  **Clone the Repository:**

    ```bash
    git clone https://github.com/eplt/RAG_Ollama_Deepseek_Streamlit_Mac.git
    cd RAG_Ollama_Deepseek_Streamlit
    ```

2.  **Create a Virtual Environment (Recommended):**

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Dependencies:**

    ```bash
    pip install -r ./src/requirements.txt
    ```

## 5. Usage

1.  **Run Ollama:**
    In another tab of command prompt/ terminal run the below
    ```bash
    ollama serve
    ollama pull deepseek-r1
    ollama pull nomic-embed-text
    ```

3.  **Upload Documents:**
    
    To upload your documents, put all pdf files in the data folder and run:
    ```bash
    python ./src/load_docs.py
    ```
    To reload/reset all the data in your vector database:
    ```bash
    python ./src/load_docs.py "--reset"
    ```

4.  **Run the Streamlit Application:**

    ```bash
    streamlit run ./src/UI.py
    ```
    
6.  **Chat with the Bot:**

    Enter your queries in the chat input and receive responses augmented with information from your documents.

## 6. Customization

* **Modify Prompts:** Edit the prompt templates in `app.py` to customize the chatbot's behavior.
* **Change Models:** You can replace DeepSeek-R1 with other models supported by Ollama. Remember to update the Ollama pull command and the model name in the code.
* **Adjust Retrieval Parameters:** Fine-tune the retrieval parameters in the code to optimize document retrieval.
* **Extend Functionality:** Add more features to the Streamlit interface or integrate with other tools.

## 7. Troubleshooting

* **Ollama Issues:** If you encounter issues with Ollama, refer to the official Ollama documentation.
* **Dependency Issues:** Ensure all dependencies are installed correctly. If you encounter errors, try reinstalling the virtual environment.
* **Model Loading Issues:** Verify that the DeepSeek-R1 model is pulled correctly in Ollama.

