## Importing libraries and files
from crewai import Task
from agents import doctor, verifier, nutritionist, exercise_specialist
from tools import search_tool, BloodTestReportTool, NutritionTool, ExerciseTool

## Creating a task to help solve user's query
help_patients = Task(
    description="""Analyze the uploaded blood test report and provide comprehensive medical insights for the user's query: {query}
    
    Instructions:
    1. First, read and analyze the blood test report thoroughly
    2. Identify key blood markers and their values
    3. Compare values against normal reference ranges
    4. Highlight any abnormal findings that require attention
    5. Provide evidence-based explanations for what the results mean
    6. Offer preliminary recommendations while emphasizing the need for professional medical consultation
    7. Use clear, patient-friendly language while maintaining medical accuracy
    
    Focus on providing accurate, helpful information that empowers the patient while being clear about the limitations of AI analysis.""",

    expected_output="""A comprehensive blood test analysis report containing:
    
    1. **Executive Summary**: Brief overview of overall health status based on blood work
    
    2. **Key Findings**: 
       - Normal values and what they indicate
       - Abnormal values and their potential significance
       - Any concerning patterns or trends
    
    3. **Detailed Analysis**:
       - Explanation of major blood markers
       - Clinical significance of the results
       - Potential health implications
    
    4. **Recommendations**:
       - Lifestyle modifications if indicated
       - Follow-up testing suggestions
       - When to consult healthcare providers
    
    5. **Important Disclaimers**:
       - This analysis is for informational purposes only
       - Always consult with qualified healthcare professionals
       - Emergency situations require immediate medical attention
    
    Format: Well-structured report with clear headings and bullet points where appropriate.""",

    agent=doctor,
    tools=[BloodTestReportTool()],
    async_execution=False,
)

## Creating a verification task
verification_task = Task(
    description="""Verify that the uploaded document is a valid blood test report containing analyzable medical data.
    
    Instructions:
    1. Read the uploaded document thoroughly
    2. Check if it contains blood test results with numerical values
    3. Verify the presence of standard blood markers (CBC, metabolic panel, etc.)
    4. Ensure the document has proper medical formatting
    5. Identify any issues with document quality or completeness
    
    If the document is not a blood test report, clearly state what type of document it appears to be.""",

    expected_output="""Document verification report containing:
    
    1. **Document Type**: Confirmed blood test report or other document type
    2. **Content Quality**: Assessment of document readability and completeness  
    3. **Available Markers**: List of blood test parameters found in the document
    4. **Data Integrity**: Any issues with values, formatting, or missing information
    5. **Recommendation**: Whether the document is suitable for medical analysis
    
    Format: Clear verification status with supporting details.""",

    agent=verifier,
    tools=[BloodTestReportTool()],
    async_execution=False,
)

## Creating a nutrition analysis task
nutrition_analysis = Task(
    description="""Analyze the blood test results to provide evidence-based nutritional recommendations.
    
    User query: {query}
    
    Instructions:
    1. Review blood markers relevant to nutritional status
    2. Identify potential nutritional deficiencies or excesses
    3. Provide dietary recommendations based on scientific evidence
    4. Suggest foods that may help optimize the identified markers
    5. Recommend appropriate nutritional supplements only when clearly indicated
    6. Consider interactions between different nutrients and blood markers""",

    expected_output="""Comprehensive nutritional analysis including:
    
    1. **Nutritional Blood Markers Review**:
       - Vitamin levels (D, B12, folate, etc.)
       - Mineral status (iron, magnesium, etc.)
       - Metabolic markers (glucose, lipids)
    
    2. **Dietary Recommendations**:
       - Foods to emphasize for optimal health
       - Foods to limit based on results
       - Meal planning suggestions
    
    3. **Supplement Guidance**:
       - Evidence-based supplement recommendations
       - Dosage guidelines when appropriate
       - Potential interactions to consider
    
    4. **Lifestyle Integration**:
       - Practical tips for dietary changes
       - Timeline for reassessment
    
    Format: Actionable nutritional guidance with scientific rationale.""",

    agent=nutritionist,
    tools=[BloodTestReportTool(), NutritionTool()],
    async_execution=False,
)

## Creating an exercise planning task
exercise_planning = Task(
    description="""Develop a safe, personalized exercise plan based on blood test results and health status.
    
    User query: {query}
    
    Instructions:
    1. Analyze blood markers relevant to exercise capacity and safety
    2. Consider cardiovascular health indicators
    3. Assess metabolic markers that affect exercise response
    4. Provide exercise recommendations appropriate for the individual's health status
    5. Include safety considerations and contraindications
    6. Suggest monitoring parameters during exercise""",

    expected_output="""Personalized exercise plan including:
    
    1. **Health Status Assessment**:
       - Cardiovascular fitness indicators from blood work
       - Metabolic health markers
       - Any exercise-related considerations
    
    2. **Exercise Recommendations**:
       - Appropriate exercise types and intensity
       - Frequency and duration guidelines
       - Progression strategies
    
    3. **Safety Considerations**:
       - Medical clearance requirements
       - Warning signs to monitor
       - Modifications for health conditions
    
    4. **Monitoring Guidelines**:
       - Parameters to track during exercise
       - When to reassess and adjust the plan
    
    Format: Safe, evidence-based exercise prescription with clear implementation steps.""",

    agent=exercise_specialist,
    tools=[BloodTestReportTool(), ExerciseTool()],
    async_execution=False,
)