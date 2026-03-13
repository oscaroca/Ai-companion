"""
Memory system with semantic search for conversation history.
Stores messages with embeddings for context-aware retrieval.
"""

import sqlite3
import json
import pickle
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    np = None

from config.settings import MemoryConfig
from utils.logging_config import get_logger


logger = get_logger(__name__)


@dataclass
class Message:
    """Conversation message."""
    id: Optional[int]
    user_id: str
    role: str  # user, assistant, system
    content: str
    timestamp: datetime
    embedding: Optional[Any] = None  # numpy array
    metadata: Dict[str, Any] = field(default_factory=dict)


class MemorySystem:
    """Manages conversation memory with semantic search."""
    
    # Database schema
    SCHEMA = """
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        embedding BLOB,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        metadata TEXT,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    );
    
    CREATE INDEX IF NOT EXISTS idx_messages_user_time 
        ON messages(user_id, timestamp DESC);
    CREATE INDEX IF NOT EXISTS idx_messages_role 
        ON messages(role);
    
    CREATE TABLE IF NOT EXISTS user_context (
        user_id TEXT NOT NULL,
        key TEXT NOT NULL,
        value TEXT NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, key),
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    );
    
    CREATE TABLE IF NOT EXISTS conversation_summaries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        summary TEXT NOT NULL,
        start_time TIMESTAMP NOT NULL,
        end_time TIMESTAMP NOT NULL,
        message_count INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    );
    """
    
    def __init__(self, config: MemoryConfig):
        """
        Initialize memory system.
        
        Args:
            config: Memory configuration
        """
        self.config = config
        self.storage_path = Path(config.storage_path)
        self.max_history = config.max_history
        self.similarity_threshold = config.similarity_threshold
        
        # Create data directory if needed
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self.db = self._initialize_database()
        
        # Load embedding model
        if EMBEDDINGS_AVAILABLE:
            try:
                logger.info(f"Loading embedding model: {config.embedding_model}")
                self.embedding_model = SentenceTransformer(config.embedding_model)
                logger.info("Embedding model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                self.embedding_model = None
        else:
            logger.warning("sentence-transformers not available, semantic search disabled")
            self.embedding_model = None
    
    def _initialize_database(self) -> sqlite3.Connection:
        """
        Initialize SQLite database with schema.
        
        Returns:
            Database connection
        """
        logger.info(f"Initializing database: {self.storage_path}")
        
        conn = sqlite3.connect(str(self.storage_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        
        # Execute schema
        conn.executescript(self.SCHEMA)
        conn.commit()
        
        logger.info("Database initialized successfully")
        return conn
    
    def _generate_embedding(self, text: str) -> Optional[np.ndarray]:
        """
        Generate embedding for text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector or None if unavailable
        """
        if not self.embedding_model:
            return None
        
        try:
            embedding = self.embedding_model.encode(text, convert_to_numpy=True)
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None
    
    def store_message(
        self,
        user_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Store conversation message with embedding.
        
        Args:
            user_id: User identifier
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Optional metadata dictionary
            
        Returns:
            Message ID
        """
        # Ensure user exists
        self._ensure_user_exists(user_id)
        
        # Generate embedding
        embedding = self._generate_embedding(content)
        embedding_blob = pickle.dumps(embedding) if embedding is not None else None
        
        # Store message
        cursor = self.db.cursor()
        cursor.execute(
            """
            INSERT INTO messages (user_id, role, content, embedding, metadata)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, role, content, embedding_blob, json.dumps(metadata or {}))
        )
        self.db.commit()
        
        message_id = cursor.lastrowid
        logger.debug(f"Stored message {message_id} for user {user_id}")
        
        # Update user last_active
        self._update_user_activity(user_id)
        
        return message_id
    
    def get_recent_history(
        self,
        user_id: str,
        limit: Optional[int] = None
    ) -> List[Message]:
        """
        Get recent conversation history.
        
        Args:
            user_id: User identifier
            limit: Maximum number of messages (uses max_history if None)
            
        Returns:
            List of messages in chronological order
        """
        limit = limit or self.max_history
        
        cursor = self.db.cursor()
        cursor.execute(
            """
            SELECT id, user_id, role, content, embedding, timestamp, metadata
            FROM messages
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (user_id, limit)
        )
        
        rows = cursor.fetchall()
        
        # Convert to Message objects (reverse to get chronological order)
        messages = []
        for row in reversed(rows):
            embedding = pickle.loads(row['embedding']) if row['embedding'] else None
            metadata = json.loads(row['metadata']) if row['metadata'] else {}
            
            messages.append(Message(
                id=row['id'],
                user_id=row['user_id'],
                role=row['role'],
                content=row['content'],
                timestamp=datetime.fromisoformat(row['timestamp']),
                embedding=embedding,
                metadata=metadata
            ))
        
        logger.debug(f"Retrieved {len(messages)} recent messages for user {user_id}")
        return messages
    
    def search_memories(
        self,
        user_id: str,
        query: str,
        limit: int = 5
    ) -> List[Message]:
        """
        Search memories by semantic similarity.
        
        Args:
            user_id: User identifier
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of relevant messages sorted by similarity
        """
        if not self.embedding_model:
            logger.warning("Semantic search unavailable, returning recent history")
            return self.get_recent_history(user_id, limit)
        
        # Generate query embedding
        query_embedding = self._generate_embedding(query)
        if query_embedding is None:
            return []
        
        # Get all messages with embeddings
        cursor = self.db.cursor()
        cursor.execute(
            """
            SELECT id, user_id, role, content, embedding, timestamp, metadata
            FROM messages
            WHERE user_id = ? AND embedding IS NOT NULL
            ORDER BY timestamp DESC
            """,
            (user_id,)
        )
        
        rows = cursor.fetchall()
        
        # Calculate similarities
        similarities = []
        for row in rows:
            embedding = pickle.loads(row['embedding'])
            
            # Cosine similarity
            similarity = np.dot(query_embedding, embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(embedding)
            )
            
            if similarity >= self.similarity_threshold:
                metadata = json.loads(row['metadata']) if row['metadata'] else {}
                
                message = Message(
                    id=row['id'],
                    user_id=row['user_id'],
                    role=row['role'],
                    content=row['content'],
                    timestamp=datetime.fromisoformat(row['timestamp']),
                    embedding=embedding,
                    metadata=metadata
                )
                
                similarities.append((similarity, message))
        
        # Sort by similarity and return top results
        similarities.sort(reverse=True, key=lambda x: x[0])
        results = [msg for _, msg in similarities[:limit]]
        
        logger.debug(f"Found {len(results)} relevant memories for user {user_id}")
        return results
    
    def store_context(self, user_id: str, key: str, value: str) -> None:
        """
        Store persistent user context (preferences, facts).
        
        Args:
            user_id: User identifier
            key: Context key
            value: Context value
        """
        self._ensure_user_exists(user_id)
        
        cursor = self.db.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO user_context (user_id, key, value, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (user_id, key, value)
        )
        self.db.commit()
        
        logger.debug(f"Stored context '{key}' for user {user_id}")
    
    def get_context(self, user_id: str) -> Dict[str, str]:
        """
        Get all stored context for user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary of context key-value pairs
        """
        cursor = self.db.cursor()
        cursor.execute(
            "SELECT key, value FROM user_context WHERE user_id = ?",
            (user_id,)
        )
        
        rows = cursor.fetchall()
        context = {row['key']: row['value'] for row in rows}
        
        logger.debug(f"Retrieved {len(context)} context items for user {user_id}")
        return context
    
    def delete_user_data(self, user_id: str) -> None:
        """
        Delete all data for user (privacy compliance).
        
        Args:
            user_id: User identifier
        """
        cursor = self.db.cursor()
        
        # Delete from all tables
        cursor.execute("DELETE FROM messages WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM user_context WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM conversation_summaries WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        
        self.db.commit()
        
        logger.info(f"Deleted all data for user {user_id}")
    
    def _ensure_user_exists(self, user_id: str) -> None:
        """Ensure user record exists."""
        cursor = self.db.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO users (user_id) VALUES (?)",
            (user_id,)
        )
        self.db.commit()
    
    def _update_user_activity(self, user_id: str) -> None:
        """Update user's last_active timestamp."""
        cursor = self.db.cursor()
        cursor.execute(
            "UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE user_id = ?",
            (user_id,)
        )
        self.db.commit()
    
    def close(self) -> None:
        """Close database connection."""
        if self.db:
            self.db.close()
            logger.info("Database connection closed")
