import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

class Visualizer:
    """Creates interactive visualizations for the dashboard"""
    
    def __init__(self):
        self.color_palette = px.colors.qualitative.Set3
    
    def create_vessel_performance_chart(self, vessel_data):
        """Create vessel performance bar chart"""
        if vessel_data.empty:
            return self._create_empty_chart("No vessel data available")
        
        fig = px.bar(
            vessel_data.reset_index(),
            x='Vessel',
            y='Completion_Rate_%',
            title='Vessel Performance - E-Form Completion Rates',
            labels={'Completion_Rate_%': 'Completion Rate (%)', 'Vessel': 'Vessel'},
            color='Completion_Rate_%',
            color_continuous_scale='Viridis'
        )
        
        fig.update_layout(
            xaxis_tickangle=-45,
            height=500,
            showlegend=False
        )
        
        return fig
    
    def create_vessel_distribution_chart(self, vessel_data):
        """Create vessel distribution pie chart"""
        if vessel_data.empty:
            return self._create_empty_chart("No vessel data available")
        
        fig = px.pie(
            vessel_data.reset_index(),
            values='Total_Records',
            names='Vessel',
            title='Distribution of Records by Vessel'
        )
        
        fig.update_layout(height=500)
        return fig
    
    def create_job_performance_chart(self, job_data):
        """Create job performance bar chart"""
        if job_data.empty:
            return self._create_empty_chart("No job data available")
