import os
from langchain_openai import ChatOpenAI
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()  # Load API keys

# Load API keys from environment variables
TAVILY_KEY = os.getenv("TAVILY_API_KEY")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

if not TAVILY_KEY:
    raise ValueError("TAVILY_API_KEY environment variable is not set")
if not OPENAI_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

# Initialize models
llm = ChatOpenAI(model="gpt-4o-mini", api_key=OPENAI_KEY)   # Lightweight + fast
tavily = TavilyClient(api_key=TAVILY_KEY)


def run_agent_query(query):
    """
    Runs Tavily search + LLM explanation.
    """

    # 1) Web search
    search_result = tavily.search(query)

    # 2) Generate final explanation
    prompt = f"""
    Analyze the following EEG-related question and provide a clear medical explanation.

    User Question:
    {query}

    Relevant medical search results:
    {search_result}

    Provide a short, human-friendly, medically accurate explanation.
    """

    response = llm.invoke(prompt)

    return response.content
