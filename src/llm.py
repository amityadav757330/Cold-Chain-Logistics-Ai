from langchain_ollama import ChatOllama


def get_llm():
    return ChatOllama(
        model="qwen2.5:1.5b",
        temperature=0.2,
        num_predict=300,
    )