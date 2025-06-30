import sqlite3
import aiosqlite
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass
import json
import logging

logger = logging.getLogger(__name__)

@dataclass
class AnalysisResult:
    """Data class for analysis results"""
    id: str
    filename: str
    query: str
    analysis_type: str
    status: str  # queued, processing, completed, failed
    result: Optional[str]
    created_at: datetime
    updated_at: datetime

class DatabaseManager:
    """Database manager for storing analysis results and user data"""
    
    def __init__(self, db_path: str = "blood_analysis.db"):
        self.db_path = db_path
    
    async def init_db(self):
        """Initialize database tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # Create analyses table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS analyses (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    query TEXT NOT NULL,
                    analysis_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    result TEXT,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL
                )
            ''')
            
            # Create users table for future expansion
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE,
                    name TEXT,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL
                )
            ''')
            
            # Create analysis_metadata table for additional info
            await db.execute('''
                CREATE TABLE IF NOT EXISTS analysis_metadata (
                    analysis_id TEXT PRIMARY KEY,
                    file_size INTEGER,
                    processing_time_seconds REAL,
                    model_version TEXT,
                    additional_data TEXT,
                    FOREIGN KEY (analysis_id) REFERENCES analyses (id)
                )
            ''')
            
            # Create indexes for better performance
            await db.execute('CREATE INDEX IF NOT EXISTS idx_analyses_status ON analyses(status)')
            await db.execute('CREATE INDEX IF NOT EXISTS idx_analyses_created_at ON analyses(created_at)')
            await db.execute('CREATE INDEX IF NOT EXISTS idx_analyses_type ON analyses(analysis_type)')
            
            await db.commit()
            logger.info("Database initialized successfully")
    
    async def create_analysis(self, analysis: AnalysisResult) -> bool:
        """Create a new analysis record"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT INTO analyses (id, filename, query, analysis_type, status, result, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    analysis.id,
                    analysis.filename,
                    analysis.query,
                    analysis.analysis_type,
                    analysis.status,
                    analysis.result,
                    analysis.created_at,
                    analysis.updated_at
                ))
                await db.commit()
                logger.info(f"Analysis {analysis.id} created successfully")
                return True
        except Exception as e:
            logger.error(f"Error creating analysis: {str(e)}")
            return False
    
    async def get_analysis(self, analysis_id: str) -> Optional[AnalysisResult]:
        """Get analysis by ID"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute('''
                    SELECT id, filename, query, analysis_type, status, result, created_at, updated_at
                    FROM analyses WHERE id = ?
                ''', (analysis_id,))
                
                row = await cursor.fetchone()
                if row:
                    return AnalysisResult(
                        id=row[0],
                        filename=row[1],
                        query=row[2],
                        analysis_type=row[3],
                        status=row[4],
                        result=row[5],
                        created_at=datetime.fromisoformat(row[6]),
                        updated_at=datetime.fromisoformat(row[7])
                    )
                return None
        except Exception as e:
            logger.error(f"Error getting analysis: {str(e)}")
            return None
    
    async def update_analysis_status(self, analysis_id: str, status: str) -> bool:
        """Update analysis status"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    UPDATE analyses SET status = ?, updated_at = ?
                    WHERE id = ?
                ''', (status, datetime.utcnow(), analysis_id))
                await db.commit()
                logger.info(f"Analysis {analysis_id} status updated to {status}")
                return True
        except Exception as e:
            logger.error(f"Error updating analysis status: {str(e)}")
            return False
    
    async def update_analysis_result(self, analysis_id: str, status: str, result: str) -> bool:
        """Update analysis result and status"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    UPDATE analyses SET status = ?, result = ?, updated_at = ?
                    WHERE id = ?
                ''', (status, result, datetime.utcnow(), analysis_id))
                await db.commit()
                logger.info(f"Analysis {analysis_id} completed with status {status}")
                return True
        except Exception as e:
            logger.error(f"Error updating analysis result: {str(e)}")
            return False
    
    async def list_analyses(self, limit: int = 10, offset: int = 0) -> List[AnalysisResult]:
        """List analyses with pagination"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute('''
                    SELECT id, filename, query, analysis_type, status, result, created_at, updated_at
                    FROM analyses 
                    ORDER BY created_at DESC 
                    LIMIT ? OFFSET ?
                ''', (limit, offset))
                
                rows = await cursor.fetchall()
                return [
                    AnalysisResult(
                        id=row[0],
                        filename=row[1],
                        query=row[2],
                        analysis_type=row[3],
                        status=row[4],
                        result=row[5],
                        created_at=datetime.fromisoformat(row[6]),
                        updated_at=datetime.fromisoformat(row[7])
                    )
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Error listing analyses: {str(e)}")
            return []
    
    async def delete_analysis(self, analysis_id: str) -> bool:
        """Delete analysis record"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute('DELETE FROM analyses WHERE id = ?', (analysis_id,))
                await db.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting analysis: {str(e)}")
            return False
    
    async def get_analysis_stats(self) -> dict:
        """Get analysis statistics"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Total analyses
                cursor = await db.execute('SELECT COUNT(*) FROM analyses')
                total = (await cursor.fetchone())[0]
                
                # Status breakdown
                cursor = await db.execute('''
                    SELECT status, COUNT(*) FROM analyses GROUP BY status
                ''')
                status_counts = dict(await cursor.fetchall())
                
                # Analysis type breakdown
                cursor = await db.execute('''
                    SELECT analysis_type, COUNT(*) FROM analyses GROUP BY analysis_type
                ''')
                type_counts = dict(await cursor.fetchall())
                
                return {
                    'total_analyses': total,
                    'status_breakdown': status_counts,
                    'type_breakdown': type_counts
                }
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            return {}
    
    async def health_check(self) -> dict:
        """Database health check"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute('SELECT 1')
                await cursor.fetchone()
                return {"status": "healthy", "connection": "ok"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}