import pandas as pd
import numpy as np
from datetime import datetime

class DataProcessor:
    """Handles data processing and analysis operations"""
    
    def __init__(self, data, config):
        self.data = data.copy()
        self.config = config
        self._preprocess_data()
    
    def _preprocess_data(self):
        """Preprocess the data for analysis"""
        # Ensure required columns exist
        required_cols = [self.config['vessel_col'], self.config['job_col'], self.config['eform_col']]
        missing_cols = [col for col in required_cols if col not in self.data.columns]
        
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        # Clean string columns
        for col in [self.config['vessel_col'], self.config['job_col']]:
            if col in self.data.columns:
                self.data[col] = self.data[col].astype(str).str.strip()
                # Replace 'nan' strings with actual NaN
                self.data[col] = self.data[col].replace(['nan', 'NaN', 'None', ''], np.nan)
        
        # Handle numeric columns - try to convert e-form column to numeric if possible
        eform_col = self.config['eform_col']
        if eform_col in self.data.columns:
            # Try to convert to numeric, keeping original if conversion fails
            numeric_series = pd.to_numeric(self.data[eform_col], errors='coerce')
            if not numeric_series.isna().all():
                self.data[f'{eform_col}_numeric'] = numeric_series
        
        # Add derived columns
        self.data['record_id'] = range(1, len(self.data) + 1)
        
        # Handle date columns if any exist
        date_columns = self.data.select_dtypes(include=['datetime64', 'object']).columns
        for col in date_columns:
            if col not in required_cols:  # Don't convert our key columns
                try:
                    self.data[f'{col}_date'] = pd.to_datetime(self.data[col], errors='coerce', dayfirst=True, format='mixed')
                except:
                    pass
    
    def get_data(self):
        """Return the processed data"""
        return self.data
    
    def get_config(self):
        """Return the configuration"""
        return self.config
    
    def get_vessel_summary(self):
        """Generate vessel-based summary statistics"""
        vessel_col = self.config['vessel_col']
        eform_col = self.config['eform_col']
        
        # Group by vessel
        vessel_groups = self.data.groupby(vessel_col)
        
        summary_data = []
        for vessel, group in vessel_groups:
            if pd.isna(vessel):
                vessel = "Unknown"
            
            # Basic statistics
            record_count = len(group)
            eform_completion = group[eform_col].notna().sum()
            completion_rate = (eform_completion / record_count) * 100 if record_count > 0 else 0
            
            # Job diversity
            unique_jobs = group[self.config['job_col']].nunique()
            
            # E-form statistics
            eform_stats = self._calculate_eform_stats(group[eform_col])
            
            summary_data.append({
                'Vessel': vessel,
                'Total_Records': record_count,
                'EForm_Completed': eform_completion,
                'Completion_Rate_%': round(completion_rate, 2),
                'Unique_Jobs': unique_jobs,
                'EForm_Unique_Values': eform_stats['unique_count'],
                'EForm_Most_Common': eform_stats['most_common'],
                'Data_Quality_Score': eform_stats['quality_score']
            })
        
        df = pd.DataFrame(summary_data)
        return df.set_index('Vessel') if not df.empty else pd.DataFrame()
    
    def get_job_summary(self):
        """Generate job-based summary statistics"""
        job_col = self.config['job_col']
        eform_col = self.config['eform_col']
        
        # Group by job
        job_groups = self.data.groupby(job_col)
        
        summary_data = []
        for job, group in job_groups:
            if pd.isna(job):
                job = "Unknown"
            
            # Basic statistics
            record_count = len(group)
            eform_completion = group[eform_col].notna().sum()
            completion_rate = (eform_completion / record_count) * 100 if record_count > 0 else 0
            
            # Vessel diversity
            unique_vessels = group[self.config['vessel_col']].nunique()
            
            # E-form statistics
            eform_stats = self._calculate_eform_stats(group[eform_col])
            
            summary_data.append({
                'Job': job,
                'Total_Records': record_count,
                'EForm_Completed': eform_completion,
                'Completion_Rate_%': round(completion_rate, 2),
                'Unique_Vessels': unique_vessels,
                'EForm_Unique_Values': eform_stats['unique_count'],
                'EForm_Most_Common': eform_stats['most_common'],
                'Avg_Records_Per_Vessel': round(record_count / unique_vessels, 2) if unique_vessels > 0 else 0
            })
        
        df = pd.DataFrame(summary_data)
        return df.set_index('Job') if not df.empty else pd.DataFrame()
    
    def get_cross_analysis(self):
        """Generate cross-analysis between vessels and jobs"""
        vessel_col = self.config['vessel_col']
        job_col = self.config['job_col']
        eform_col = self.config['eform_col']
        
        # Create pivot table for cross-analysis
        try:
            cross_table = pd.crosstab(
                self.data[vessel_col].fillna('Unknown'),
                self.data[job_col].fillna('Unknown'),
                values=self.data[eform_col].notna(),
                aggfunc='sum'
            ).fillna(0)
            
            return cross_table
        except Exception as e:
            # Return empty DataFrame if cross-analysis fails
            return pd.DataFrame()
    
    def filter_by_vessels(self, vessel_list):
        """Filter data by selected vessels"""
        vessel_col = self.config['vessel_col']
        return self.data[self.data[vessel_col].isin(vessel_list)]
    
    def filter_by_jobs(self, job_list):
        """Filter data by selected jobs"""
        job_col = self.config['job_col']
        return self.data[self.data[job_col].isin(job_list)]
    
    def _calculate_eform_stats(self, series):
        """Calculate statistics for e-form column"""
        stats = {
            'unique_count': series.nunique(),
            'most_common': 'N/A',
            'quality_score': 0
        }
        
        # Most common value
        if not series.empty and series.notna().any():
            value_counts = series.value_counts()
            if not value_counts.empty:
                stats['most_common'] = str(value_counts.index[0])
        
        # Quality score based on completion rate
        if len(series) > 0:
            completion_rate = series.notna().sum() / len(series)
            stats['quality_score'] = round(completion_rate * 100, 1)
        
        return stats
    
    def get_column_info(self):
        """Get information about all columns in the dataset"""
        info = []
        for col in self.data.columns:
            col_info = {
                'Column': col,
                'Type': str(self.data[col].dtype),
                'Non_Null_Count': self.data[col].notna().sum(),
                'Null_Count': self.data[col].isna().sum(),
                'Unique_Values': self.data[col].nunique()
            }
            
            if self.data[col].dtype in ['int64', 'float64']:
                col_info.update({
                    'Mean': round(self.data[col].mean(), 2) if self.data[col].notna().any() else 'N/A',
                    'Min': self.data[col].min() if self.data[col].notna().any() else 'N/A',
                    'Max': self.data[col].max() if self.data[col].notna().any() else 'N/A'
                })
            
            info.append(col_info)
        
        return pd.DataFrame(info)
