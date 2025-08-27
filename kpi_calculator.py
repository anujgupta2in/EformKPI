import pandas as pd
import numpy as np

class KPICalculator:
    """Calculates various KPIs for the e-form analysis"""
    
    def __init__(self, data_processor):
        self.data_processor = data_processor
        self.data = data_processor.get_data()
        self.config = data_processor.get_config()
    
    def calculate_summary_kpis(self):
        """Calculate comprehensive KPIs for vessels, jobs, and e-forms"""
        return {
            'vessel_kpis': self._calculate_vessel_kpis(),
            'job_kpis': self._calculate_job_kpis(),
            'eform_kpis': self._calculate_eform_kpis()
        }
    
    def _calculate_vessel_kpis(self):
        """Calculate vessel-related KPIs"""
        vessel_col = self.config['vessel_col']
        eform_col = self.config['eform_col']
        
        vessel_data = self.data_processor.get_vessel_summary()
        
        if vessel_data.empty:
            return {
                'Total Vessels': 0,
                'Avg Records per Vessel': 0,
                'Best Performing Vessel': 'N/A',
                'Avg Completion Rate': 0
            }
        
        total_vessels = len(vessel_data)
        avg_records = vessel_data['Total_Records'].mean()
        best_vessel = vessel_data['Completion_Rate_%'].idxmax() if not vessel_data.empty else 'N/A'
        avg_completion = vessel_data['Completion_Rate_%'].mean()
        
        return {
            'Total Vessels': total_vessels,
            'Avg Records per Vessel': round(avg_records, 1),
            'Best Performing Vessel': str(best_vessel),
            'Avg Completion Rate': f"{avg_completion:.1f}%"
        }
    
    def _calculate_job_kpis(self):
        """Calculate job-related KPIs"""
        job_col = self.config['job_col']
        eform_col = self.config['eform_col']
        
        job_data = self.data_processor.get_job_summary()
        
        if job_data.empty:
            return {
                'Total Job Types': 0,
                'Avg Records per Job': 0,
                'Most Efficient Job': 'N/A',
                'Job Diversity Score': 0
            }
        
        total_jobs = len(job_data)
        avg_records = job_data['Total_Records'].mean()
        most_efficient = job_data['Completion_Rate_%'].idxmax() if not job_data.empty else 'N/A'
        
        # Job diversity score (based on distribution evenness)
        job_counts = self.data[job_col].value_counts()
        if len(job_counts) > 1:
            # Calculate entropy as diversity measure
            probabilities = job_counts / job_counts.sum()
            entropy = -np.sum(probabilities * np.log2(probabilities))
            max_entropy = np.log2(len(job_counts))
            diversity_score = (entropy / max_entropy) * 100 if max_entropy > 0 else 0
        else:
            diversity_score = 0
        
        return {
            'Total Job Types': total_jobs,
            'Avg Records per Job': round(avg_records, 1),
            'Most Efficient Job': str(most_efficient),
            'Job Diversity Score': f"{diversity_score:.1f}%"
        }
    
    def _calculate_eform_kpis(self):
        """Calculate e-form related KPIs"""
        eform_col = self.config['eform_col']
        eform_data = self.data[eform_col]
        
        total_forms = len(eform_data)
        completed_forms = eform_data.notna().sum()
        completion_rate = (completed_forms / total_forms) * 100 if total_forms > 0 else 0
        unique_values = eform_data.nunique()
        
        # Data quality metrics
        null_count = eform_data.isna().sum()
        duplicate_rate = (len(eform_data) - len(eform_data.drop_duplicates())) / len(eform_data) * 100 if len(eform_data) > 0 else 0
        
        # Consistency score (lower is better for duplicates)
        consistency_score = 100 - duplicate_rate
        
        return {
            'Total E-Forms': total_forms,
            'Completion Rate': f"{completion_rate:.1f}%",
            'Unique Values': unique_values,
            'Null Values': null_count,
            'Consistency Score': f"{consistency_score:.1f}%"
        }
    
    def calculate_completion_rate(self):
        """Calculate overall data completion rate"""
        total_cells = len(self.data) * len(self.data.columns)
        null_cells = self.data.isna().sum().sum()
        completion_rate = ((total_cells - null_cells) / total_cells) * 100 if total_cells > 0 else 0
        return completion_rate
    
    def calculate_eform_statistics(self):
        """Calculate detailed e-form statistics"""
        eform_col = self.config['eform_col']
        eform_data = self.data[eform_col]
        
        total_forms = len(eform_data)
        completed_forms = eform_data.notna().sum()
        completion_rate = (completed_forms / total_forms) * 100 if total_forms > 0 else 0
        unique_values = eform_data.nunique()
        null_count = eform_data.isna().sum()
        
        # Most common value
        most_common = 'N/A'
        if eform_data.notna().any():
            value_counts = eform_data.value_counts()
            if not value_counts.empty:
                most_common = value_counts.index[0]
        
        # Quality score based on completion and uniqueness
        uniqueness_score = (unique_values / completed_forms) * 100 if completed_forms > 0 else 0
        quality_score = (completion_rate + min(uniqueness_score, 100)) / 2
        
        return {
            'total_forms': total_forms,
            'completed_forms': completed_forms,
            'completion_rate': completion_rate,
            'unique_values': unique_values,
            'null_count': null_count,
            'most_common': most_common,
            'quality_score': quality_score
        }
    
    def calculate_trend_analysis(self):
        """Calculate trend analysis if date columns are available"""
        # Look for date columns
        date_columns = [col for col in self.data.columns if 'date' in col.lower() or col.endswith('_date')]
        
        if not date_columns:
            return None
        
        # Use the first date column found
        date_col = date_columns[0]
        eform_col = self.config['eform_col']
        
        try:
            # Group by date and calculate completion rates
            date_data = self.data.copy()
            date_data[date_col] = pd.to_datetime(date_data[date_col], errors='coerce')
            date_data = date_data.dropna(subset=[date_col])
            
            if date_data.empty:
                return None
            
            # Group by month for trend analysis
            date_data['year_month'] = date_data[date_col].dt.to_period('M')
            monthly_stats = date_data.groupby('year_month').agg({
                eform_col: ['count', lambda x: x.notna().sum()]
            }).round(2)
            
            monthly_stats.columns = ['Total_Records', 'Completed_Forms']
            monthly_stats['Completion_Rate'] = (monthly_stats['Completed_Forms'] / monthly_stats['Total_Records']) * 100
            
            return monthly_stats
            
        except Exception as e:
            return None
    
    def calculate_performance_metrics(self):
        """Calculate performance metrics by vessel and job combination"""
        vessel_col = self.config['vessel_col']
        job_col = self.config['job_col']
        eform_col = self.config['eform_col']
        
        # Group by vessel and job
        grouped = self.data.groupby([vessel_col, job_col])
        
        performance_data = []
        for (vessel, job), group in grouped:
            vessel_name = str(vessel) if not pd.isna(vessel) else "Unknown"
            job_name = str(job) if not pd.isna(job) else "Unknown"
            
            record_count = len(group)
            completed_count = group[eform_col].notna().sum()
            completion_rate = (completed_count / record_count) * 100 if record_count > 0 else 0
            
            performance_data.append({
                'Vessel': vessel_name,
                'Job': job_name,
                'Records': record_count,
                'Completed': completed_count,
                'Completion_Rate': round(completion_rate, 2),
                'Performance_Score': self._calculate_performance_score(completion_rate, record_count)
            })
        
        return pd.DataFrame(performance_data)
    
    def _calculate_performance_score(self, completion_rate, record_count):
        """Calculate a composite performance score"""
        # Normalize record count (log scale to handle wide ranges)
        normalized_count = min(np.log10(record_count + 1) / np.log10(1000), 1) * 100
        
        # Weighted average of completion rate and volume
        performance_score = (completion_rate * 0.7) + (normalized_count * 0.3)
        return round(performance_score, 2)
