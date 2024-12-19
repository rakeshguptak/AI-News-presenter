import os
import streamlit as st
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools import DuckDuckGoSearchResults
from langchain.docstore.document import Document
from langchain.chains.summarize import load_summarize_chain
from langchain.prompts import PromptTemplate
import requests
import json
import time

GOOGLE_API_KEY = ""  
DID_API_KEY = ""   

os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
genai.configure(api_key=GOOGLE_API_KEY)

llm = ChatGoogleGenerativeAI(
    model="gemini-pro",
    google_api_key=GOOGLE_API_KEY,
    temperature=0.0
)

def genvideo(img_url, summary, v_id):
    url = "https://api.d-id.com/talks"
    
    payload = {
        "source_url": img_url,
        "script": {
            "type": "text",
            "input": summary,
            "provider": {
                "type": "microsoft",
                "voice_id": v_id,
                "voice_config": {
                    "style": "Default"
                }
            }
        }
    }
    
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Basic {DID_API_KEY}"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  
        
        response_data = response.json()
        st.write("D-ID API Response:", response_data) 
        
        if "id" not in response_data:
            raise Exception(f"No ID in response: {response_data}")
            
        return response_data["id"]
        
    except requests.exceptions.RequestException as e:
        st.error(f"D-ID API Error: {str(e)}")
        raise Exception(f"D-ID API Error: {str(e)}")

def download_video(id):
    url = f"https://api.d-id.com/talks/{id}"
    
    headers = {
        "accept": "application/json",
        "authorization": f"Basic {DID_API_KEY}"
    }
    
    max_attempts = 10
    attempt = 0
    
    while attempt < max_attempts:
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            response_data = response.json()
            st.write(f"Video status check {attempt + 1}:", response_data)  
            
            if response_data.get("status") == "done" and "result_url" in response_data:
                return response_data["result_url"]
            elif response_data.get("status") == "error":
                raise Exception(f"Video generation failed: {response_data.get('error', 'Unknown error')}")
                
            attempt += 1
            time.sleep(15)  
            
        except requests.exceptions.RequestException as e:
            st.error(f"Error checking video status: {str(e)}")
            raise Exception(f"Error checking video status: {str(e)}")
    
    raise Exception("Video generation timed out")

ts = """
you are a news anchor for a global news channel, with this context generate a concise summary of the following:
{text}
"""
pt = PromptTemplate(template=ts, input_variables=["text"])

st.set_page_config(page_title="AI NEWS PRESENTER")
st.title("AI News Presenter - Nebula9.ai")


tab1, tab2 = st.tabs(["Search News", "Input Article"])

with tab1:
    qsn = st.text_area("Enter your search query")
    if st.button("Search and Present", key="search_button"):
        if qsn.strip():
            try:
                with st.spinner("Searching for news..."):
                    search = DuckDuckGoSearchResults(backend="news")
                    result = search.run(qsn)
                    data = result.replace("[snippet: ", "")
                    data = data[:-1]
                    docs = [Document(page_content=t) for t in data]
                    
                    chain = load_summarize_chain(llm, chain_type="stuff", prompt=pt)
                    summary = chain.run(docs)
                    
                    st.write("Generated summary:", summary)  
                    
                    with st.spinner("Generating video presentation..."):
                        video_id = genvideo(
                            "https://clips-presenters.d-id.com/lana/uXbrIxQFjr/kzlKYBZ2wc/image.png",
                            summary,
                            "en-US-JaneNeural"
                        )
                        
                        st.write("Waiting for video processing...")
                        video_url = download_video(video_id)
                        
                        if video_url:
                            st.video(video_url)
                        else:
                            st.error("Failed to generate video")
                            
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
        else:
            st.warning("Please enter a search query before submitting.")

with tab2:
    article_text = st.text_area("Paste your news article here", height=300)
    if st.button("Present Article", key="article_button"):
        if article_text.strip():
            try:
                with st.spinner("Processing article..."):
                    docs = [Document(page_content=article_text)]
                    chain = load_summarize_chain(llm, chain_type="stuff", prompt=pt)
                    summary = chain.run(docs)
                    
                    st.write("Generated summary:", summary)  
                    
                    with st.spinner("Generating video presentation..."):
                        video_id = genvideo(
                            "https://clips-presenters.d-id.com/lana/uXbrIxQFjr/kzlKYBZ2wc/image.png",
                            summary,
                            "en-US-JaneNeural"
                        )
                        
                        st.write("Waiting for video processing...")
                        video_url = download_video(video_id)
                        
                        if video_url:
                            st.video(video_url)
                        else:
                            st.error("Failed to generate video")
                            
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
        else:
            st.warning("Please enter an article before submitting.")