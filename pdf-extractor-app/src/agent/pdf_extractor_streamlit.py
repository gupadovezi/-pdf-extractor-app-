import streamlit as st
import pandas as pd
from pathlib import Path
import os
from datetime import datetime
from math_example import process_pdf_directory
from ai_processor import AIProcessor

# Set page config
st.set_page_config(
    page_title="AI-Powered PDF Extractor",
    page_icon="📚",
    layout="wide"
)

# Initialize session state
if 'ai_processor' not in st.session_state:
    st.session_state.ai_processor = None

# Title and description
st.title("📚 AI-Powered PDF Extractor")
st.markdown("""
This application helps you extract and analyze information from PDF files using AI.
Upload your PDFs and let the AI process them to extract key information and insights.
""")

# Get API key from secrets
api_key = st.secrets.get("OPENROUTER_API_KEY", "")
if not api_key:
    st.error("OpenRouter API key not found in secrets. Please add it to .streamlit/secrets.toml")
    st.stop()

# Initialize AI processor
try:
    os.environ["OPENROUTER_API_KEY"] = api_key
    st.session_state.ai_processor = AIProcessor()
except Exception as e:
    st.error(f"Error initializing AI processor: {str(e)}")
    st.stop()

# File uploader
uploaded_files = st.file_uploader("Upload PDF files", type=['pdf'], accept_multiple_files=True)

# Output directory selection
output_dir = st.text_input(
    "Output Directory",
    value=str(Path.home() / "Downloads"),
    help="Directory where the Excel file will be saved"
)

if uploaded_files:
    # Create a temporary directory for uploaded files
    temp_dir = Path("temp_uploads")
    temp_dir.mkdir(exist_ok=True)
    
    # Save uploaded files
    for uploaded_file in uploaded_files:
        with open(temp_dir / uploaded_file.name, "wb") as f:
            f.write(uploaded_file.getvalue())
    
    if st.button("Process PDFs"):
        with st.spinner("Processing PDFs..."):
            try:
                # Process PDFs without protocol
                results = process_pdf_directory(str(temp_dir))
                
                if results:
                    # Convert results to DataFrame
                    df = pd.DataFrame(results)
                    
                    # Process with AI
                    st.subheader("AI Analysis")
                    with st.spinner("Analyzing with AI..."):
                        # Process each PDF with AI
                        ai_results = []
                        for _, row in df.iterrows():
                            text = row['text'] if 'text' in row else ""
                            if text:
                                st.write(f"Processing file: {row.get('filename', 'unknown')}")
                                ai_data = st.session_state.ai_processor.process_text(text)
                                if "error" in ai_data:
                                    st.error(f"Error processing file {row.get('filename', 'unknown')}:")
                                    st.error(f"Error details: {ai_data['error']}")
                                    if "raw_response" in ai_data:
                                        with st.expander("View raw response"):
                                            st.code(ai_data['raw_response'])
                                ai_results.append(ai_data)
                        
                        # Analyze findings across all papers
                        if ai_results:
                            analysis = st.session_state.ai_processor.analyze_findings(ai_results)
                            
                            # Display analysis
                            st.markdown("### Research Analysis")
                            if isinstance(analysis['analysis'], dict):
                                for key, value in analysis['analysis'].items():
                                    st.markdown(f"#### {key.replace('_', ' ').title()}")
                                    if isinstance(value, list):
                                        for item in value:
                                            st.markdown(f"- {item}")
                                    else:
                                        st.write(value)
                            else:
                                st.write(analysis['analysis'])
                            
                            # Create AI-enhanced DataFrame
                            ai_df = pd.DataFrame(ai_results)
                            
                            # Save both DataFrames
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            excel_path = Path(output_dir) / f"pdf_extracts_ai_{timestamp}.xlsx"
                            
                            with pd.ExcelWriter(excel_path) as writer:
                                df.to_excel(writer, sheet_name='Raw Data', index=False)
                                ai_df.to_excel(writer, sheet_name='AI Analysis', index=False)
                            
                            st.success(f"Files processed successfully! Saved to: {excel_path}")
                            
                            # Display preview of AI analysis
                            st.subheader("Preview of AI Analysis")
                            st.dataframe(ai_df)
                        else:
                            st.error("No text content found in PDFs for AI analysis")
                else:
                    st.error("No results found from PDF processing")
            except Exception as e:
                st.error(f"Error processing PDFs: {str(e)}")
        
        # Clean up temporary files
        for file in temp_dir.glob("*.pdf"):
            file.unlink()
        temp_dir.rmdir()

# Add information about the app
st.sidebar.markdown("""
### About
This app uses AI to:
- Extract structured information from PDFs
- Analyze research findings
- Identify patterns and insights
- Generate comprehensive reports

### Requirements
- PDF files to analyze
""") 