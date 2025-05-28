# database.py
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from typing import List, Optional, Dict, Any
import logging

from config import settings

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        
    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(settings.MONGODB_URL)
            self.db = self.client[settings.DATABASE_NAME]
            
            # Test the connection
            await self.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")
            
            # Create indexes
            await self._create_indexes()
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("Database connection closed")
    
    async def ping(self):
        """Ping database to check connection"""
        if self.client:
            await self.client.admin.command('ping')
        else:
            raise Exception("Database not connected")
    
    async def _create_indexes(self):
        """Create database indexes for better performance"""
        try:
            # Index on token field for fast lookups
            await self.db.tokens.create_index("token", unique=True)
            
            # Index on usage records for efficient queries
            await self.db.usages.create_index([("token", 1), ("timestamp", -1)])
            await self.db.usages.create_index("timestamp")
            
            logger.info("Database indexes created successfully")
        except Exception as e:
            logger.warning(f"Error creating indexes: {e}")
    
    # Token management methods
    async def create_token(self, token: str, is_admin: bool = False) -> Dict[str, Any]:
        """Create a new token"""
        token_doc = {
            "token": token,
            "isAdmin": is_admin,
            "createdAt": datetime.utcnow(),
            "lastUsed": None
        }
        print(token_doc)
        result = await self.db.tokens.insert_one(token_doc)
        print("result =", result)
        token_doc["_id"] = result.inserted_id
        
        logger.info(f"Created {'admin' if is_admin else 'regular'} token")
        return token_doc
    
    async def get_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Get token document by token string"""
        return await self.db.tokens.find_one({"token": token})
    
    async def get_admin_token(self) -> Optional[Dict[str, Any]]:
        """Get any admin token (for initialization)"""
        return await self.db.tokens.find_one({"isAdmin": True})
    
    async def list_tokens(self) -> List[Dict[str, Any]]:
        """List all tokens (admin only)"""
        cursor = self.db.tokens.find({}, {"_id": 0})
        tokens = await cursor.to_list(length=None)
        
        # Add usage statistics
        for token_data in tokens:
            usage_count = await self.db.usages.count_documents({"token": token_data["token"]})
            token_data["usageCount"] = usage_count
        
        return tokens
    
    async def delete_token(self, token: str) -> bool:
        """Delete a token"""
        result = await self.db.tokens.delete_one({"token": token})
        
        if result.deleted_count > 0:
            # Also delete usage records for this token
            await self.db.usages.delete_many({"token": token})
            logger.info(f"Deleted token and its usage records")
            return True
        
        return False
    
    async def update_token_last_used(self, token: str):
        """Update the last used timestamp for a token"""
        await self.db.tokens.update_one(
            {"token": token},
            {"$set": {"lastUsed": datetime.utcnow()}}
        )
    
    # Usage tracking methods
    async def record_usage(self, token: str, endpoint: str, metadata: Optional[Dict] = None):
        """Record API usage"""
        usage_doc = {
            "token": token,
            "endpoint": endpoint,
            "timestamp": datetime.utcnow(),
            "metadata": metadata or {}
        }
        
        await self.db.usages.insert_one(usage_doc)
        
        # Update token's last used timestamp
        await self.update_token_last_used(token)
    
    async def get_usage_stats(self, token: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get usage statistics for a token"""
        cursor = self.db.usages.find(
            {"token": token},
            {"_id": 0}
        ).sort("timestamp", -1).limit(limit)
        
        return await cursor.to_list(length=limit)
    
    async def get_usage_summary(self, token: str) -> Dict[str, Any]:
        """Get usage summary for a token"""
        pipeline = [
            {"$match": {"token": token}},
            {"$group": {
                "_id": "$endpoint",
                "count": {"$sum": 1},
                "lastUsed": {"$max": "$timestamp"}
            }},
            {"$sort": {"count": -1}}
        ]
        
        cursor = self.db.usages.aggregate(pipeline)
        summary = await cursor.to_list(length=None)
        
        total_usage = await self.db.usages.count_documents({"token": token})
        
        return {
            "totalUsage": total_usage,
            "endpointBreakdown": summary
        }
    
    # Cleanup methods
    async def cleanup_old_usage_records(self, days: int = 30):
        """Clean up usage records older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        result = await self.db.usages.delete_many({"timestamp": {"$lt": cutoff_date}})
        
        logger.info(f"Cleaned up {result.deleted_count} old usage records")
        return result.deleted_count