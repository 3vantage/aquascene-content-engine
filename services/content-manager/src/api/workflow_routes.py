"""
Workflow API Routes
Handles agentic workflow operations including Airtable schema analysis
"""
import os
import json
import uuid
import subprocess
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from fastapi import APIRouter, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.session import get_async_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/workflows", tags=["workflows"])

# In-memory storage for workflow executions (in production, use Redis/DB)
workflow_executions = {}
active_connections = []

class WorkflowConfig(BaseModel):
    """Configuration for workflow execution"""
    airtable_api_key: str = Field(..., description="Airtable API Key")
    airtable_base_id: str = Field(..., description="Airtable Base ID")
    workflow_type: str = Field(..., description="Type of workflow to execute")
    options: Dict[str, Any] = Field(default_factory=dict, description="Additional options")

class WorkflowStatus(BaseModel):
    """Workflow execution status"""
    workflow_id: str
    status: str  # pending, running, completed, failed
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    progress: float = 0.0
    logs: List[str] = []
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class ConnectionManager:
    """WebSocket connection manager for real-time updates"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def send_workflow_update(self, workflow_id: str, data: Dict[str, Any]):
        message = json.dumps({
            "type": "workflow_update",
            "workflow_id": workflow_id,
            "data": data
        })
        
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            self.active_connections.remove(conn)

# Global connection manager
connection_manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time workflow updates"""
    await connection_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)

