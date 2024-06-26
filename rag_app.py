from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import NLTKTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
import streamlit as st

with open('api_key.txt') as f:
    api_key = f.read()

loader = PyPDFLoader("leavenocontext.pdf")
data = loader.load_and_split()
text_splitter = NLTKTextSplitter(chunk_size=500, chunk_overlap=100)

chunks = text_splitter.split_documents(data)
print(type(chunks[0]))


chat_model = ChatGoogleGenerativeAI(google_api_key=api_key, 
                                   model="gemini-1.5-pro-latest")
embedding_model = GoogleGenerativeAIEmbeddings(google_api_key=api_key, 
                                               model="models/embedding-001")

db = Chroma.from_documents(chunks, embedding_model, persist_directory="./chroma_db_")


db.persist()

db_connection = Chroma(persist_directory="./chroma_db_", embedding_function=embedding_model)

retriever = db_connection.as_retriever(search_kwargs={"k": 5})

print(type(retriever))

chat_template = ChatPromptTemplate.from_messages([
 
    SystemMessage(content="""You are a Helpful AI Bot. 
    You take the context and question from user. Your answer should be based on the specific context."""),

    HumanMessagePromptTemplate.from_template("""Aswer the question based on the given context.
    Context:
    {context}
    
    Question: 
    {question}
    
    Answer: """)
])

from langchain_core.runnables import RunnablePassthrough

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

from langchain_core.output_parsers import StrOutputParser

output_parser = StrOutputParser()

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | chat_template
    | chat_model
    | output_parser
)

def main():
    try:
        st.title('📃Clarify your Doubts on paper "Leave No Context"🛫')
        st.subheader('An ai driven question answer system on paper leave no context')

        # User Input: Question
        user_question = st.text_input('Enter your query related to above paper..')

        if st.button('View '):
            if user_question:
                response = rag_chain.invoke(user_question)

                if response:
                    st.subheader('View solution : ')
                    st.write(response)
                else: st.warning('Please enter the questions related to the given paper')
            
            elif user_question == '':
                st.warning('Enter your query')

    except Exception as e: 
        st.error(f'Error Occured: {e}')

if __name__ == '__main__':
    main()



