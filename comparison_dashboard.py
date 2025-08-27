import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime
from data_processor import DataProcessor
from kpi_calculator import KPICalculator
from visualizer import Visualizer

class ComparisonDashboard:
    """Dashboard component for comparing multiple data files"""
    
    def __init__(self, files_data, config):
        self.files_data = files_data
        self.config = config
        self.file_names = list(files_data.keys())
        
        # Initialize processors for each file
        self.processors = {}
        self.kpi_calculators = {}
        for name, data in files_data.items():
            processor = DataProcessor(data, config)
            self.processors[name] = processor
            self.kpi_calculators[name] = KPICalculator(processor)
    
    def render(self):
        """Render the comparison dashboard"""
        st.header("📊 Multi-File Data Comparison")
        
        # File selection for comparison
        self._render_file_selector()
        
        # Comparison overview
        self._render_comparison_overview()
        
        # Detailed comparisons
        self._render_vessel_comparison()
        self._render_eform_comparison()
        self._render_job_comparison()
    
    def _render_file_selector(self):
        """Render file selection interface"""
        st.subheader("📁 Select Files to Compare")
        
        col1, col2 = st.columns(2)
        
        with col1:
            selected_files = st.multiselect(
                "Choose files for comparison:",
                options=self.file_names,
                default=self.file_names[:2] if len(self.file_names) >= 2 else self.file_names,
                help="Select 2 or more files to compare"
            )
        
        with col2:
            if len(selected_files) < 2:
                st.warning("Please select at least 2 files for comparison")
                
        # Store selected files in session state
        st.session_state.selected_comparison_files = selected_files
        
        return selected_files
    
    def _render_comparison_overview(self):
        """Render high-level comparison metrics"""
        if 'selected_comparison_files' not in st.session_state or len(st.session_state.selected_comparison_files) < 2:
            return
        
        st.subheader("📈 Comparison Overview")
        
        selected_files = st.session_state.selected_comparison_files
        
        # Create comparison metrics table
        comparison_data = []
        for file_name in selected_files:
            data = self.files_data[file_name]
            comparison_data.append({
                'File': file_name.split('_', 2)[-1] if '_' in file_name else file_name,  # Clean filename
                'Total Records': len(data),
                'Unique Vessels': data[self.config['vessel_col']].nunique(),
                'Unique E-Forms': data[self.config['eform_col']].nunique(),
                'Unique Jobs': data[self.config['job_col']].nunique() if self.config['job_col'] in data.columns else 0,
                'Management Units': data['Management Unit'].nunique() if 'Management Unit' in data.columns else 0,
                'Fleet Names': data['Fleet Name'].nunique() if 'Fleet Name' in data.columns else 0
            })
        
        comparison_df = pd.DataFrame(comparison_data)
        st.dataframe(comparison_df, use_container_width=True, hide_index=True)
        
        # Visual comparison chart
        self._render_comparison_chart(comparison_df)
    
    def _render_comparison_chart(self, comparison_df):
        """Render visual comparison chart"""
        st.subheader("📊 Visual Comparison")
        
        # Create subplots for different metrics
        metrics = ['Total Records', 'Unique Vessels', 'Unique E-Forms', 'Unique Jobs']
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=metrics,
            specs=[[{"type": "bar"}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "bar"}]]
        )
        
        colors = px.colors.qualitative.Set2
        
        for i, metric in enumerate(metrics):
            row = (i // 2) + 1
            col = (i % 2) + 1
            
            fig.add_trace(
                go.Bar(
                    x=comparison_df['File'],
                    y=comparison_df[metric],
                    name=metric,
                    marker_color=colors[i % len(colors)],
                    showlegend=False
                ),
                row=row, col=col
            )
        
        fig.update_layout(
            height=600,
            title_text="File Comparison Metrics",
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_vessel_comparison(self):
        """Render vessel-based comparison"""
        if 'selected_comparison_files' not in st.session_state or len(st.session_state.selected_comparison_files) < 2:
            return
        
        st.subheader("🚢 Vessel Comparison")
        
        selected_files = st.session_state.selected_comparison_files
        
        # Get top vessels from each file
        vessel_data = {}
        for file_name in selected_files:
            data = self.files_data[file_name]
            vessel_counts = data[self.config['vessel_col']].value_counts().head(10)
            vessel_data[file_name.split('_', 2)[-1] if '_' in file_name else file_name] = vessel_counts
        
        # Create comparison dataframe
        vessel_comparison = pd.DataFrame(vessel_data).fillna(0)
        
        if not vessel_comparison.empty:
            # Show top vessels table
            st.write("**Top 10 Vessels by Record Count:**")
            st.dataframe(vessel_comparison, use_container_width=True, hide_index=True)
            
            # Visualization
            fig = go.Figure()
            for file_name in vessel_comparison.columns:
                fig.add_trace(go.Bar(
                    x=vessel_comparison.index[:5],  # Top 5 for readability
                    y=vessel_comparison[file_name][:5],
                    name=file_name,
                    opacity=0.7
                ))
            
            fig.update_layout(
                title="Top 5 Vessels Comparison",
                xaxis_title="Vessels",
                yaxis_title="Record Count",
                barmode='group'
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    def _render_eform_comparison(self):
        """Render E-form based comparison"""
        if 'selected_comparison_files' not in st.session_state or len(st.session_state.selected_comparison_files) < 2:
            return
        
        st.subheader("📝 E-Form Comparison")
        
        selected_files = st.session_state.selected_comparison_files
        
        # Get E-form data from each file
        eform_data = {}
        for file_name in selected_files:
            data = self.files_data[file_name]
            eform_counts = data[self.config['eform_col']].value_counts().head(10)
            eform_data[file_name.split('_', 2)[-1] if '_' in file_name else file_name] = eform_counts
        
        # Create comparison dataframe
        eform_comparison = pd.DataFrame(eform_data).fillna(0)
        
        if not eform_comparison.empty:
            # Show E-forms table
            st.write("**Top 10 E-Forms by Frequency:**")
            st.dataframe(eform_comparison, use_container_width=True, hide_index=True)
            
            # Find unique E-forms per file
            all_eforms = set()
            file_eforms = {}
            for file_name in selected_files:
                data = self.files_data[file_name]
                eforms = set(data[self.config['eform_col']].dropna().unique())
                file_eforms[file_name.split('_', 2)[-1] if '_' in file_name else file_name] = eforms
                all_eforms.update(eforms)
            
            # Show unique E-forms analysis
            st.write("**E-Form Overlap Analysis:**")
            overlap_data = []
            for file_name, eforms in file_eforms.items():
                overlap_data.append({
                    'File': file_name,
                    'Total E-Forms': len(eforms),
                    'Unique to This File': len(eforms - set().union(*[ef for fn, ef in file_eforms.items() if fn != file_name])),
                    'Common E-Forms': len(eforms.intersection(*[ef for fn, ef in file_eforms.items() if fn != file_name]))
                })
            
            overlap_df = pd.DataFrame(overlap_data)
            st.dataframe(overlap_df, use_container_width=True, hide_index=True)
    
    def _render_job_comparison(self):
        """Render job-based comparison"""
        if 'selected_comparison_files' not in st.session_state or len(st.session_state.selected_comparison_files) < 2:
            return
        
        st.subheader("💼 Job Comparison")
        
        selected_files = st.session_state.selected_comparison_files
        
        # Check if job column exists
        if self.config['job_col'] not in self.files_data[selected_files[0]].columns:
            st.info("Job comparison not available - job column not found in data")
            return
        
        # Get job data from each file
        job_data = {}
        for file_name in selected_files:
            data = self.files_data[file_name]
            if self.config['job_col'] in data.columns:
                job_counts = data[self.config['job_col']].value_counts().head(10)
                job_data[file_name.split('_', 2)[-1] if '_' in file_name else file_name] = job_counts
        
        if job_data:
            # Create comparison dataframe
            job_comparison = pd.DataFrame(job_data).fillna(0)
            
            # Show jobs table
            st.write("**Top 10 Jobs by Frequency:**")
            st.dataframe(job_comparison, use_container_width=True, hide_index=True)
            
            # Show jobs with E-forms comparison
            st.write("**Jobs with E-Forms Comparison:**")
            eform_jobs_data = {}
            for file_name in selected_files:
                data = self.files_data[file_name]
                if self.config['job_col'] in data.columns:
                    jobs_with_eforms = data[data[self.config['eform_col']].notna()][self.config['job_col']].value_counts().head(10)
                    eform_jobs_data[file_name.split('_', 2)[-1] if '_' in file_name else file_name] = jobs_with_eforms
            
            if eform_jobs_data:
                eform_jobs_comparison = pd.DataFrame(eform_jobs_data).fillna(0)
                st.dataframe(eform_jobs_comparison, use_container_width=True, hide_index=True)