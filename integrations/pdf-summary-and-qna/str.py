import streamlit as st
import pdfplumber
from summary_agent import ResearchPaperSummarizer
from qna_agent import ResearchPaperQnA
import asyncio
import os
import tempfile




def about_us():
    st.title("About Us")
    st.image("logo.png", width=100)  # Adjust the width as needed
    st.write("""
Welcome to DOCRead! We specialize in making your PDF documents more accessible and actionable than ever before. With DOCRead, you can seamlessly convert your PDFs into editable text, enabling easy search, analysis, and manipulation of your documents.

But that's not all – we don't just stop at conversion. Our model goes the extra mile by providing you with a concise summary of the extracted text, allowing you to quickly grasp the key insights and information within your documents.

And to make your experience even more interactive and efficient, we offer a built-in chatbot feature. With our chatbot, you can ask questions about the contents of your PDFs, receive instant responses, and delve deeper into the nuances of your documents.

At DOCRead, we're proud to have developed our model using cutting-edge technology. We've leveraged uAgents by Fetch.ai to create an intelligent system that delivers accurate results and enhances your document processing experience.

DOCRead is your all-in-one solution for PDF processing, summarization, and interaction. Experience the power of intelligent document handling today!
    """)

async def handle_uploaded_file(uploaded_file):
    if uploaded_file is not None:
        try:
            # Save the uploaded file to a temporary location
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name

            with pdfplumber.open(tmp_path) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text()

            # Remove the temporary file
            os.unlink(tmp_path)

            # Generate summary
            summarizer = ResearchPaperSummarizer()
            summary = await summarizer.handle_request(text)
            st.subheader("Document Text")
            st.write(text)
            st.subheader("Summary")
            st.write(summary)

            # Chatbot UI
            user_input = st.text_area("User Input")
            if user_input:
                qna_agent = ResearchPaperQnA()
                answer = await qna_agent.handle_request(text, user_input)
                st.text_area("Chatbot Response", answer, height=200)

        except Exception as e:
            st.error(f"An error occurred: {e}\nPlease check the uploaded PDF file.")
    else:
        st.write("No file uploaded. Go to Upload File to upload a PDF.")

def main():
    os.environ["HUGGING_FACE_API_TOKEN"] = "HUGGING_FACE_TOKEN_HERE"     #Set the API Token
    st.sidebar.title("DOCRead")
    page = st.sidebar.radio("Navigation", ["Home", "About Us", "Upload File", "Results"])

    if page == "Home":
        st.title("Welcome to DOCRead")
        st.write("Your Solution to Complex DOCS")
        st.image("logo.png", width=300)  # Adjust the width as needed

    elif page == "About Us":
        about_us()

    elif page == "Upload File":
        uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])
        if uploaded_file is not None:
            st.session_state["uploaded_file"] = uploaded_file
            st.session_state["page"] = "Results"  # Redirect to the "Results" tab
        else:
            st.write("No file uploaded yet.")

    elif page == "Results":
        uploaded_file = st.session_state.get("uploaded_file")
        if uploaded_file is not None:
            asyncio.run(handle_uploaded_file(uploaded_file))
        else:
            st.write("No file uploaded. Go to Upload File to upload a PDF.")

if __name__ == "__main__":
    main()