"""
It is a small helper file that you will run once (or whenever you want to refresh your Pinecone index).
It calls your RAGPipeline.ingest_docs() method to load and embed documents from your local folder (./data/docs) into Pinecone.

This makes your RAG pipeline usable — it ensures Pinecone has context documents before your chatbot starts querying.

# How to run it --- ' python -m scripts.seed_vector_index '

"""
# import asyncio
# from app.services.rag.pipeline import RAGPipeline

# async def main():
#     rag = RAGPipeline()
#     await rag.ingest_docs()   # Loads from DOCUMENTS_PATH in config.py

# if __name__ == "__main__":
#     asyncio.run(main())