@router.post("/airtable/test-connection")
async def test_airtable_connection(config: WorkflowConfig):
    """Test Airtable API connection"""
    try:
        # Create a temporary Python script to test connection
        script_content = f"""
import os
from pyairtable import Api
import sys

try:
    api = Api('{config.airtable_api_key}')
    base = api.base('{config.airtable_base_id}')
    tables = base.schema().tables
    print(f"SUCCESS: Connected to base with {{len(tables)}} tables")
    for table in tables:
        print(f"- {{table.name}}")
    sys.exit(0)
except Exception as e:
    print(f"ERROR: {{str(e)}}")
    sys.exit(1)
"""
        
        # Write temporary script
        script_path = f"/tmp/test_connection_{uuid.uuid4().hex}.py"
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        # Execute script
        result = subprocess.run(
            ["python3", script_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Clean up
        os.unlink(script_path)
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            tables = [line.replace('- ', '') for line in lines[1:] if line.startswith('- ')]
            return {
                "success": True,
                "message": lines[0],
                "tables": tables
            }
        else:
            return {
                "success": False,
                "message": result.stdout or result.stderr
            }
            
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/airtable/schema-analysis")
async def start_airtable_analysis(config: WorkflowConfig, background_tasks: BackgroundTasks):
    """Start Airtable schema analysis workflow"""
    workflow_id = str(uuid.uuid4())
    
    # Initialize workflow status
    workflow_executions[workflow_id] = WorkflowStatus(
        workflow_id=workflow_id,
        status="pending",
        started_at=datetime.now()
    )
    
    # Start background task
    background_tasks.add_task(
        execute_airtable_analysis,
        workflow_id,
        config.airtable_api_key,
        config.airtable_base_id
    )
    
    return {"workflow_id": workflow_id, "status": "started"}

async def execute_airtable_analysis(workflow_id: str, api_key: str, base_id: str):
    """Execute the Airtable schema analysis in the background"""
    try:
        status = workflow_executions[workflow_id]
        status.status = "running"
        status.logs.append("Starting Airtable schema analysis...")
        
        # Notify via WebSocket
        await connection_manager.send_workflow_update(workflow_id, {
            "status": status.status,
            "progress": 10,
            "logs": status.logs
        })
        
        # Create the analysis script with environment variables
        script_content = f"""
import os
import sys
sys.path.append('/app')

# Set environment variables
os.environ['AIRTABLE_API_KEY'] = '{api_key}'
os.environ['AIRTABLE_BASE_ID'] = '{base_id}'

# Import and run the analysis
from airtable_schema_analysis import AirtableSchemaAnalyzer
import json
from datetime import datetime

def main():
    try:
        print("Initializing analyzer...")
        analyzer = AirtableSchemaAnalyzer('{api_key}', '{base_id}')
        
        print("Performing analysis...")
        base_metadata = analyzer.perform_full_analysis()
        
        if not base_metadata:
            print("ERROR: Analysis failed")
            return 1
        
        print("Exporting results...")
        json_file = analyzer.export_results(base_metadata, 'json')
        summary_file = analyzer.export_results(base_metadata, 'summary')
        
        print(f"SUCCESS:{{json_file}},{{summary_file}}")
        return 0
        
    except Exception as e:
        print(f"ERROR: {{str(e)}}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
"""
        
        # Write the script to a temporary file
        script_path = f"/tmp/analysis_{workflow_id}.py"
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        status.logs.append("Created analysis script")
        await connection_manager.send_workflow_update(workflow_id, {
            "status": status.status,
            "progress": 20,
            "logs": status.logs
        })
        
        # Copy the analysis script to the working directory
        analysis_script_path = "/app/airtable_schema_analysis.py"
        if os.path.exists("/Users/kg/aquascene-content-engine/airtable_schema_analysis.py"):
            import shutil
            shutil.copy2("/Users/kg/aquascene-content-engine/airtable_schema_analysis.py", analysis_script_path)
        
        # Execute the analysis
        process = subprocess.Popen(
            ["python3", script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd="/app"
        )
        
        status.logs.append("Running schema analysis...")
        await connection_manager.send_workflow_update(workflow_id, {
            "status": status.status,
            "progress": 30,
            "logs": status.logs
        })
        
        # Monitor progress
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                status.logs.append(output.strip())
                status.progress = min(90, status.progress + 10)
                await connection_manager.send_workflow_update(workflow_id, {
                    "status": status.status,
                    "progress": status.progress,
                    "logs": status.logs
                })
        
        return_code = process.poll()
        stdout, stderr = process.communicate()
        
        # Clean up script
        if os.path.exists(script_path):
            os.unlink(script_path)
        
        if return_code == 0:
            # Parse the output to get file names
            last_line = status.logs[-1] if status.logs else ""
            if last_line.startswith("SUCCESS:"):
                files = last_line.replace("SUCCESS:", "").split(",")
                status.results = {
                    "json_file": files[0] if len(files) > 0 else None,
                    "summary_file": files[1] if len(files) > 1 else None
                }
            
            status.status = "completed"
            status.completed_at = datetime.now()
            status.progress = 100.0
            status.logs.append("Analysis completed successfully!")
        else:
            status.status = "failed"
            status.completed_at = datetime.now()
            status.error = stderr or "Analysis failed"
            status.logs.append(f"Error: {status.error}")
        
        await connection_manager.send_workflow_update(workflow_id, {
            "status": status.status,
            "progress": status.progress,
            "logs": status.logs,
            "results": status.results,
            "error": status.error
        })
        
    except Exception as e:
        logger.error(f"Workflow {workflow_id} failed: {e}")
        status = workflow_executions.get(workflow_id)
        if status:
            status.status = "failed"
            status.completed_at = datetime.now()
            status.error = str(e)
            status.logs.append(f"Unexpected error: {str(e)}")
            
            await connection_manager.send_workflow_update(workflow_id, {
                "status": status.status,
                "progress": status.progress,
                "logs": status.logs,
                "error": status.error
            })

@router.get("/status/{workflow_id}")
async def get_workflow_status(workflow_id: str):
    """Get the current status of a workflow execution"""
    if workflow_id not in workflow_executions:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return workflow_executions[workflow_id]

@router.get("/")
async def list_workflows():
    """List all workflow executions"""
    return list(workflow_executions.values())

@router.post("/airtable/create-metadata-table")
async def create_metadata_table(workflow_id: str, background_tasks: BackgroundTasks):
    """Create metadata table from analysis results"""
    if workflow_id not in workflow_executions:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    status = workflow_executions[workflow_id]
    if status.status != "completed" or not status.results:
        raise HTTPException(status_code=400, detail="Analysis must be completed first")
    
    # Start metadata table creation
    metadata_workflow_id = str(uuid.uuid4())
    workflow_executions[metadata_workflow_id] = WorkflowStatus(
        workflow_id=metadata_workflow_id,
        status="pending",
        started_at=datetime.now()
    )
    
    background_tasks.add_task(
        execute_metadata_table_creation,
        metadata_workflow_id,
        status.results.get("json_file")
    )
    
    return {"workflow_id": metadata_workflow_id, "status": "started"}


@router.post("/airtable/sync-to-database")
async def sync_airtable_to_database(
    workflow_id: str, 
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session)
):
    """Sync Airtable analysis results to database"""
    if workflow_id not in workflow_executions:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    status = workflow_executions[workflow_id]
    if status.status != "completed" or not status.results:
        raise HTTPException(status_code=400, detail="Analysis must be completed first")
    
    try:
        from ..services.airtable_integration import airtable_integration
        import json
        
        # Load analysis results
        json_file = status.results.get("json_file")
        if not json_file or not os.path.exists(json_file):
            raise HTTPException(status_code=400, detail="Analysis results file not found")
        
        with open(json_file, 'r') as f:
            airtable_data = json.load(f)
        
        # Sync to database
        sync_results = await airtable_integration.sync_content_from_airtable(
            session, airtable_data
        )
        
        return {
            "success": True,
            "workflow_id": workflow_id,
            "sync_results": sync_results
        }
        
    except Exception as e:
        logger.error(f"Failed to sync Airtable data to database: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def execute_metadata_table_creation(workflow_id: str, analysis_file: str):
    """Execute metadata table creation"""
    try:
        status = workflow_executions[workflow_id]
        status.status = "running"
        status.logs.append("Starting metadata table creation...")
        
        await connection_manager.send_workflow_update(workflow_id, {
            "status": status.status,
            "progress": 10,
            "logs": status.logs
        })
        
        # Create metadata table creation script
        script_content = f"""
import sys
sys.path.append('/app')

from create_metadata_table import MetadataTableCreator
import os

def main():
    try:
        print("Loading analysis results...")
        creator = MetadataTableCreator('{analysis_file}')
        
        if not creator.load_analysis():
            print("ERROR: Failed to load analysis")
            return 1
        
        print("Generating metadata table files...")
        instructions_file, structure_file, records_file = creator.export_creation_files()
        
        print(f"SUCCESS:{{instructions_file}},{{structure_file}},{{records_file}}")
        return 0
        
    except Exception as e:
        print(f"ERROR: {{str(e)}}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
"""
        
        script_path = f"/tmp/metadata_{workflow_id}.py"
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        # Copy the metadata creation script
        metadata_script_path = "/app/create_metadata_table.py"
        if os.path.exists("/Users/kg/aquascene-content-engine/create_metadata_table.py"):
            import shutil
            shutil.copy2("/Users/kg/aquascene-content-engine/create_metadata_table.py", metadata_script_path)
        
        # Execute the script
        result = subprocess.run(
            ["python3", script_path],
            capture_output=True,
            text=True,
            timeout=60,
            cwd="/app"
        )
        
        os.unlink(script_path)
        
        if result.returncode == 0:
            # Parse output files
            last_line = result.stdout.strip().split('\n')[-1]
            if last_line.startswith("SUCCESS:"):
                files = last_line.replace("SUCCESS:", "").split(",")
                status.results = {
                    "instructions_file": files[0] if len(files) > 0 else None,
                    "structure_file": files[1] if len(files) > 1 else None,
                    "records_file": files[2] if len(files) > 2 else None
                }
            
            status.status = "completed"
            status.completed_at = datetime.now()
            status.progress = 100.0
            status.logs.extend(result.stdout.strip().split('\n'))
        else:
            status.status = "failed"
            status.completed_at = datetime.now()
            status.error = result.stderr or "Metadata table creation failed"
            status.logs.append(f"Error: {status.error}")
        
        await connection_manager.send_workflow_update(workflow_id, {
            "status": status.status,
            "progress": status.progress,
            "logs": status.logs,
            "results": status.results,
            "error": status.error
        })
        
    except Exception as e:
        logger.error(f"Metadata workflow {workflow_id} failed: {e}")
        status = workflow_executions.get(workflow_id)
        if status:
            status.status = "failed"
            status.completed_at = datetime.now()
            status.error = str(e)

@router.post("/test-workflow")
async def test_complete_workflow(config: WorkflowConfig, background_tasks: BackgroundTasks):
    """Test complete end-to-end workflow execution"""
    workflow_id = str(uuid.uuid4())
    
    # Initialize workflow status
    workflow_executions[workflow_id] = WorkflowStatus(
        workflow_id=workflow_id,
        status="pending",
        started_at=datetime.now()
    )
    
    # Start comprehensive test workflow
    background_tasks.add_task(
        execute_test_workflow,
        workflow_id,
        config.airtable_api_key,
        config.airtable_base_id
    )
    
    return {"workflow_id": workflow_id, "status": "started", "message": "Complete workflow test started"}

async def execute_test_workflow(workflow_id: str, api_key: str, base_id: str):
    """Execute a comprehensive test workflow"""
    try:
        status = workflow_executions[workflow_id]
        status.status = "running"
        status.logs.append("Starting comprehensive workflow test...")
        
        await connection_manager.send_workflow_update(workflow_id, {
            "status": status.status,
            "progress": 5,
            "logs": status.logs
        })
        
        # Step 1: Test Airtable connection
        status.logs.append("Step 1: Testing Airtable connection...")
        status.progress = 10
        await connection_manager.send_workflow_update(workflow_id, {
            "status": status.status,
            "progress": status.progress,
            "logs": status.logs
        })
        
        connection_result = await test_connection_internal(api_key, base_id)
        if not connection_result["success"]:
            raise Exception(f"Connection test failed: {connection_result['message']}")
        
        status.logs.append(f"✓ Connected to Airtable with {len(connection_result['tables'])} tables")
        status.progress = 25
        
        # Step 2: Run schema analysis
        status.logs.append("Step 2: Running schema analysis...")
        await connection_manager.send_workflow_update(workflow_id, {
            "status": status.status,
            "progress": status.progress,
            "logs": status.logs
        })
        
        analysis_result = await run_schema_analysis_internal(workflow_id, api_key, base_id)
        if not analysis_result["success"]:
            raise Exception(f"Schema analysis failed: {analysis_result['error']}")
        
        status.logs.append("✓ Schema analysis completed successfully")
        status.progress = 75
        
        # Step 3: Generate metadata table files
        status.logs.append("Step 3: Generating metadata table files...")
        await connection_manager.send_workflow_update(workflow_id, {
            "status": status.status,
            "progress": status.progress,
            "logs": status.logs
        })
        
        metadata_result = await create_metadata_files_internal(analysis_result["json_file"])
        if not metadata_result["success"]:
            raise Exception(f"Metadata creation failed: {metadata_result['error']}")
        
        status.logs.append("✓ Metadata table files generated successfully")
        status.progress = 100
        
        # Final results
        status.status = "completed"
        status.completed_at = datetime.now()
        status.results = {
            "connection_test": connection_result,
            "schema_analysis": analysis_result,
            "metadata_files": metadata_result,
            "json_file": analysis_result.get("json_file"),
            "summary_file": analysis_result.get("summary_file"),
            "instructions_file": metadata_result.get("instructions_file"),
            "structure_file": metadata_result.get("structure_file"),
            "records_file": metadata_result.get("records_file")
        }
        
        status.logs.append("🎉 Complete workflow test finished successfully!")
        
        await connection_manager.send_workflow_update(workflow_id, {
            "status": status.status,
            "progress": status.progress,
            "logs": status.logs,
            "results": status.results
        })
        
    except Exception as e:
        logger.error(f"Test workflow {workflow_id} failed: {e}")
        status = workflow_executions.get(workflow_id)
        if status:
            status.status = "failed"
            status.completed_at = datetime.now()
            status.error = str(e)
            status.logs.append(f"❌ Workflow failed: {str(e)}")
            
            await connection_manager.send_workflow_update(workflow_id, {
                "status": status.status,
                "progress": status.progress,
                "logs": status.logs,
                "error": status.error
            })

async def test_connection_internal(api_key: str, base_id: str) -> dict:
    """Internal function to test Airtable connection"""
    try:
        script_content = f"""
import os
from pyairtable import Api
import sys

try:
    api = Api('{api_key}')
    base = api.base('{base_id}')
    tables = base.schema().tables
    print(f"SUCCESS: Connected to base with {{len(tables)}} tables")
    for table in tables:
        print(f"- {{table.name}}")
    sys.exit(0)
except Exception as e:
    print(f"ERROR: {{str(e)}}")
    sys.exit(1)
"""
        
        script_path = f"/tmp/test_connection_{uuid.uuid4().hex}.py"
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        result = subprocess.run(
            ["python3", script_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        os.unlink(script_path)
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            tables = [line.replace('- ', '') for line in lines[1:] if line.startswith('- ')]
            return {
                "success": True,
                "message": lines[0],
                "tables": tables
            }
        else:
            return {
                "success": False,
                "message": result.stdout or result.stderr
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

async def run_schema_analysis_internal(workflow_id: str, api_key: str, base_id: str) -> dict:
    """Internal function to run schema analysis"""
    try:
        script_content = f"""
import os
import sys
sys.path.append('/app')

os.environ['AIRTABLE_API_KEY'] = '{api_key}'
os.environ['AIRTABLE_BASE_ID'] = '{base_id}'

from airtable_schema_analysis import AirtableSchemaAnalyzer
import json
from datetime import datetime

def main():
    try:
        analyzer = AirtableSchemaAnalyzer('{api_key}', '{base_id}')
        base_metadata = analyzer.perform_full_analysis()
        
        if not base_metadata:
            print("ERROR: Analysis failed")
            return 1
        
        json_file = analyzer.export_results(base_metadata, 'json')
        summary_file = analyzer.export_results(base_metadata, 'summary')
        
        print(f"SUCCESS:{{json_file}},{{summary_file}}")
        return 0
        
    except Exception as e:
        print(f"ERROR: {{str(e)}}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
"""
        
        script_path = f"/tmp/analysis_{workflow_id}.py"
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        # Copy analysis script if it exists
        analysis_script_path = "/app/airtable_schema_analysis.py"
        if os.path.exists("/Users/kg/aquascene-content-engine/airtable_schema_analysis.py"):
            import shutil
            shutil.copy2("/Users/kg/aquascene-content-engine/airtable_schema_analysis.py", analysis_script_path)
        
        result = subprocess.run(
            ["python3", script_path],
            capture_output=True,
            text=True,
            timeout=120,
            cwd="/app"
        )
        
        os.unlink(script_path)
        
        if result.returncode == 0:
            last_line = result.stdout.strip().split('\n')[-1]
            if last_line.startswith("SUCCESS:"):
                files = last_line.replace("SUCCESS:", "").split(",")
                return {
                    "success": True,
                    "json_file": files[0] if len(files) > 0 else None,
                    "summary_file": files[1] if len(files) > 1 else None
                }
        
        return {
            "success": False,
            "error": result.stderr or result.stdout or "Analysis failed"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

async def create_metadata_files_internal(analysis_file: str) -> dict:
    """Internal function to create metadata files"""
    try:
        script_content = f"""
import sys
sys.path.append('/app')

from create_metadata_table import MetadataTableCreator
import os

def main():
    try:
        creator = MetadataTableCreator('{analysis_file}')
        
        if not creator.load_analysis():
            print("ERROR: Failed to load analysis")
            return 1
        
        instructions_file, structure_file, records_file = creator.export_creation_files()
        
        print(f"SUCCESS:{{instructions_file}},{{structure_file}},{{records_file}}")
        return 0
        
    except Exception as e:
        print(f"ERROR: {{str(e)}}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
"""
        
        script_path = f"/tmp/metadata_{uuid.uuid4().hex}.py"
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        # Copy metadata script if it exists
        metadata_script_path = "/app/create_metadata_table.py"
        if os.path.exists("/Users/kg/aquascene-content-engine/create_metadata_table.py"):
            import shutil
            shutil.copy2("/Users/kg/aquascene-content-engine/create_metadata_table.py", metadata_script_path)
        
        result = subprocess.run(
            ["python3", script_path],
            capture_output=True,
            text=True,
            timeout=60,
            cwd="/app"
        )
        
        os.unlink(script_path)
        
        if result.returncode == 0:
            last_line = result.stdout.strip().split('\n')[-1]
            if last_line.startswith("SUCCESS:"):
                files = last_line.replace("SUCCESS:", "").split(",")
                return {
                    "success": True,
                    "instructions_file": files[0] if len(files) > 0 else None,
                    "structure_file": files[1] if len(files) > 1 else None,
                    "records_file": files[2] if len(files) > 2 else None
                }
        
        return {
            "success": False,
            "error": result.stderr or result.stdout or "Metadata creation failed"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/download/{workflow_id}/{file_type}")
async def download_workflow_file(workflow_id: str, file_type: str):
    """Download workflow result files"""
    if workflow_id not in workflow_executions:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    status = workflow_executions[workflow_id]
    if not status.results:
        raise HTTPException(status_code=404, detail="No results available")
    
    file_path = status.results.get(f"{file_type}_file")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename=os.path.basename(file_path),
        media_type='application/octet-stream'
    )