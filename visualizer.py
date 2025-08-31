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
        
        fig = px.bar(
            job_data.reset_index(),
            x='Job',
            y='Completion_Rate_%',
            title='Job Performance - E-Form Completion Rates',
            labels={'Completion_Rate_%': 'Completion Rate (%)', 'Job': 'Job Type'},
            color='Total_Records',
            color_continuous_scale='Blues'
        )
        
        fig.update_layout(
            xaxis_tickangle=-45,
            height=500
        )
        
        return fig
    
    def create_job_trend_chart(self, job_data):
        """Create job efficiency scatter plot"""
        if job_data.empty:
            return self._create_empty_chart("No job data available")
        
        fig = px.scatter(
            job_data.reset_index(),
            x='Total_Records',
            y='Completion_Rate_%',
            size='Unique_Vessels',
            hover_name='Job',
            title='Job Efficiency Analysis',
            labels={
                'Total_Records': 'Total Records',
                'Completion_Rate_%': 'Completion Rate (%)',
                'Unique_Vessels': 'Number of Vessels'
            }
        )
        
        fig.update_layout(height=500)
        return fig
    
    def create_eform_distribution_chart(self):
        """Create e-form value distribution chart"""
        from utils.data_processor import DataProcessor
        import streamlit as st
        
        # Get data from session state
        if 'data' not in st.session_state or st.session_state.data is None:
            return self._create_empty_chart("No data available")
        
        data = st.session_state.data
        config = st.session_state.config
        eform_col = config['eform_col']
        
        # Get value counts for e-form column
        value_counts = data[eform_col].value_counts().head(20)  # Top 20 values
        
        if value_counts.empty:
            return self._create_empty_chart("No e-form data available")
        
        fig = px.bar(
            x=value_counts.index.astype(str),
            y=value_counts.values,
            title='E-Form Value Distribution (Top 20)',
            labels={'x': 'E-Form Values', 'y': 'Frequency'}
        )
        
        fig.update_layout(
            xaxis_tickangle=-45,
            height=500
        )
        
        return fig
    
    def create_heatmap(self, cross_analysis_data):
        """Create heatmap for cross-analysis"""
        if cross_analysis_data.empty:
            return self._create_empty_chart("No cross-analysis data available")
        
        fig = px.imshow(
            cross_analysis_data,
            title='Vessel vs Job Cross-Analysis Heatmap',
            labels=dict(x="Job Type", y="Vessel", color="Completed E-Forms"),
            aspect="auto"
        )
        
        fig.update_layout(height=600)
        return fig
    
    def create_kpi_gauge(self, value, title, max_value=100):
        """Create a gauge chart for KPI display"""
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = value,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': title},
            gauge = {
                'axis': {'range': [None, max_value]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, max_value*0.5], 'color': "lightgray"},
                    {'range': [max_value*0.5, max_value*0.8], 'color': "gray"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': max_value*0.9
                }
            }
        ))
        
        fig.update_layout(height=300)
        return fig
    
    def create_trend_chart(self, trend_data):
        """Create trend analysis chart"""
        if trend_data is None or trend_data.empty:
            return self._create_empty_chart("No trend data available")
        
        fig = go.Figure()
        
        # Add completion rate line
        fig.add_trace(go.Scatter(
            x=trend_data.index.astype(str),
            y=trend_data['Completion_Rate'],
            mode='lines+markers',
            name='Completion Rate (%)',
            line=dict(color='blue', width=3)
        ))
        
        # Add total records bar
        fig.add_trace(go.Bar(
            x=trend_data.index.astype(str),
            y=trend_data['Total_Records'],
            name='Total Records',
            opacity=0.6,
            yaxis='y2'
        ))
        
        # Update layout for dual y-axis
        fig.update_layout(
            title='E-Form Completion Trends Over Time',
            xaxis_title='Time Period',
            yaxis=dict(
                title='Completion Rate (%)',
                side='left'
            ),
            yaxis2=dict(
                title='Total Records',
                side='right',
                overlaying='y'
            ),
            height=500,
            legend=dict(x=0.01, y=0.99)
        )
        
        return fig
    
    def create_comparison_chart(self, data, x_col, y_col, color_col, title):
        """Create a generic comparison chart"""
        if data.empty:
            return self._create_empty_chart(f"No data available for {title}")
        
        fig = px.scatter(
            data,
            x=x_col,
            y=y_col,
            color=color_col,
            title=title,
            hover_data=data.columns.tolist()
        )
        
        fig.update_layout(height=500)
        return fig
    
    def create_multi_metric_chart(self, data, metrics, title):
        """Create a multi-metric comparison chart"""
        if data.empty:
            return self._create_empty_chart(f"No data available for {title}")
        
        fig = make_subplots(
            rows=len(metrics),
            cols=1,
            subplot_titles=metrics,
            vertical_spacing=0.08
        )
        
        for i, metric in enumerate(metrics):
            if metric in data.columns:
                fig.add_trace(
                    go.Bar(
                        x=data.index,
                        y=data[metric],
                        name=metric,
                        showlegend=False
                    ),
                    row=i+1,
                    col=1
                )
        
        fig.update_layout(
            height=200 * len(metrics),
            title_text=title
        )
        
        return fig
    
    def _create_empty_chart(self, message):
        """Create an empty chart with a message"""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font=dict(size=16)
        )
        fig.update_layout(
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False, showticklabels=False),
            height=400
        )
        return fig
