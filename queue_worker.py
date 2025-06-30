import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import time

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class QueueTask:
    """Queue task data structure"""
    id: str
    task_type: str
    data: Dict
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

class InMemoryQueue:
    """In-memory queue implementation (for systems without Redis)"""
    
    def __init__(self):
        self.tasks: Dict[str, QueueTask] = {}
        self.processing_tasks: Dict[str, QueueTask] = {}
        self.completed_tasks: Dict[str, QueueTask] = {}
        self.failed_tasks: Dict[str, QueueTask] = {}
        self._lock = threading.Lock()
    
    def enqueue(self, task: QueueTask) -> bool:
        """Add task to queue"""
        with self._lock:
            self.tasks[task.id] = task
            logger.info(f"Task {task.id} added to queue")
            return True
    
    def dequeue(self) -> Optional[QueueTask]:
        """Get next task from queue"""
        with self._lock:
            if not self.tasks:
                return None
            
            # Get oldest task
            task_id = min(self.tasks.keys(), key=lambda x: self.tasks[x].created_at)
            task = self.tasks.pop(task_id)
            
            # Move to processing
            task.status = TaskStatus.PROCESSING
            task.started_at = datetime.utcnow()
            self.processing_tasks[task.id] = task
            
            logger.info(f"Task {task.id} dequeued for processing")
            return task
    
    def complete_task(self, task_id: str, result: Optional[str] = None) -> bool:
        """Mark task as completed"""
        with self._lock:
            if task_id not in self.processing_tasks:
                return False
            
            task = self.processing_tasks.pop(task_id)
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            self.completed_tasks[task_id] = task
            
            logger.info(f"Task {task_id} completed successfully")
            return True
    
    def fail_task(self, task_id: str, error_message: str) -> bool:
        """Mark task as failed"""
        with self._lock:
            if task_id not in self.processing_tasks:
                return False
            
            task = self.processing_tasks.pop(task_id)
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.utcnow()
            task.error_message = error_message
            task.retry_count += 1
            
            # Retry if under max retries
            if task.retry_count < task.max_retries:
                task.status = TaskStatus.QUEUED
                task.started_at = None
                task.completed_at = None
                self.tasks[task_id] = task
                logger.info(f"Task {task_id} queued for retry ({task.retry_count}/{task.max_retries})")
            else:
                self.failed_tasks[task_id] = task
                logger.error(f"Task {task_id} failed permanently: {error_message}")
            
            return True
    
    def get_task_status(self, task_id: str) -> Optional[QueueTask]:
        """Get task status"""
        with self._lock:
            # Check all queues
            for queue in [self.tasks, self.processing_tasks, self.completed_tasks, self.failed_tasks]:
                if task_id in queue:
                    return queue[task_id]
            return None
    
    def get_queue_stats(self) -> Dict:
        """Get queue statistics"""
        with self._lock:
            return {
                "queued": len(self.tasks),
                "processing": len(self.processing_tasks),
                "completed": len(self.completed_tasks),
                "failed": len(self.failed_tasks),
                "total": len(self.tasks) + len(self.processing_tasks) + len(self.completed_tasks) + len(self.failed_tasks)
            }

