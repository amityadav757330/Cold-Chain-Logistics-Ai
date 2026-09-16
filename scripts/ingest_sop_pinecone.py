import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.documents import Document


load_dotenv()


SOP_PATH = (
    Path(__file__).parent.parent
    / "data"
    / "policy"
    / "Cold_Chain_Incident_SOP_v2.md"
)


def load_sop():
    if not SOP_PATH.exists():
        raise FileNotFoundError(
            f"SOP file not found: {SOP_PATH}"
        )

    with open(SOP_PATH, "r", encoding="utf-8") as file:
        content = file.read()

    return Document(
        page_content=content,
        metadata={
            "source_file": SOP_PATH.name,
            "document_type": "cold_chain_sop",
            "file_format": "markdown",
        },
    )


def split_sop(document):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=60,
    )

    return splitter.split_documents([document])


def create_embeddings():
    return HuggingFaceEmbeddings(
        model_name="BAAI/bge-m3"
    )


def upload_to_pinecone(documents, embeddings):
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    pinecone_index = os.getenv("PINECONE_INDEX")

    if not pinecone_api_key:
        raise ValueError(
            "PINECONE_API_KEY is missing from the .env file."
        )

    if not pinecone_index:
        raise ValueError(
            "PINECONE_INDEX is missing from the .env file."
        )

    os.environ["PINECONE_API_KEY"] = pinecone_api_key

    PineconeVectorStore.from_documents(
        documents=documents,
        embedding=embeddings,
        index_name=pinecone_index,
    )


def main():
    print("Loading SOP...")

    document = load_sop()

    print("Splitting SOP into chunks...")

    chunks = split_sop(document)

    print(f"Created {len(chunks)} chunks.")

    print("Loading embedding model...")

    embeddings = create_embeddings()

    print("Uploading SOP embeddings to Pinecone...")

    upload_to_pinecone(chunks, embeddings)

    print("SOP ingestion completed successfully.")


if __name__ == "__main__":
    main()