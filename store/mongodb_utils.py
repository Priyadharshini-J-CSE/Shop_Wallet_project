# store/mongodb_utils.py
"""
MongoDB utilities for ShopWallet application
Handles direct MongoDB operations for transactions and wallet data
"""

from pymongo import MongoClient
from django.conf import settings
from datetime import datetime
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class MongoDBConnection:
    """MongoDB connection manager"""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.connect()
    
    def connect(self):
        """Establish connection to MongoDB"""
        try:
            mongodb_settings = getattr(settings, 'MONGODB_SETTINGS', {})
            host = mongodb_settings.get('host', 'mongodb://localhost:27017/')
            database_name = mongodb_settings.get('database', 'shopwallet_db')
            
            self.client = MongoClient(host, serverSelectionTimeoutMS=5000)
            # Test connection
            self.client.server_info()
            self.db = self.client[database_name]
            logger.info(f"Connected to MongoDB: {database_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False
    
    def get_collection(self, collection_name):
        """Get a MongoDB collection"""
        if self.db is not None:
            return self.db[collection_name]
        return None
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()

# Global MongoDB connection instance
mongo_connection = MongoDBConnection()

class MongoWallet:
    """MongoDB-based Wallet operations"""
    
    @staticmethod
    def get_or_create_wallet(user_id, username):
        """Get or create wallet for user"""
        try:
            wallets = mongo_connection.get_collection('wallets')
            if wallets is None:
                return None
            
            wallet = wallets.find_one({'user_id': user_id})
            if not wallet:
                # Create new wallet
                wallet_data = {
                    'user_id': user_id,
                    'username': username,
                    'balance': float(Decimal('0.00')),  # Convert Decimal to float for MongoDB
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                }
                wallets.insert_one(wallet_data)
                wallet = wallet_data
            
            return wallet
        except Exception as e:
            logger.error(f"Error getting/creating wallet: {e}")
            return None
    
    @staticmethod
    def update_balance(user_id, new_balance):
        """Update wallet balance"""
        try:
            wallets = mongo_connection.get_collection('wallets')
            if wallets is None:
                return False
            
            result = wallets.update_one(
                {'user_id': user_id},
                {
                    '$set': {
                        'balance': float(new_balance),
                        'updated_at': datetime.now()
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating wallet balance: {e}")
            return False
    
    @staticmethod
    def get_balance(user_id):
        """Get wallet balance"""
        try:
            wallets = mongo_connection.get_collection('wallets')
            if wallets is None:
                return Decimal('0.00')
            
            wallet = wallets.find_one({'user_id': user_id})
            if wallet:
                return Decimal(str(wallet.get('balance', 0)))
            return Decimal('0.00')
        except Exception as e:
            logger.error(f"Error getting wallet balance: {e}")
            return Decimal('0.00')

class MongoTransaction:
    """MongoDB-based Transaction operations"""
    
    @staticmethod
    def create_transaction(user_id, username, transaction_type, amount, description, balance_after):
        """Create a new transaction record"""
        try:
            transactions = mongo_connection.get_collection('transactions')
            if transactions is None:
                return None
            
            transaction_data = {
                'user_id': user_id,
                'username': username,
                'transaction_type': transaction_type,
                'amount': float(amount),
                'description': description,
                'balance_after': float(balance_after),
                'timestamp': datetime.now(),
                'created_at': datetime.now()
            }
            
            result = transactions.insert_one(transaction_data)
            transaction_data['_id'] = result.inserted_id
            return transaction_data
        except Exception as e:
            logger.error(f"Error creating transaction: {e}")
            return None
    
    @staticmethod
    def get_user_transactions(user_id, limit=50):
        """Get user's transaction history"""
        try:
            transactions = mongo_connection.get_collection('transactions')
            if transactions is None:
                return []
            
            cursor = transactions.find(
                {'user_id': user_id}
            ).sort('timestamp', -1).limit(limit)
            
            return list(cursor)
        except Exception as e:
            logger.error(f"Error getting user transactions: {e}")
            return []

def test_mongodb_connection():
    """Test MongoDB connection and basic operations"""
    try:
        # Test connection
        if not mongo_connection.connect():
            return False, "Failed to connect to MongoDB"
        
        # Test collections
        wallets = mongo_connection.get_collection('wallets')
        transactions = mongo_connection.get_collection('transactions')
        
        if wallets is None or transactions is None:
            return False, "Failed to access MongoDB collections"
        
        return True, "MongoDB connection and operations successful"
    
    except Exception as e:
        return False, f"MongoDB test failed: {e}"
