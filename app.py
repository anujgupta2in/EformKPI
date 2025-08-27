import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime
import io
import base64

# Import custom modules
from file_handler import FileHandler
from analysis_dashboard import AnalysisDashboard
from data_processor import DataProcessor
from kpi_calculator import KPICalculator
from visualizer import Visualizer

# Page configuration
st.set_page_config(
    page_title="E-Form Data Analysis Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.title("📊 E-Form Data Analysis Dashboard")
    st.markdown("Upload Excel or CSV files to analyze e-form data with vessel and job-based KPIs")
    
    # Initialize session state
    if 'data' not in st.session_state:
        st.session_state.data = None
    if 'analysis_complete' not in st.session_state:
        st.session_state.analysis_complete = False
    
    # Sidebar for file upload and configuration
    with st.sidebar:
        st.header("📁 File Upload")
        
        # E-form file upload
        st.subheader("📊 E-Form Data")
        file_handler = FileHandler()
        uploaded_file = st.file_uploader(
            "Choose E-Form file",
            type=['csv', 'xlsx', 'xls'],
            help="Upload Excel (.xlsx, .xls) or CSV files with E-form data",
            key="eform_file"
        )
        
        # Fleet file upload
        st.subheader("⚓ Fleet Data")
        fleet_file = st.file_uploader(
            "Choose Fleet file (optional)",
            type=['csv', 'xlsx', 'xls'],
            help="Upload Excel (.xlsx, .xls) or CSV files with fleet data. If not provided, default fleet data will be used.",
            key="fleet_file"
        )
        
        # Store fleet file in session state with a different key
        if fleet_file is not None:
            st.session_state.uploaded_fleet_file = fleet_file
        elif 'uploaded_fleet_file' not in st.session_state:
            st.session_state.uploaded_fleet_file = None
        
        if uploaded_file is not None:
            try:
                with st.spinner("Loading and processing file..."):
                    data = file_handler.process_file(uploaded_file)
                    if data is not None and not data.empty:
                        st.session_state.data = data
                        st.session_state.analysis_complete = True
                        
                        # Auto-detect and set configuration
                        columns = data.columns.tolist()
                        
                        # Auto-detect potential vessel and job columns
                        vessel_candidates = [col for col in columns if any(keyword in col.lower() for keyword in ['vessel', 'ship', 'boat'])]
                        job_candidates = [col for col in columns if any(keyword in col.lower() for keyword in ['job', 'work', 'task', 'project', 'code'])]
                        
                        # Store configuration in session state with auto-detected values
                        st.session_state.config = {
                            'vessel_col': vessel_candidates[0] if vessel_candidates else columns[0],
                            'job_col': job_candidates[0] if job_candidates else (columns[1] if len(columns) > 1 else columns[0]),
                            'eform_col': 'E-Form'  # Fixed to use exact column name
                        }
                        
                        st.success(f"✅ File loaded successfully! ({len(data)} rows, {len(data.columns)} columns)")
                    else:
                        st.error("❌ Failed to load file or file is empty")
            except Exception as e:
                st.error(f"❌ Error processing file: {str(e)}")
    
    # Main dashboard
    if st.session_state.analysis_complete and st.session_state.data is not None:
        config = st.session_state.config
        data = st.session_state.data
        
        # Initialize components
        data_processor = DataProcessor(data, config)
        kpi_calculator = KPICalculator(data_processor)
        visualizer = Visualizer()
        dashboard = AnalysisDashboard(data_processor, kpi_calculator, visualizer)
        
        # Display dashboard
        dashboard.render()
        
    else:
        # Welcome screen
        st.markdown("""
        ## Welcome to the E-Form Data Analysis Dashboard
        
        This application helps you analyze e-form data with comprehensive KPIs based on vessels and jobs.
        
        ### Features:
        - 📊 **Interactive KPI Dashboard** - Real-time metrics and insights
        - 🚢 **Vessel-based Analysis** - Performance metrics by vessel
        - 💼 **Job-based Analysis** - Efficiency tracking by job type
        - 📈 **Advanced Visualizations** - Charts, graphs, and trend analysis
        - 🔍 **Hierarchical Filtering** - Filter by Management Unit → Fleet Name → Vessel
        - ⚓ **Fleet Integration** - Automatic fleet data merging and analysis
        
        ### Supported File Formats:
        - Excel files (.xlsx, .xls)
        - CSV files (.csv)
        
        ### Getting Started:
        1. Upload your E-form data file using the sidebar
        2. Optionally upload a fleet data file for enhanced analysis
        3. Explore the interactive dashboard with hierarchical filtering
        4. Analyze vessel performance, E-forms, and job distributions
        
        **Upload a file to begin your analysis!**
        """)

if __name__ == "__main__":
    main()
