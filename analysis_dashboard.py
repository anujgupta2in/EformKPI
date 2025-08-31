import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime
import io
import base64

class AnalysisDashboard:
    """Main dashboard component for displaying analysis results"""
    
    def __init__(self, data_processor, kpi_calculator, visualizer):
        self.data_processor = data_processor
        self.kpi_calculator = kpi_calculator
        self.visualizer = visualizer
    
    def render(self):
        """Render the simplified analysis dashboard"""
        # Basic data overview
        self._render_basic_overview()
        
        # Vessel filtering
        self._render_vessel_filter()
        
        # Unique vessels list
        self._render_unique_vessels()
        
        # Unique E-forms with frequency
        self._render_eforms_with_frequency()
        
        # Job codes and titles with E-forms
        self._render_jobs_with_eforms()
    
    def _render_basic_overview(self):
        """Render basic data overview"""
        st.header("📋 E-Form Data Analysis")
        
        data = self.data_processor.get_data()
        config = self.data_processor.get_config()
        
        # Apply current filters to get filtered data for KPIs
        filtered_data = self._apply_vessel_filter(data, config)
        
        # Check if fleet data is available
        has_fleet_data = 'Management Unit' in data.columns and 'Fleet Name' in data.columns
        
        if has_fleet_data:
            # Show all KPIs when fleet data is available
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("Total Records", len(filtered_data))
            
            with col2:
                unique_vessels = filtered_data[config['vessel_col']].nunique()
                st.metric("Unique Vessels", unique_vessels)
            
            with col3:
                unique_eforms = filtered_data[config['eform_col']].dropna().nunique()
                st.metric("Unique E-Forms", unique_eforms)
            
            with col4:
                unique_mgmt_units = filtered_data['Management Unit'].nunique()
                st.metric("Unique Management Units", unique_mgmt_units)
            
            with col5:
                unique_fleet_names = filtered_data['Fleet Name'].nunique()
                st.metric("Unique Fleet Names", unique_fleet_names)
        else:
            # Show only basic KPIs when fleet data is not available
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Records", len(filtered_data))
            
            with col2:
                unique_vessels = filtered_data[config['vessel_col']].nunique()
                st.metric("Unique Vessels", unique_vessels)
            
            with col3:
                unique_eforms = filtered_data[config['eform_col']].dropna().nunique()
                st.metric("Unique E-Forms", unique_eforms)
    
    def _render_vessel_filter(self):
        """Render filtering section - shows fleet filters only if fleet data is loaded"""
        data = self.data_processor.get_data()
        config = self.data_processor.get_config()
        
        st.header("🔍 Filter Options")
        
        # Check if fleet data is available
        has_fleet_data = 'Management Unit' in data.columns and 'Fleet Name' in data.columns
        
        if has_fleet_data:
            # Show hierarchical filtering when fleet data is available
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.subheader("🏢 Management Unit")
                management_units = sorted(data['Management Unit'].dropna().unique())
                selected_mgmt_units = st.multiselect(
                    "Select Management Units:",
                    options=["All"] + management_units,
                    default=["All"],
                    help="First level filter - Management Units",
                    key="mgmt_unit_filter"
                )
                
                # Filter data based on management unit selection
                if 'All' not in selected_mgmt_units:
                    filtered_data = data[data['Management Unit'].isin(selected_mgmt_units)]
                else:
                    filtered_data = data
            
            with col2:
                st.subheader("⛵ Fleet Name")
                available_fleet_names = sorted(filtered_data['Fleet Name'].dropna().unique())
                selected_fleet_names = st.multiselect(
                    "Select Fleet Names:",
                    options=["All"] + available_fleet_names,
                    default=["All"],
                    help="Second level filter - Fleet Names",
                    key="fleet_name_filter"
                )
                
                # Further filter data based on fleet name selection
                if 'All' not in selected_fleet_names:
                    filtered_data = filtered_data[filtered_data['Fleet Name'].isin(selected_fleet_names)]
            
            with col3:
                st.subheader("🚢 Vessel")
                vessel_col = config['vessel_col']
                available_vessels = sorted(filtered_data[vessel_col].dropna().unique())
                selected_vessels = st.multiselect(
                    "Select Vessels:",
                    options=["All"] + available_vessels,
                    default=["All"],
                    help="Third level filter - Individual vessels",
                    key="vessel_filter"
                )
        else:
            # Show only vessel filter when fleet data is not available
            st.subheader("🚢 Vessel")
            vessel_col = config['vessel_col']
            available_vessels = sorted(data[vessel_col].dropna().unique())
            selected_vessels = st.multiselect(
                "Select Vessels:",
                options=["All"] + available_vessels,
                default=["All"],
                help="Filter by individual vessels",
                key="vessel_filter"
            )
            filtered_data = data
        
        # Additional filters row
        st.write("---")
        col4, col5 = st.columns(2)
        
        with col4:
            st.subheader("📝 E-Form Name")
            eform_col = config['eform_col']
            available_eforms = sorted(filtered_data[eform_col].dropna().unique())
            selected_eforms = st.multiselect(
                "Select E-Forms:",
                options=["All"] + available_eforms,
                default=["All"],
                help="Filter by specific E-Forms",
                key="eform_filter"
            )
        
        with col5:
            st.subheader("💼 Job Code")
            job_col = config['job_col']
            available_jobs = sorted(filtered_data[job_col].dropna().unique())
            selected_jobs = st.multiselect(
                "Select Job Codes:",
                options=["All"] + available_jobs,
                default=["All"],
                help="Filter by specific Job Codes",
                key="job_filter"
            )
    
    def _render_unique_vessels(self):
        """Render unique vessels list"""
        st.header("🚢 Unique Vessels List")
        
        data = self.data_processor.get_data()
        config = self.data_processor.get_config()
        
        # Apply vessel filter if exists
        filtered_data = self._apply_vessel_filter(data, config)
        
        # Check if fleet data is available
        has_fleet_data = 'Management Unit' in data.columns and 'Fleet Name' in data.columns
        
        # Get unique vessels with counts and management/fleet information only if fleet data is loaded
        group_columns = [config['vessel_col']]
        column_names = ['Vessel Name']
        
        if has_fleet_data and 'Management Unit' in filtered_data.columns:
            group_columns.append('Management Unit')
            column_names.append('Management Unit')
        
        if has_fleet_data and 'Fleet Name' in filtered_data.columns:
            group_columns.append('Fleet Name')
            column_names.append('Fleet Name')
        
        if len(group_columns) > 1:
            vessel_summary = filtered_data.groupby(group_columns).size().reset_index(name='Total Records')
            vessel_summary.columns = column_names + ['Total Records']
        else:
            vessel_summary = filtered_data[config['vessel_col']].value_counts().reset_index()
            vessel_summary.columns = ['Vessel Name', 'Total Records']
        
        st.dataframe(vessel_summary, use_container_width=True, hide_index=True)
    
    def _render_eforms_with_frequency(self):
        """Render unique E-forms with frequency"""
        st.header("📝 E-Forms with Frequency")
        
        data = self.data_processor.get_data()
        config = self.data_processor.get_config()
        
        # Apply vessel filter if exists
        filtered_data = self._apply_vessel_filter(data, config)
        
        # Get E-forms with frequency and record count only
        eform_data = filtered_data[['E-Form', 'Frequency']].dropna(subset=['E-Form'])
        
        if not eform_data.empty:
            # Group by E-Form and get frequency information
            eform_summary = eform_data.groupby('E-Form').agg({
                'Frequency': lambda x: x.mode().iloc[0] if not x.mode().empty else 'Unknown'
            }).reset_index()
            
            # Add count of records for each E-form
            eform_counts = filtered_data['E-Form'].value_counts().reset_index()
            eform_counts.columns = ['E-Form', 'Record_Count']
            
            # Merge the data
            final_eforms = eform_summary.merge(eform_counts, on='E-Form', how='left')
            final_eforms = final_eforms.sort_values('Record_Count', ascending=False)
            
            # Reorder columns to show E-Form, Frequency, Record_Count
            final_eforms = final_eforms[['E-Form', 'Frequency', 'Record_Count']]
            
            st.dataframe(final_eforms, use_container_width=True, hide_index=True)
        else:
            st.warning("No E-form data available for the selected filters.")
    
    def _render_jobs_with_eforms(self):
        """Render Job codes and titles where E-form exists"""
        st.header("💼 Jobs with E-Forms")
        
        data = self.data_processor.get_data()
        config = self.data_processor.get_config()
        
        # Apply vessel filter if exists
        filtered_data = self._apply_vessel_filter(data, config)
        
        # Filter only records that have E-forms
        jobs_with_eforms = filtered_data[filtered_data['E-Form'].notna()]
        
        if not jobs_with_eforms.empty:
            # Check if fleet data is available
            has_fleet_data = 'Management Unit' in data.columns and 'Fleet Name' in data.columns
            
            # Select relevant columns including vessel name and management/fleet-related columns only if fleet data is loaded
            job_columns = ['Job Code', 'Title', 'E-Form', 'Frequency', config['vessel_col']]
            if has_fleet_data and 'Management Unit' in jobs_with_eforms.columns:
                job_columns.append('Management Unit')
            if has_fleet_data and 'Fleet Name' in jobs_with_eforms.columns:
                job_columns.append('Fleet Name')
            
            available_columns = [col for col in job_columns if col in jobs_with_eforms.columns]
            
            job_display = jobs_with_eforms[available_columns].drop_duplicates()
            job_display = job_display.sort_values('Job Code' if 'Job Code' in available_columns else available_columns[0])
            
            st.dataframe(job_display, use_container_width=True, hide_index=True)
            
            # Summary statistics
            metrics_count = 2  # Base metrics: Total Jobs and Unique E-Forms
            if 'Management Unit' in job_display.columns:
                metrics_count += 1
            if 'Fleet Name' in job_display.columns:
                metrics_count += 1
            
            if metrics_count == 2:
                col1, col2 = st.columns(2)
            elif metrics_count == 3:
                col1, col2, col3 = st.columns(3)
            else:
                col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Jobs with E-Forms", len(job_display))
            with col2:
                unique_eforms_in_jobs = job_display['E-Form'].nunique() if 'E-Form' in job_display.columns else 0
                st.metric("Unique E-Forms in Jobs", unique_eforms_in_jobs)
            
            if 'Management Unit' in job_display.columns:
                with col3:
                    unique_mgmt_units = job_display['Management Unit'].nunique()
                    st.metric("Unique Management Units", unique_mgmt_units)
            
            if 'Fleet Name' in job_display.columns:
                with col4 if metrics_count >= 4 else col3:
                    unique_fleet_names = job_display['Fleet Name'].nunique()
                    st.metric("Unique Fleet Names", unique_fleet_names)
        else:
            st.warning("No jobs with E-forms found for the selected filters.")
    
    def _apply_vessel_filter(self, data, config):
        """Apply all filters: management unit, fleet name, vessel, e-form, and job filters based on session state"""
        filtered_data = data.copy()
        
        # Apply management unit filter if column exists
        if ('Management Unit' in filtered_data.columns and 
            'mgmt_unit_filter' in st.session_state and 
            'All' not in st.session_state.mgmt_unit_filter):
            filtered_data = filtered_data[filtered_data['Management Unit'].isin(st.session_state.mgmt_unit_filter)]
        
        # Apply fleet name filter if column exists
        if ('Fleet Name' in filtered_data.columns and 
            'fleet_name_filter' in st.session_state and 
            'All' not in st.session_state.fleet_name_filter):
            filtered_data = filtered_data[filtered_data['Fleet Name'].isin(st.session_state.fleet_name_filter)]
        
        # Apply vessel filter
        if 'vessel_filter' in st.session_state and 'All' not in st.session_state.vessel_filter:
            vessel_col = config['vessel_col']
            filtered_data = filtered_data[filtered_data[vessel_col].isin(st.session_state.vessel_filter)]
        
        # Apply e-form filter
        if 'eform_filter' in st.session_state and 'All' not in st.session_state.eform_filter:
            eform_col = config['eform_col']
            filtered_data = filtered_data[filtered_data[eform_col].isin(st.session_state.eform_filter)]
        
        # Apply job filter
        if 'job_filter' in st.session_state and 'All' not in st.session_state.job_filter:
            job_col = config['job_col']
            filtered_data = filtered_data[filtered_data[job_col].isin(st.session_state.job_filter)]
        
        return filtered_data
