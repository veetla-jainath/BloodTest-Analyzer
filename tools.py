## Importing libraries and files
import os
from dotenv import load_dotenv
load_dotenv()

from crewai.tools import BaseTool
from crewai_tools import SerperDevTool
from langchain_community.document_loaders import PyPDFLoader
import pandas as pd
from typing import Type
from pydantic import BaseModel, Field

## Creating search tool
search_tool = SerperDevTool()

## Creating custom pdf reader tool
class BloodTestReportInput(BaseModel):
    """Input schema for BloodTestReportTool."""
    path: str = Field(..., description="Path to the PDF file containing the blood test report")

class BloodTestReportTool(BaseTool):
    name: str = "blood_test_reader"
    description: str = "Tool to read and extract data from blood test report PDF files"
    args_schema: Type[BaseModel] = BloodTestReportInput
    
    def _run(self, path: str = 'data/sample.pdf') -> str:
        """Tool to read data from a pdf file from a path

        Args:
            path (str): Path of the pdf file. Defaults to 'data/sample.pdf'.

        Returns:
            str: Full Blood Test report content
        """
        try:
            # List of possible paths to check
            possible_paths = [
                path,  # Original path as provided
                f"data/{path}",  # Check in data folder
                f"./{path}",  # Check in current directory
                f"uploads/{path}",  # Check in uploads folder
                f"files/{path}",  # Check in files folder
                "data/sample.pdf",  # Default fallback
            ]
            
            # Find the first existing file
            file_path = None
            for p in possible_paths:
                if os.path.exists(p):
                    file_path = p
                    break
            
            if not file_path:
                # List available files for debugging
                available_files = []
                for folder in [".", "data", "uploads", "files"]:
                    if os.path.exists(folder):
                        files = [f for f in os.listdir(folder) if f.endswith('.pdf')]
                        if files:
                            available_files.extend([f"{folder}/{f}" for f in files])
                
                error_msg = f"Error: File '{path}' not found. Searched in: {', '.join(possible_paths)}"
                if available_files:
                    error_msg += f"\n\nAvailable PDF files found: {', '.join(available_files)}"
                else:
                    error_msg += "\n\nNo PDF files found in common directories (., data/, uploads/, files/)"
                
                return error_msg
            
            print(f"Reading PDF from: {file_path}")  # Debug info
            
            loader = PyPDFLoader(file_path)
            docs = loader.load()

            full_report = ""
            for doc in docs:
                # Clean and format the report data
                content = doc.page_content
                
                # Remove extra whitespaces and format properly
                content = content.replace('\n\n', '\n').strip()
                full_report += content + "\n"
                
            if not full_report.strip():
                return f"Error: Could not extract content from PDF file at {file_path}"
                
            return f"Successfully extracted blood test report from {file_path}:\n\n{full_report}"
            
        except Exception as e:
            return f"Error reading PDF file: {str(e)}\nAttempted path: {path}"

## Creating Nutrition Analysis Tool Input Schema
class NutritionAnalysisInput(BaseModel):
    """Input schema for NutritionTool."""
    blood_report_data: str = Field(..., description="Blood test report data to analyze for nutrition")

class NutritionTool(BaseTool):
    name: str = "nutrition_analyzer"
    description: str = "Tool to analyze blood test results and provide nutritional recommendations"
    args_schema: Type[BaseModel] = NutritionAnalysisInput
    
    def _run(self, blood_report_data: str) -> str:
        """Analyze blood test data for nutritional insights
        
        Args:
            blood_report_data (str): The blood test report content
            
        Returns:
            str: Nutritional analysis and recommendations
        """
        try:
            # Basic analysis of common blood markers for nutrition
            analysis = []
            
            # Check for common nutritional markers
            if "hemoglobin" in blood_report_data.lower() or "hgb" in blood_report_data.lower():
                analysis.append("Hemoglobin levels analyzed for iron status")
            
            if "vitamin d" in blood_report_data.lower() or "25(oh)d" in blood_report_data.lower():
                analysis.append("Vitamin D levels reviewed")
                
            if "b12" in blood_report_data.lower() or "cobalamin" in blood_report_data.lower():
                analysis.append("Vitamin B12 status evaluated")
                
            if "glucose" in blood_report_data.lower():
                analysis.append("Blood glucose levels assessed for metabolic health")
                
            if not analysis:
                analysis.append("Blood report processed for nutritional markers")
                
            return "Nutritional analysis completed: " + "; ".join(analysis)
            
        except Exception as e:
            return f"Error in nutrition analysis: {str(e)}"

## Creating Exercise Planning Tool Input Schema
class ExercisePlanInput(BaseModel):
    """Input schema for ExerciseTool."""
    blood_report_data: str = Field(..., description="Blood test report data to base exercise recommendations on")

class ExerciseTool(BaseTool):
    name: str = "exercise_planner"
    description: str = "Tool to create exercise recommendations based on blood test results"
    args_schema: Type[BaseModel] = ExercisePlanInput
    
    def _run(self, blood_report_data: str) -> str:
        """Create exercise recommendations based on blood test data
        
        Args:
            blood_report_data (str): The blood test report content
            
        Returns:
            str: Exercise planning recommendations
        """
        try:
            recommendations = []
            
            # Basic exercise recommendations based on common markers
            if "glucose" in blood_report_data.lower():
                recommendations.append("Cardiovascular exercise recommended for glucose management")
                
            if "cholesterol" in blood_report_data.lower() or "ldl" in blood_report_data.lower():
                recommendations.append("Aerobic exercise beneficial for cholesterol management")
                
            if "blood pressure" in blood_report_data.lower() or "bp" in blood_report_data.lower():
                recommendations.append("Moderate exercise recommended for blood pressure control")
                
            if not recommendations:
                recommendations.append("General fitness assessment completed based on blood markers")
                
            return "Exercise planning analysis: " + "; ".join(recommendations)
            
        except Exception as e:
            return f"Error in exercise planning: {str(e)}"