#!/usr/bin/env python3
"""
Script to store test documents in Qdrant vector database.
This will process the test PDFs and store them with real embeddings.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.storage.services.file_processor import FileProcessor
from services.storage.services.embedding_service import EmbeddingService
from services.storage.services.vector_store import VectorStore
from shared.models import FileType
from shared.config import settings


async def main():
    """Store test documents in Qdrant."""
    print("🚀 Starting test document storage process...")
    
    # Initialize services
    file_processor = FileProcessor()
    embedding_service = EmbeddingService()
    vector_store = VectorStore()
    
    # Initialize vector store (create collection if needed)
    print("📊 Initializing vector store...")
    await vector_store.initialize()
    
    # Test document paths
    test_docs = [
        {
            "path": "test_docs/A_Comprehensive_Review_of_Low_Rank_Adaptation_in_Large_Language_Models_for_Efficient_Parameter_Tuning-1.pdf",
            "name": "lora_review.pdf"
        },
        {
            "path": "test_docs/Frontier AI Models for Key Use Cases (2025).pdf", 
            "name": "frontier_ai_models.pdf"
        }
    ]
    
    total_chunks_stored = 0
    
    for doc_info in test_docs:
        doc_path = doc_info["path"]
        doc_name = doc_info["name"]
        
        if not os.path.exists(doc_path):
            print(f"⚠️  Document not found: {doc_path}")
            continue
            
        print(f"\n📄 Processing document: {doc_name}")
        
        try:
            # Step 1: Extract text
            print("   📝 Extracting text...")
            text = await file_processor.extract_text(doc_path, FileType.PDF)
            print(f"   ✅ Extracted {len(text):,} characters")
            
            # Step 2: Create chunks
            print("   🔪 Creating chunks...")
            chunks = await file_processor.chunk_text(text, doc_name)
            print(f"   ✅ Created {len(chunks)} chunks")
            
            # Step 3: Generate embeddings
            print("   🧠 Generating embeddings...")
            texts = [chunk.content for chunk in chunks]
            embeddings = await embedding_service.generate_embeddings(texts)
            print(f"   ✅ Generated {len(embeddings)} embeddings")
            
            # Step 4: Add embeddings to chunks
            for chunk, embedding in zip(chunks, embeddings):
                chunk.embedding = embedding
            
            # Step 5: Store in Qdrant
            print("   💾 Storing in vector database...")
            await vector_store.store_chunks(chunks)
            print(f"   ✅ Stored {len(chunks)} chunks in Qdrant")
            
            total_chunks_stored += len(chunks)
            
        except Exception as e:
            print(f"   ❌ Error processing {doc_name}: {e}")
            continue
    
    print(f"\n🎉 Storage complete! Total chunks stored: {total_chunks_stored}")
    
    # Verify storage
    print("\n🔍 Verifying storage...")
    try:
        info = await vector_store.get_collection_info()
        print(f"   📊 Collection: {info['name']}")
        print(f"   📊 Total vectors: {info['vectors_count']}")
        print(f"   📊 Indexed vectors: {info['indexed_vectors_count']}")
        print(f"   📊 Status: {info['status']}")
        
        # List stored files
        files = await vector_store.list_files()
        print(f"   📁 Stored files: {files}")
        
    except Exception as e:
        print(f"   ⚠️  Could not verify storage: {e}")
    
    print("\n✅ All done! Documents are now stored in Qdrant and ready for retrieval testing.")


if __name__ == "__main__":
    asyncio.run(main())