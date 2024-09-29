import os
import logging
import json
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from typing import List, Dict
from langchain.document_loaders import PyPDFLoader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS

from langchain.chains import RetrievalQA
from langchain.llms import OpenAI


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


UPLOAD_DIRECTORY = "uploaded_files"


os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

app = FastAPI()


OPENAI_API_KEY = "your-own-open-ai-key"  


@app.post("/upload/")
async def upload_pdf_json_and_questions(
        questions: str = Form(...),  
        file: UploadFile = File(...),
        source: str = Form(...)  
) -> Dict[str, str]:
    """
    FastAPI endpoint to upload either a PDF or JSON and a list of questions.
    Processes the input using a vector database (FAISS) and LangChain with OpenAI.
    Returns answers for each question.
    """
    
    try:
        questions_dict = json.loads(questions)
        question_list = questions_dict.get("question", [])
    except json.JSONDecodeError:
        raise HTTPException(status_code=400,
                            detail="Invalid questions format. It should be a valid JSON object with a 'question' field.")

    file_extension = file.filename.split('.')[-1].lower()

    
    if source == "pdf" and file_extension == "pdf":
        pdf_filename = file.filename
        logger.info(f"Uploaded PDF filename: {pdf_filename}")

        
        file_path = os.path.join(UPLOAD_DIRECTORY, pdf_filename)
        with open(file_path, "wb") as f:
            content = await file.read()  
            f.write(content)  

        logger.info(f"PDF saved locally at: {file_path}")

        
        loader = PyPDFLoader(file_path)
        documents = loader.load()

    elif source == "json" and file_extension == "json":
        json_filename = file.filename
        logger.info(f"Uploaded JSON filename: {json_filename}")

        
        json_file_path = os.path.join(UPLOAD_DIRECTORY, json_filename)
        with open(json_file_path, "wb") as f:
            content = await file.read()  
            f.write(content)  

        logger.info(f"JSON saved locally at: {json_file_path}")

        
        try:
            with open(json_file_path, "r") as f:
                json_data = json.load(f)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON file content.")

        
        json_text = json.dumps(json_data, indent=2)

        
        documents = [{"page_content": json_text}]

    else:
        raise HTTPException(status_code=400, detail="Invalid file type or source. Please upload either a PDF or JSON.")

    #  OpenAI Embeddings model for embedding generation
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

    #  FAISS as the vector store
    vectorstore = FAISS.from_documents(documents, embeddings)

    #  RetrievalQA chain using OpenAI's language model
    llm = OpenAI(openai_api_key=OPENAI_API_KEY)
    retriever = vectorstore.as_retriever()
    qa_chain = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever)

    #  Process each question and get the answer
    answers = {}
    for question in question_list:
        answer = qa_chain.run(question)
        answers[question] = answer
        logger.info(f"Question: {question}, Answer: {answer}")

    
    if os.path.exists(file_path):
        os.remove(file_path)
        logger.info(f"File deleted after processing: {file_path}")

    # answers as {q1: answer1, q2: answer2}
    return answers