class RedisQueue:
    """Redis-based queue implementation (optional)"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        try:
            import redis
            self.redis_client = redis.from_url(redis_url)
            self.redis_available = True
            logger.info("Redis queue initialized successfully")
        except ImportError:
            logger.warning("Redis not available, falling back to in-memory queue")
            self.redis_available = False
        except Exception as e:
            logger.error(f"Redis connection failed: {str(e)}")
            self.redis_available = False
    
    def enqueue(self, task: QueueTask) -> bool:
        """Add task to Redis queue"""
        if not self.redis_available:
            return False
        
        try:
            task_data = {
                "id": task.id,
                "task_type": task.task_type,
                "data": task.data,
                "status": task.status.value,
                "created_at": task.created_at.isoformat(),
                "retry_count": task.retry_count,
                "max_retries": task.max_retries
            }
            
            # Add to queue
            self.redis_client.lpush("blood_analysis_queue", json.dumps(task_data))
            
            # Store task details
            self.redis_client.hset(f"task:{task.id}", mapping=task_data)
            
            logger.info(f"Task {task.id} added to Redis queue")
            return True
            
        except Exception as e:
            logger.error(f"Error adding task to Redis queue: {str(e)}")
            return False
    
    def dequeue(self) -> Optional[QueueTask]:
        """Get next task from Redis queue"""
        if not self.redis_available:
            return None
        
        try:
            # Get task from queue
            task_data = self.redis_client.brpop("blood_analysis_queue", timeout=1)
            if not task_data:
                return None
            
            task_json = json.loads(task_data[1])
            
            # Create QueueTask object
            task = QueueTask(
                id=task_json["id"],
                task_type=task_json["task_type"],
                data=task_json["data"],
                status=TaskStatus.PROCESSING,
                created_at=datetime.fromisoformat(task_json["created_at"]),
                started_at=datetime.utcnow(),
                retry_count=task_json["retry_count"],
                max_retries=task_json["max_retries"]
            )
            
            # Update task status in Redis
            self.redis_client.hset(f"task:{task.id}", "status", TaskStatus.PROCESSING.value)
            self.redis_client.hset(f"task:{task.id}", "started_at", task.started_at.isoformat())
            
            logger.info(f"Task {task.id} dequeued from Redis")
            return task
            
        except Exception as e:
            logger.error(f"Error dequeuing task from Redis: {str(e)}")
            return None

class QueueManager:
    """Queue manager that handles both in-memory and Redis queues"""
    
    def __init__(self, redis_url: Optional[str] = None):
        self.in_memory_queue = InMemoryQueue()
        
        if redis_url:
            self.redis_queue = RedisQueue(redis_url)
            self.use_redis = self.redis_queue.redis_available
        else:
            self.redis_queue = None
            self.use_redis = False
        
        if self.use_redis:
            logger.info("QueueManager initialized with Redis backend")
        else:
            logger.info("QueueManager initialized with in-memory backend")
    
    def enqueue_task(self, task_id: str, task_type: str, data: Dict) -> bool:
        """Add task to appropriate queue"""
        task = QueueTask(
            id=task_id,
            task_type=task_type,
            data=data,
            status=TaskStatus.QUEUED,
            created_at=datetime.utcnow()
        )
        
        if self.use_redis:
            return self.redis_queue.enqueue(task)
        else:
            return self.in_memory_queue.enqueue(task)
    
    def get_next_task(self) -> Optional[QueueTask]:
        """Get next task for processing"""
        if self.use_redis:
            return self.redis_queue.dequeue()
        else:
            return self.in_memory_queue.dequeue()
    
    def complete_task(self, task_id: str, result: Optional[str] = None) -> bool:
        """Mark task as completed"""
        if self.use_redis:
            try:
                self.redis_queue.redis_client.hset(f"task:{task_id}", "status", TaskStatus.COMPLETED.value)
                self.redis_queue.redis_client.hset(f"task:{task_id}", "completed_at", datetime.utcnow().isoformat())
                if result:
                    self.redis_queue.redis_client.hset(f"task:{task_id}", "result", result)
                return True
            except Exception as e:
                logger.error(f"Error completing Redis task: {str(e)}")
                return False
        else:
            return self.in_memory_queue.complete_task(task_id, result)
    
    def fail_task(self, task_id: str, error_message: str) -> bool:
        """Mark task as failed"""
        if self.use_redis:
            try:
                self.redis_queue.redis_client.hset(f"task:{task_id}", "status", TaskStatus.FAILED.value)
                self.redis_queue.redis_client.hset(f"task:{task_id}", "completed_at", datetime.utcnow().isoformat())
                self.redis_queue.redis_client.hset(f"task:{task_id}", "error_message", error_message)
                return True
            except Exception as e:
                logger.error(f"Error failing Redis task: {str(e)}")
                return False
        else:
            return self.in_memory_queue.fail_task(task_id, error_message)
    
    def get_task_status(self, task_id: str) -> Optional[QueueTask]:
        """Get task status"""
        if self.use_redis:
            try:
                task_data = self.redis_queue.redis_client.hgetall(f"task:{task_id}")
                if not task_data:
                    return None
                
                return QueueTask(
                    id=task_data[b"id"].decode(),
                    task_type=task_data[b"task_type"].decode(),
                    data=json.loads(task_data[b"data"].decode()),
                    status=TaskStatus(task_data[b"status"].decode()),
                    created_at=datetime.fromisoformat(task_data[b"created_at"].decode()),
                    started_at=datetime.fromisoformat(task_data[b"started_at"].decode()) if b"started_at" in task_data else None,
                    completed_at=datetime.fromisoformat(task_data[b"completed_at"].decode()) if b"completed_at" in task_data else None,
                    error_message=task_data[b"error_message"].decode() if b"error_message" in task_data else None,
                    retry_count=int(task_data[b"retry_count"].decode()),
                    max_retries=int(task_data[b"max_retries"].decode())
                )
            except Exception as e:
                logger.error(f"Error getting Redis task status: {str(e)}")
                return None
        else:
            return self.in_memory_queue.get_task_status(task_id)
    
    def get_queue_stats(self) -> Dict:
        """Get queue statistics"""
        if self.use_redis:
            try:
                queue_length = self.redis_queue.redis_client.llen("blood_analysis_queue")
                return {
                    "backend": "redis",
                    "queued": queue_length,
                    "processing": "N/A",  # Would need separate tracking
                    "completed": "N/A",
                    "failed": "N/A"
                }
            except Exception as e:
                logger.error(f"Error getting Redis stats: {str(e)}")
                return {"error": str(e)}
        else:
            stats = self.in_memory_queue.get_queue_stats()
            stats["backend"] = "in-memory"
            return stats
    
    def health_check(self) -> Dict:
        """Queue health check"""
        try:
            if self.use_redis:
                self.redis_queue.redis_client.ping()
                return {"status": "healthy", "backend": "redis"}
            else:
                return {"status": "healthy", "backend": "in-memory"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}