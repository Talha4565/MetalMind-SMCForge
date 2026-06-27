"""
ChromaDB client wrapper for signal memory.
Manages connection and collection lifecycle.
"""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Default to embedded ChromaDB (no separate container needed)
CHROMA_HOST = "localhost"
CHROMA_PORT = 8100


class SignalMemoryClient:
    """ChromaDB client for signal storage."""
    
    def __init__(self, host: str = None, port: int = None, persistent: bool = True):
        """
        Initialize ChromaDB client.
        
        Args:
            host: ChromaDB host (default: localhost)
            port: ChromaDB port (default: 8100)
            persistent: If True, use embedded mode with local storage
        """
        self.host = host or CHROMA_HOST
        self.port = port or CHROMA_PORT
        self.persistent = persistent
        self._client = None
        self._collections = {}
    
    def get_client(self):
        """Get or create ChromaDB client."""
        if self._client is not None:
            return self._client
        
        try:
            import chromadb
            
            if self.persistent:
                # Use embedded mode with local storage
                persist_dir = Path(__file__).parent.parent / "data" / "chroma_db"
                persist_dir.mkdir(parents=True, exist_ok=True)
                self._client = chromadb.PersistentClient(path=str(persist_dir))
                logger.info(f"ChromaDB initialized (persistent mode): {persist_dir}")
            else:
                # Connect to remote ChromaDB server
                self._client = chromadb.HttpClient(host=self.host, port=self.port)
                logger.info(f"ChromaDB connected to {self.host}:{self.port}")
            
            return self._client
        
        except ImportError:
            logger.error("chromadb not installed. Run: pip install chromadb")
            raise
        except Exception as e:
            logger.error(f"Failed to connect to ChromaDB: {e}")
            raise
    
    def get_collection(self, name: str, embedding_function=None):
        """Get or create a ChromaDB collection."""
        if name in self._collections:
            return self._collections[name]
        
        client = self.get_client()
        
        try:
            if embedding_function:
                collection = client.get_or_create_collection(
                    name=name,
                    embedding_function=embedding_function,
                    metadata={"hnsw:space": "cosine"}
                )
            else:
                collection = client.get_or_create_collection(
                    name=name,
                    metadata={"hnsw:space": "cosine"}
                )
            
            self._collections[name] = collection
            logger.info(f"Collection '{name}' ready")
            return collection
        
        except Exception as e:
            logger.error(f"Failed to get collection '{name}': {e}")
            raise
    
    def reset(self):
        """Reset client state."""
        self._client = None
        self._collections.clear()
