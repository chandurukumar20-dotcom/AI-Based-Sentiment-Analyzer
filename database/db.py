import json
import logging
import uuid
from datetime import datetime
from bson import ObjectId
from pymongo import MongoClient, DESCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from config import Config

logger = logging.getLogger(__name__)


class DatabaseService:
    """
    Robust MongoDB Database Service with automatic fallback to JSON storage
    if the MongoDB daemon is offline or unreachable.
    """

    def __init__(self, uri=None, db_name=None, timeout_ms=None):
        self.uri = uri or Config.MONGO_URI
        self.db_name = db_name or Config.MONGO_DB_NAME
        self.timeout_ms = timeout_ms or Config.MONGO_TIMEOUT_MS
        self.client = None
        self.db = None
        self.collection = None
        self.is_connected = False
        self.storage_mode = "unknown"
        self._init_connection()

    def _init_connection(self):
        """Attempts to connect to MongoDB, falls back to local JSON if unavailable."""
        try:
            self.client = MongoClient(
                self.uri,
                serverSelectionTimeoutMS=self.timeout_ms,
                connectTimeoutMS=self.timeout_ms
            )
            # Trigger a quick ping command to verify connectivity
            self.client.admin.command('ping')
            self.db = self.client[self.db_name]
            self.collection = self.db["sentiment_history"]
            # Create an index on timestamp descending for fast queries
            self.collection.create_index([("created_at", DESCENDING)])
            self.is_connected = True
            self.storage_mode = "mongodb"
            logger.info("Successfully connected to MongoDB: %s -> %s", self.uri, self.db_name)
        except (ConnectionFailure, ServerSelectionTimeoutError, Exception) as exc:
            logger.warning("MongoDB not reachable (%s). Falling back to Local Storage mode.", exc)
            self.is_connected = False
            self.storage_mode = "local"
            self._ensure_local_db()

    def _ensure_local_db(self):
        """Ensures the local fallback JSON file exists and is valid."""
        if not Config.LOCAL_DB_FILE.exists():
            with open(Config.LOCAL_DB_FILE, "w", encoding="utf-8") as f:
                json.dump([], f)

    def _read_local_db(self):
        """Reads records from local JSON storage."""
        self._ensure_local_db()
        try:
            with open(Config.LOCAL_DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _write_local_db(self, records):
        """Writes records to local JSON storage."""
        self._ensure_local_db()
        with open(Config.LOCAL_DB_FILE, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, default=str)

    def get_status(self):
        """Returns the current database connection state and metadata."""
        total_count = self.get_count()
        return {
            "connected": self.is_connected,
            "storage_mode": self.storage_mode,
            "uri": self.uri,
            "db_name": self.db_name,
            "total_records": total_count,
            "message": "Connected to MongoDB" if self.is_connected else "Operating in Local JSON Storage Fallback Mode (MongoDB offline)"
        }

    def insert_record(self, text, sentiment, confidence, scores=None, source="single", filename=None):
        """Inserts a single sentiment analysis record."""
        now = datetime.utcnow()
        record = {
            "text": text,
            "sentiment": sentiment.capitalize(),
            "confidence": round(float(confidence), 2),
            "scores": scores or {},
            "source": source,
            "filename": filename,
            "created_at": now.strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp": now.timestamp()
        }

        if self.is_connected and self.collection is not None:
            try:
                res = self.collection.insert_one(record)
                record["_id"] = str(res.inserted_id)
                return record
            except Exception as e:
                logger.error("Error inserting to MongoDB: %s. Falling back to local.", e)
                self.is_connected = False
                self.storage_mode = "local"

        # Local storage fallback
        records = self._read_local_db()
        record["_id"] = str(uuid.uuid4())
        records.insert(0, record)
        self._write_local_db(records)
        return record

    def insert_many_records(self, record_list):
        """Inserts multiple sentiment analysis records in batch."""
        if not record_list:
            return []

        now = datetime.utcnow()
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")
        ts = now.timestamp()

        prepared = []
        for r in record_list:
            rec = {
                "text": r.get("text", ""),
                "sentiment": str(r.get("sentiment", "Neutral")).capitalize(),
                "confidence": round(float(r.get("confidence", 0.0)), 2),
                "scores": r.get("scores", {}),
                "source": r.get("source", "batch"),
                "filename": r.get("filename", ""),
                "created_at": r.get("created_at", now_str),
                "timestamp": r.get("timestamp", ts)
            }
            prepared.append(rec)

        if self.is_connected and self.collection is not None:
            try:
                res = self.collection.insert_many(prepared)
                for idx, inserted_id in enumerate(res.inserted_ids):
                    prepared[idx]["_id"] = str(inserted_id)
                return prepared
            except Exception as e:
                logger.error("Error inserting many to MongoDB: %s. Falling back to local.", e)
                self.is_connected = False
                self.storage_mode = "local"

        # Local storage fallback
        records = self._read_local_db()
        for rec in prepared:
            rec["_id"] = str(uuid.uuid4())
        records = prepared + records
        self._write_local_db(records)
        return prepared

    def get_all_records(self, limit=500, sentiment_filter=None, search_query=None):
        """Retrieves records with optional filtering and search."""
        if self.is_connected and self.collection is not None:
            try:
                query = {}
                if sentiment_filter and sentiment_filter.lower() != "all":
                    query["sentiment"] = sentiment_filter.capitalize()
                if search_query:
                    query["text"] = {"$regex": search_query, "$options": "i"}

                cursor = self.collection.find(query).sort("created_at", DESCENDING).limit(limit)
                results = []
                for doc in cursor:
                    doc["_id"] = str(doc["_id"])
                    results.append(doc)
                return results
            except Exception as e:
                logger.error("Error querying MongoDB: %s. Reading from local fallback.", e)
                self.is_connected = False
                self.storage_mode = "local"

        # Local fallback
        records = self._read_local_db()
        filtered = []
        q = (search_query or "").lower().strip()
        sf = (sentiment_filter or "").capitalize() if sentiment_filter and sentiment_filter.lower() != "all" else None

        for rec in records:
            if sf and rec.get("sentiment") != sf:
                continue
            if q and q not in rec.get("text", "").lower():
                continue
            filtered.append(rec)

        # Sort descending by created_at / timestamp
        filtered.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        return filtered[:limit]

    def get_count(self):
        """Returns total record count."""
        if self.is_connected and self.collection is not None:
            try:
                return self.collection.count_documents({})
            except Exception:
                pass
        return len(self._read_local_db())

    def get_statistics(self):
        """
        Calculates aggregate metrics for the dashboard:
        - Total reviews
        - Positive, Negative, Neutral counts
        - Percentage distribution
        - Average confidence score
        - Recent history records
        - Sentiment trend over time
        """
        records = self.get_all_records(limit=2000)
        total = len(records)
        pos_count = sum(1 for r in records if r.get("sentiment") == "Positive")
        neg_count = sum(1 for r in records if r.get("sentiment") == "Negative")
        neu_count = sum(1 for r in records if r.get("sentiment") == "Neutral")

        pos_pct = round((pos_count / total * 100), 1) if total > 0 else 0.0
        neg_pct = round((neg_count / total * 100), 1) if total > 0 else 0.0
        neu_pct = round((neu_count / total * 100), 1) if total > 0 else 0.0

        avg_conf = (
            round(sum(float(r.get("confidence", 0)) for r in records) / total, 1)
            if total > 0 else 0.0
        )

        # Build timeline breakdown (grouped by date)
        timeline = {}
        for r in reversed(records[:100]):  # up to 100 recent
            date_str = r.get("created_at", "").split(" ")[0] if "created_at" in r else "Recent"
            if not date_str:
                date_str = "Recent"
            if date_str not in timeline:
                timeline[date_str] = {"positive": 0, "negative": 0, "neutral": 0}
            s = r.get("sentiment", "Neutral").lower()
            if s in timeline[date_str]:
                timeline[date_str][s] += 1

        return {
            "total": total,
            "positive": pos_count,
            "negative": neg_count,
            "neutral": neu_count,
            "positive_pct": pos_pct,
            "negative_pct": neg_pct,
            "neutral_pct": neu_pct,
            "avg_confidence": avg_conf,
            "recent": records[:6],
            "timeline": timeline,
            "storage_status": self.get_status()
        }

    def delete_record(self, record_id):
        """Deletes a record by its _id."""
        deleted = False
        if self.is_connected and self.collection is not None:
            try:
                try:
                    obj_id = ObjectId(record_id)
                    res = self.collection.delete_one({"_id": obj_id})
                except Exception:
                    res = self.collection.delete_one({"_id": record_id})
                if res.deleted_count > 0:
                    return True
            except Exception as e:
                logger.error("Error deleting from MongoDB: %s", e)

        # Local fallback delete
        records = self._read_local_db()
        new_records = [r for r in records if str(r.get("_id")) != str(record_id)]
        if len(new_records) < len(records):
            self._write_local_db(new_records)
            deleted = True
        return deleted

    def clear_all(self):
        """Clears all records."""
        if self.is_connected and self.collection is not None:
            try:
                self.collection.delete_many({})
            except Exception as e:
                logger.error("Error clearing MongoDB: %s", e)
        self._write_local_db([])
        return True


# Global database singleton
_db_instance = None


def get_db():
    """Returns singleton instance of DatabaseService."""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseService()
    return _db_instance
