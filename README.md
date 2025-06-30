# BloodTest-Analyzer

A comprehensive AI-powered blood test analysis system built with CrewAI, FastAPI, and modern async architecture. This system provides intelligent analysis of blood test reports with specialized AI agents for medical analysis, nutrition recommendations, and exercise planning.

## 🐛 Bugs Found and Fixed

### Critical Issues Resolved:

1. **Undefined LLM Variable** (`agents.py`)
   - **Problem**: `llm = llm` was undefined
   - **Fix**: Properly imported and configured `ChatOpenAI` from LangChain with environment variables

2. **Missing Import Dependencies** 
   - **Problem**: `PDFLoader` not imported, incorrect imports throughout
   - **Fix**: Added proper imports for `PyPDFLoader`, `BaseTool`, and other dependencies

3. **Incorrect Tool Implementation** (`tools.py`)
   - **Problem**: Tools used incorrect async syntax and method signatures
   - **Fix**: Implemented proper `BaseTool` inheritance with correct `_run` methods and Pydantic schemas

4. **Task-Agent Mismatch** (`task.py`)
   - **Problem**: Tasks assigned to wrong agents, poor task descriptions
   - **Fix**: Properly matched tasks to appropriate agents and rewrote professional task descriptions

5. **Improper File Handling** (`main.py`)
   - **Problem**: No proper file cleanup, synchronous file operations
   - **Fix**: Added proper async file handling and cleanup in try/finally blocks

6. **Poor Agent Backstories**
   - **Problem**: Agents designed to give bad medical advice and make up information
   - **Fix**: Rewrote all agent backstories to be professional, evidence-based, and ethical

7. **Missing Error Handling**
   - **Problem**: No comprehensive error handling throughout the system
   - **Fix**: Added proper exception handling, logging, and user-friendly error messages

8. **Requirements File Issues**
   - **Problem**: Missing key dependencies, incorrect package names
   - **Fix**: Complete requirements.txt with all necessary packages and correct versions

## 🚀 New Features Added

### Database Integration
- **SQLite Database**: Persistent storage for analysis results
- **Async Operations**: All database operations are async for better performance
- **Data Models**: Proper data structures for analysis results and metadata
- **Statistics**: Built-in analytics for system usage

### Queue Worker System
- **Dual Backend**: Support for both in-memory and Redis-based queues
- **Background Processing**: Asynchronous analysis processing
- **Retry Logic**: Automatic retry mechanism for failed tasks
- **Status Tracking**: Real-time status updates for analysis requests

### Enhanced API
- **RESTful Design**: Complete REST API with proper status codes
- **Background Tasks**: Non-blocking analysis processing
- **Health Checks**: System health monitoring endpoints
- **CORS Support**: Cross-origin resource sharing enabled

## 📋 Setup and Installation

### Prerequisites
- Python 3.8+
- OpenAI API key (or other supported LLM provider)
- Optional: Redis server (for production queue management)

### Environment Setup

1. **Clone the repository**
```bash
git clone <https://github.com/veetla-jainath/BloodTest-Analyzer.git>
cd blood-test-analyzer
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Environment Variables**
Create a `.env` file in the root directory:
```env
# Required: OpenAI Configuration
GEMINI_API_KEY=your_openai_api_key_here

# Optional: Serper Dev API for web search
SERPER_API_KEY=your_serper_api_key_here

# Optional: Redis Configuration (for production)
REDIS_URL=redis://localhost:6379

# Optional: Database Configuration
DATABASE_URL=sqlite:///blood_analysis.db
```

5. **Create required directories**
```bash
mkdir -p data outputs
```

## 🔧 Usage Instructions

### Starting the Server

**Development Mode:**
```bash
python main.py
```

**Production Mode:**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### API Endpoints

The server will start on `http://localhost:8000`
- **API Documentation**: `http://localhost:8000/docs`
- **Alternative Docs**: `http://localhost:8000/redoc`

### Basic Usage
**open:
1. **Health Check**
```bash
curl http://localhost:8000/docs#
```

2. **Analyze Blood Report**
```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your_blood_report.pdf" \
  -F "query=Analyze my blood test results" \
  -F "analysis_type=comprehensive"
```

3. **Check Analysis Status**
```bash
curl "http://localhost:8000/analysis/{analysis_id}"
```

4. **List All Analyses**
```bash
curl "http://localhost:8000/analysis?limit=10&offset=0"
```

## 📊 API Documentation

### Analysis Endpoints

#### POST `/analyze`
Upload and analyze a blood test report.

**Parameters:**
- `file` (required): PDF file containing blood test report
- `query` (optional): Specific question about the blood test
- `analysis_type` (optional): Type of analysis (`comprehensive`, `nutrition`, `exercise`, `verification`)

**Response:**
```json
{
  "status": "queued",
  "analysis_id": "uuid-string",
  "message": "Analysis queued successfully",
  "query": "Your query here",
  "analysis_type": "comprehensive",
  "file_processed": "filename.pdf"
}
```

#### GET `/analysis/{analysis_id}`
Get analysis results by ID.

**Response:**
```json
{
  "analysis_id": "uuid-string",
  "status": "completed",
  "query": "Your query",
  "analysis_type": "comprehensive",
  "filename": "report.pdf",
  "result": "Detailed analysis results...",
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:05:00"
}
```

#### GET `/analysis`
List recent analyses with pagination.

**Parameters:**
- `limit` (optional): Number of results (default: 10)
- `offset` (optional): Offset for pagination (default: 0)

#### DELETE `/analysis/{analysis_id}`
Delete an analysis record.

### System Endpoints

#### GET `/health`
Detailed system health check.

**Response:**
```json
{
  "status": "healthy",
  "database": {"status": "healthy", "connection": "ok"},
  "queue": {"status": "healthy", "backend": "in-memory"},
  "timestamp": "2024-01-01T00:00:00"
}
```

## 🏗️ Architecture

### System Components

1. **CrewAI Agents**
   - **Doctor Agent**: Primary medical analysis
   - **Verifier Agent**: Document validation
   - **Nutritionist Agent**: Dietary recommendations
   - **Exercise Specialist**: Fitness guidance

2. **Tools**
   - **BloodTestReportTool**: PDF reading and parsing
   - **NutritionTool**: Nutritional analysis
   - **ExerciseTool**: Exercise planning
   - **SearchTool**: Web search capabilities

3. **Database Layer**
   - **DatabaseManager**: Async SQLite operations
   - **Analysis tracking**: Complete audit trail
   - **Statistics**: Usage analytics

4. **Queue System**
   - **QueueManager**: Dual backend support
   - **Background processing**: Non-blocking operations
   - **Retry logic**: Fault tolerance

### Data Flow

1. **Upload**: User uploads PDF via API
2. **Queue**: Request added to processing queue
3. **Process**: CrewAI agents analyze the document
4. **Store**: Results saved to database
5. **Retrieve**: User gets results via API

## 🧪 Testing

### Unit Tests
```bash
pytest tests/
```

### API Testing
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test analysis with sample file
curl -X POST "http://localhost:8000/analyze" \
  -F "file=@data/sample.pdf" \
  -F "query=Test analysis"
```

## 🔒 Security Considerations

- **File Validation**: Only PDF files accepted
- **Input Sanitization**: All user inputs are validated
- **Error Handling**: No sensitive information in error messages
- **File Cleanup**: Uploaded files are automatically cleaned up
- **Rate Limiting**: Consider implementing rate limiting for production

## 🚀 Production Deployment

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8
