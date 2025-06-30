from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import uuid
import asyncio
from datetime import datetime
from typing import Optional
import logging

from crewai import Crew, Process
from agents import doctor, verifier, nutritionist, exercise_specialist
from tasks import help_patients, verification_task, nutrition_analysis, exercise_planning
from database import DatabaseManager, AnalysisResult
from queue_worker import QueueManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Blood Test Report Analyzer",
    description="AI-powered blood test analysis with comprehensive health recommendations",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database and queue managers
db_manager = DatabaseManager()
queue_manager = QueueManager()

@app.on_event("startup")
async def startup_event():
    """Initialize database and queue on startup"""
    await db_manager.init_db()
    logger.info("Database initialized successfully")

def run_crew(query: str, file_path: str, analysis_type: str = "comprehensive"):
    """Run the CrewAI analysis crew"""
    try:
        if analysis_type == "verification":
            medical_crew = Crew(
                agents=[verifier],
                tasks=[verification_task],
                process=Process.sequential,
                verbose=True
            )
        elif analysis_type == "nutrition":
            medical_crew = Crew(
                agents=[doctor, nutritionist],
                tasks=[help_patients, nutrition_analysis],
                process=Process.sequential,
                verbose=True
            )
        elif analysis_type == "exercise":
            medical_crew = Crew(
                agents=[doctor, exercise_specialist],
                tasks=[help_patients, exercise_planning],
                process=Process.sequential,
                verbose=True
            )
        else:  # comprehensive analysis
            medical_crew = Crew(
                agents=[doctor, verifier, nutritionist, exercise_specialist],
                tasks=[verification_task, help_patients, nutrition_analysis, exercise_planning],
                process=Process.sequential,
                verbose=True
            )
        
        result = medical_crew.kickoff({
            'query': query,
            'file_path': file_path
        })
        
        return {
            "status": "success",
            "result": str(result),
            "analysis_type": analysis_type
        }
        
    except Exception as e:
        logger.error(f"Crew execution error: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "analysis_type": analysis_type
        }

async def process_analysis_background(analysis_id: str, query: str, file_path: str, analysis_type: str):
    """Background task to process analysis"""
    try:
        # Update status to processing
        await db_manager.update_analysis_status(analysis_id, "processing")
        
        # Run the crew analysis
        result = run_crew(query, file_path, analysis_type)
        
        # Update database with results
        if result["status"] == "success":
            await db_manager.update_analysis_result(
                analysis_id, 
                "completed", 
                result["result"]
            )
        else:
            await db_manager.update_analysis_result(
                analysis_id,
                "failed",
                result.get("error", "Unknown error")
            )
            
    except Exception as e:
        logger.error(f"Background processing error: {str(e)}")
        await db_manager.update_analysis_result(analysis_id, "failed", str(e))
    
    finally:
        # Clean up file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Blood Test Report Analyzer API is running",
        "version": "2.0.0",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        db_status = await db_manager.health_check()
        queue_status = queue_manager.health_check()
        
        return {
            "status": "healthy",
            "database": db_status,
            "queue": queue_status,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

@app.post("/analyze")
async def analyze_blood_report(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    query: str = Form(default="Provide comprehensive analysis of my blood test report"),
    analysis_type: str = Form(default="comprehensive")
):
    """Analyze blood test report and provide comprehensive health recommendations"""
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Generate unique identifiers
    analysis_id = str(uuid.uuid4())
    file_id = str(uuid.uuid4())
    file_path = f"data/blood_test_report_{file_id}.pdf"
    
    try:
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        
        # Save uploaded file
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Validate query
        if not query or query.strip() == "":
            query = "Provide comprehensive analysis of my blood test report"
        
        # Validate analysis type
        valid_types = ["comprehensive", "verification", "nutrition", "exercise"]
        if analysis_type not in valid_types:
            analysis_type = "comprehensive"
        
        # Store analysis request in database
        analysis_result = AnalysisResult(
            id=analysis_id,
            filename=file.filename,
            query=query.strip(),
            analysis_type=analysis_type,
            status="queued",
            result=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        await db_manager.create_analysis(analysis_result)
        
        # Add to background processing queue
        background_tasks.add_task(
            process_analysis_background,
            analysis_id,
            query.strip(),
            file_path,
            analysis_type
        )
        
        return {
            "status": "queued",
            "analysis_id": analysis_id,
            "message": "Analysis queued successfully. Use the analysis_id to check status.",
            "query": query.strip(),
            "analysis_type": analysis_type,
            "file_processed": file.filename
        }
        
    except Exception as e:
        # Clean up file on error
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        
        logger.error(f"Analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing blood report: {str(e)}")

@app.get("/analysis/{analysis_id}")
async def get_analysis_status(analysis_id: str):
    """Get analysis status and results"""
    try:
        analysis = await db_manager.get_analysis(analysis_id)
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        return {
            "analysis_id": analysis_id,
            "status": analysis.status,
            "query": analysis.query,
            "analysis_type": analysis.analysis_type,
            "filename": analysis.filename,
            "result": analysis.result,
            "created_at": analysis.created_at.isoformat(),
            "updated_at": analysis.updated_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving analysis: {str(e)}")

@app.get("/analysis")
async def list_analyses(limit: int = 10, offset: int = 0):
    """List recent analyses"""
    try:
        analyses = await db_manager.list_analyses(limit, offset)
        return {
            "analyses": [
                {
                    "analysis_id": analysis.id,
                    "status": analysis.status,
                    "query": analysis.query,
                    "analysis_type": analysis.analysis_type,
                    "filename": analysis.filename,
                    "created_at": analysis.created_at.isoformat(),
                    "updated_at": analysis.updated_at.isoformat()
                }
                for analysis in analyses
            ],
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error listing analyses: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing analyses: {str(e)}")

@app.delete("/analysis/{analysis_id}")
async def delete_analysis(analysis_id: str):
    """Delete an analysis record"""
    try:
        success = await db_manager.delete_analysis(analysis_id)
        if not success:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        return {"message": "Analysis deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting analysis: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )