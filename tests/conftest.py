import sys
import types


# Stub optional LLM provider packages so importing modules that depend on
# them does not require the actual heavy dependencies during tests.
sys.modules.setdefault("langchain_anthropic", types.SimpleNamespace(ChatAnthropic=object))
sys.modules.setdefault("langchain_deepseek", types.SimpleNamespace(ChatDeepSeek=object))
sys.modules.setdefault(
    "langchain_google_genai", types.SimpleNamespace(ChatGoogleGenerativeAI=object)
)
sys.modules.setdefault("langchain_groq", types.SimpleNamespace(ChatGroq=object))
sys.modules.setdefault("langchain_xai", types.SimpleNamespace(ChatXAI=object))
sys.modules.setdefault(
    "langchain_openai", types.SimpleNamespace(ChatOpenAI=object, AzureChatOpenAI=object)
)
sys.modules.setdefault("langchain_gigachat", types.SimpleNamespace(GigaChat=object))
sys.modules.setdefault("langchain_ollama", types.SimpleNamespace(ChatOllama=object))

