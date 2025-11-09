# app/core/memory_store.py
from supabase import create_client, Client
import json
from datetime import datetime
from typing import List, Dict, Optional
import logging

from app.config import settings
from app.core.encryption import DataEncryptor

logger = logging.getLogger(__name__)
encryptor = DataEncryptor()

class SupabaseMemoryStore:
    def __init__(self):
        self.client: Client = create_client(settings.supabase_url, settings.supabase_key)
        self._ensure_connection()
    
    def _ensure_connection(self):
        """Test Supabase connection"""
        try:
            # Simple query to test connection
            self.client.table('memories').select('id', count='exact').limit(1).execute()
            logger.info("Supabase connection successful")
        except Exception as e:
            logger.error(f"Supabase connection failed: {e}")
            raise
    
    def add_memory(self, input_text: str, output_text: str, context: str = None, 
                   category: str = "general", embedding: list = None) -> int:
        """Add a memory to Supabase"""
        try:
            # Encrypt sensitive data
            encrypted_input = encryptor.encrypt(input_text)
            encrypted_output = encryptor.encrypt(output_text)
            encrypted_context = encryptor.encrypt(context) if context else None
            
            memory_data = {
                "input_text": encrypted_input.decode('utf-8'),
                "output_text": encrypted_output.decode('utf-8'),
                "context": encrypted_context.decode('utf-8') if encrypted_context else None,
                "category": category,
                "embedding": json.dumps(embedding) if embedding else None,
                "confidence": 1.0,
                "is_active": True
            }
            
            response = self.client.table('memories').insert(memory_data).execute()
            
            if response.data:
                memory_id = response.data[0]['id']
                logger.info(f"Memory added with ID: {memory_id}")
                return memory_id
            else:
                raise Exception("No data returned from Supabase")
                
        except Exception as e:
            logger.error(f"Error adding memory to Supabase: {e}")
            raise
    
    def get_active_memories(self, category: str = None, limit: int = 1000) -> List[Dict]:
        """Get active memories from Supabase"""
        try:
            query = self.client.table('memories').select('*').eq('is_active', True)
            
            if category:
                query = query.eq('category', category)
            
            response = query.order('created_at', desc=True).limit(limit).execute()
            
            # Decrypt the data
            decrypted_memories = []
            for memory in response.data:
                try:
                    decrypted_memories.append({
                        'id': memory['id'],
                        'input_text': encryptor.decrypt(memory['input_text'].encode('utf-8')),
                        'output_text': encryptor.decrypt(memory['output_text'].encode('utf-8')),
                        'context': encryptor.decrypt(memory['context'].encode('utf-8')) if memory['context'] else None,
                        'category': memory['category'],
                        'embedding': json.loads(memory['embedding']) if memory['embedding'] else None,
                        'confidence': memory['confidence'],
                        'created_at': datetime.fromisoformat(memory['created_at'].replace('Z', '+00:00')),
                        'is_active': memory['is_active']
                    })
                except Exception as e:
                    logger.error(f"Error decrypting memory {memory['id']}: {e}")
                    continue
            
            return decrypted_memories
            
        except Exception as e:
            logger.error(f"Error fetching memories from Supabase: {e}")
            return []
    
    def delete_memory(self, memory_id: int) -> bool:
        """Soft delete a memory"""
        try:
            response = self.client.table('memories').update({
                'is_active': False
            }).eq('id', memory_id).execute()
            
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"Error deleting memory {memory_id}: {e}")
            return False
    
    def add_rule(self, pattern: str, action: str, priority: int = 1) -> int:
        """Add a rule to Supabase"""
        try:
            encrypted_pattern = encryptor.encrypt(pattern)
            encrypted_action = encryptor.encrypt(action)
            
            rule_data = {
                "pattern": encrypted_pattern.decode('utf-8'),
                "action": encrypted_action.decode('utf-8'),
                "priority": priority,
                "is_active": True
            }
            
            response = self.client.table('rules').insert(rule_data).execute()
            
            if response.data:
                rule_id = response.data[0]['id']
                logger.info(f"Rule added with ID: {rule_id}")
                return rule_id
            else:
                raise Exception("No data returned from Supabase")
                
        except Exception as e:
            logger.error(f"Error adding rule to Supabase: {e}")
            raise
    
    def get_active_rules(self) -> List[Dict]:
        """Get active rules from Supabase"""
        try:
            response = self.client.table('rules').select('*').eq('is_active', True).order('priority', desc=True).execute()
            
            decrypted_rules = []
            for rule in response.data:
                try:
                    decrypted_rules.append({
                        'id': rule['id'],
                        'pattern': encryptor.decrypt(rule['pattern'].encode('utf-8')),
                        'action': encryptor.decrypt(rule['action'].encode('utf-8')),
                        'priority': rule['priority'],
                        'is_active': rule['is_active'],
                        'created_at': datetime.fromisoformat(rule['created_at'].replace('Z', '+00:00'))
                    })
                except Exception as e:
                    logger.error(f"Error decrypting rule {rule['id']}: {e}")
                    continue
            
            return decrypted_rules
            
        except Exception as e:
            logger.error(f"Error fetching rules from Supabase: {e}")
            return []
    
    def get_stats(self) -> Dict:
        """Get memory and rule counts"""
        try:
            # Get memory count
            mem_response = self.client.table('memories').select('id', count='exact').eq('is_active', True).execute()
            memory_count = mem_response.count
            
            # Get rule count
            rule_response = self.client.table('rules').select('id', count='exact').eq('is_active', True).execute()
            rule_count = rule_response.count
            
            return {
                'memory_count': memory_count or 0,
                'rule_count': rule_count or 0
            }
        except Exception as e:
            logger.error(f"Error getting stats from Supabase: {e}")
            return {'memory_count': 0, 'rule_count': 0}