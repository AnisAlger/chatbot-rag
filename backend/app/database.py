import logging
import time
from typing import Any, Dict, List, Optional
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from app.config import settings

logger = logging.getLogger(__name__)


class InMemoryCollection:
    """
    Lightweight in-memory MongoDB-compatible collection fallback.
    Used during offline development or unit tests when live MongoDB is unreachable.
    """
    def __init__(self, name: str):
        self.name = name
        self.docs: List[Dict[str, Any]] = []

    def insert_one(self, document: Dict[str, Any]):
        doc = dict(document)
        if "_id" not in doc:
            import uuid
            doc["_id"] = str(uuid.uuid4())
        self.docs.append(doc)
        
        class InsertResult:
            inserted_id = doc["_id"]
        return InsertResult()

    def find_one(self, filter: Dict[str, Any], projection: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        for doc in self.docs:
            if self._matches(doc, filter):
                res = dict(doc)
                if projection and "_id" in projection and projection["_id"] == 0:
                    res.pop("_id", None)
                return res
        return None

    def find(self, filter: Optional[Dict[str, Any]] = None, projection: Optional[Dict[str, Any]] = None):
        filter = filter or {}
        matches = [dict(doc) for doc in self.docs if self._matches(doc, filter)]
        
        class Cursor:
            def __init__(self, data):
                self.data = data
            def sort(self, key, direction=1):
                reverse = direction < 0
                self.data.sort(key=lambda x: x.get(key, ""), reverse=reverse)
                return self
            def skip(self, n):
                self.data = self.data[n:]
                return self
            def limit(self, n):
                self.data = self.data[:n]
                return self
            def __iter__(self):
                return iter(self.data)
            def list(self):
                return self.data

        return Cursor(matches)

    def count_documents(self, filter: Optional[Dict[str, Any]] = None) -> int:
        filter = filter or {}
        return len([d for d in self.docs if self._matches(d, filter)])

    def update_one(self, filter: Dict[str, Any], update: Dict[str, Any]):
        for doc in self.docs:
            if self._matches(doc, filter):
                if "$set" in update:
                    for k, v in update["$set"].items():
                        doc[k] = v
                class UpdateResult:
                    matched_count = 1
                    modified_count = 1
                return UpdateResult()
        class NoUpdateResult:
            matched_count = 0
            modified_count = 0
        return NoUpdateResult()

    def delete_one(self, filter: Dict[str, Any]):
        for i, doc in enumerate(self.docs):
            if self._matches(doc, filter):
                del self.docs[i]
                class DelResult:
                    deleted_count = 1
                return DelResult()
        class NoDelResult:
            deleted_count = 0
        return NoDelResult()

    def delete_many(self, filter: Dict[str, Any]):
        initial_len = len(self.docs)
        self.docs = [doc for doc in self.docs if not self._matches(doc, filter)]
        count = initial_len - len(self.docs)
        class DelManyResult:
            deleted_count = count
        return DelManyResult()

    def _matches(self, doc: Dict[str, Any], filter_dict: Dict[str, Any]) -> bool:
        for k, v in filter_dict.items():
            if isinstance(v, dict):
                if "$in" in v:
                    if doc.get(k) not in v["$in"]:
                        return False
                elif "$ne" in v:
                    if doc.get(k) == v["$ne"]:
                        return False
            elif doc.get(k) != v:
                return False
        return True


class InMemoryDatabase:
    def __init__(self, name: str):
        self.name = name
        self.collections: Dict[str, InMemoryCollection] = {}

    def __getitem__(self, item: str) -> InMemoryCollection:
        if item not in self.collections:
            self.collections[item] = InMemoryCollection(item)
        return self.collections[item]


class DatabaseManager:
    """
    Manages MongoDB client lifecycle with resilient fallback for development.
    """
    def __init__(self):
        self._client: Optional[MongoClient] = None
        self._db = None
        self._is_fallback: bool = False

    def connect(self):
        try:
            logger.info("Connecting to MongoDB at %s...", settings.MONGODB_URI.split("@")[-1])
            self._client = MongoClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=settings.MONGODB_TIMEOUT_MS,
                connectTimeoutMS=settings.MONGODB_TIMEOUT_MS
            )
            # Test ping
            self._client.admin.command('ping')
            self._db = self._client[settings.MONGODB_DATABASE]
            self._is_fallback = False
            logger.info("MongoDB connection established successfully.")
            self._ensure_indexes()
        except Exception as e:
            logger.warning("Could not connect to MongoDB (%s). Using in-memory database fallback for development.", e)
            self._is_fallback = True
            self._db = InMemoryDatabase(settings.MONGODB_DATABASE)

    def _ensure_indexes(self):
        if not self._is_fallback and self._db is not None:
            try:
                self._db.users.create_index("email", unique=True)
                self._db.documents.create_index([("owner_id", 1), ("uploaded_at", -1)])
                self._db.conversations.create_index([("owner_id", 1), ("updated_at", -1)])
                self._db.messages.create_index([("conversation_id", 1), ("created_at", 1)])
            except Exception as e:
                logger.warning("Could not create MongoDB indexes: %s", e)

    def close(self):
        if self._client:
            self._client.close()
            logger.info("MongoDB connection closed.")

    @property
    def db(self):
        if self._db is None:
            self.connect()
        return self._db

    @property
    def is_fallback(self) -> bool:
        return self._is_fallback

    def check_health(self) -> Dict[str, Any]:
        if self._is_fallback:
            return {"status": "degraded", "mode": "in_memory_fallback", "connected": False}
        try:
            if self._client:
                self._client.admin.command('ping')
                return {"status": "healthy", "mode": "mongodb", "connected": True}
        except Exception as e:
            return {"status": "unhealthy", "mode": "mongodb", "connected": False, "error": str(e)}
        return {"status": "unknown", "mode": "mongodb", "connected": False}

    # Collection helpers
    @property
    def users(self) -> Any:
        return self.db["users"]

    @property
    def documents(self) -> Any:
        return self.db["documents"]

    @property
    def conversations(self) -> Any:
        return self.db["conversations"]

    @property
    def messages(self) -> Any:
        return self.db["messages"]

    @property
    def chunks(self) -> Any:
        return self.db["chunks"]


db_manager = DatabaseManager()
