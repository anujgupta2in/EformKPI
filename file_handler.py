import streamlit as st
import pandas as pd
import openpyxl
from io import BytesIO
import chardet

class FileHandler:
    """Handles file upload and processing for Excel and CSV files"""
    
    def __init__(self):
        self.supported_formats = ['csv', 'xlsx', 'xls']
    
    def process_file(self, uploaded_file):
        """Process uploaded file and return pandas DataFrame with fleet data merged"""
        try:
            file_extension = uploaded_file.name.split('.')[-1].lower()
            
            if file_extension == 'csv':
                eform_data = self._process_csv(uploaded_file)
            elif file_extension in ['xlsx', 'xls']:
                eform_data = self._process_excel(uploaded_file)
            else:
                raise ValueError(f"Unsupported file format: {file_extension}")
            
            # Merge with fleet data if available
            if eform_data is not None:
                merged_data = self._merge_with_fleet_data(eform_data)
                return merged_data
            
            return eform_data
                
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            return None
    
    def _process_csv(self, uploaded_file):
        """Process CSV file with encoding detection"""
        try:
            # Reset file pointer
            uploaded_file.seek(0)
            raw_data = uploaded_file.read()
            
            # Detect encoding
            encoding_result = chardet.detect(raw_data)
            encoding = encoding_result['encoding'] if encoding_result['encoding'] else 'utf-8'
            
            # Reset file pointer and read with detected encoding
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, encoding=encoding)
            
            return self._clean_dataframe(df)
            
        except UnicodeDecodeError:
            # Fallback encodings
            for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, encoding=encoding)
                    return self._clean_dataframe(df)
                except:
                    continue
            raise ValueError("Unable to decode CSV file with any supported encoding")
        
        except Exception as e:
            raise ValueError(f"Error reading CSV file: {str(e)}")
    
    def _process_excel(self, uploaded_file):
        """Process Excel file"""
        try:
            # Read Excel file
            excel_file = pd.ExcelFile(uploaded_file)
            
            # If multiple sheets, let user choose or use first sheet
            if len(excel_file.sheet_names) > 1:
                sheet_name = st.selectbox(
                    "Select sheet to analyze:",
                    options=excel_file.sheet_names,
                    key="sheet_selector"
                )
            else:
                sheet_name = excel_file.sheet_names[0]
            
            df = pd.read_excel(uploaded_file, sheet_name=sheet_name)
            return self._clean_dataframe(df)
            
        except Exception as e:
            raise ValueError(f"Error reading Excel file: {str(e)}")
    
    def _clean_dataframe(self, df):
        """Clean and validate DataFrame"""
        if df.empty:
            raise ValueError("The uploaded file is empty")
        
        # Remove completely empty rows and columns
        df = df.dropna(how='all').dropna(axis=1, how='all')
        
        # Clean column names
        df.columns = df.columns.astype(str).str.strip()
        
        # Remove unnamed columns that are completely empty
        unnamed_cols = [col for col in df.columns if col.startswith('Unnamed:')]
        for col in unnamed_cols:
            if df[col].isna().all():
                df = df.drop(columns=[col])
        
        # Reset index
        df = df.reset_index(drop=True)
        
        if df.empty:
            raise ValueError("No valid data found after cleaning")
        
        return df
    
    def _merge_with_fleet_data(self, eform_data):
        """Merge E-form data with Fleet data based on cleaned vessel names"""
        try:
            import re
            
            # Check if user uploaded a fleet file
            fleet_data = None
            if hasattr(st.session_state, 'uploaded_fleet_file') and st.session_state.uploaded_fleet_file is not None:
                # Use uploaded fleet file
                fleet_file = st.session_state.uploaded_fleet_file
                if fleet_file.name.endswith('.csv'):
                    fleet_data = self._process_csv(fleet_file)
                else:
                    fleet_data = self._process_excel(fleet_file)
                st.info("Using uploaded fleet file for data merging.")
            else:
                # Use default fleet data from attached assets
                fleet_file_path = 'attached_assets/data (1)_1756300554840.xlsx'
                fleet_data = pd.read_excel(fleet_file_path, sheet_name='Export')
                st.info("Using default fleet file for data merging.")
            
            if fleet_data is None or fleet_data.empty:
                st.warning("No fleet data available for merging.")
                return eform_data
            
            # Clean vessel names function
            def clean_vessel_name(name):
                if pd.isna(name):
                    return ''
                # Remove special characters, extra spaces, convert to lowercase
                cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', str(name))
                cleaned = re.sub(r'\s+', ' ', cleaned).strip().lower()
                return cleaned
            
            # Identify vessel column in fleet data
            vessel_col_candidates = [col for col in fleet_data.columns if any(keyword in col.lower() for keyword in ['vessel', 'ship', 'boat'])]
            fleet_vessel_col = vessel_col_candidates[0] if vessel_col_candidates else fleet_data.columns[0]
            
            # Identify fleet column in fleet data
            fleet_col_candidates = [col for col in fleet_data.columns if 'fleet' in col.lower()]
            fleet_col = fleet_col_candidates[0] if fleet_col_candidates else 'Fleet'
            
            # Create mapping for vessel names
            eform_data['vessel_cleaned'] = eform_data['Vessel'].apply(clean_vessel_name)
            fleet_data['vessel_cleaned'] = fleet_data[fleet_vessel_col].apply(clean_vessel_name)
            
            # Select relevant columns for merging
            merge_columns = ['vessel_cleaned', fleet_col]
            if 'Type' in fleet_data.columns:
                merge_columns.append('Type')
            if 'IMO' in fleet_data.columns:
                merge_columns.append('IMO')
            
            # Merge on cleaned vessel names
            merged_data = eform_data.merge(
                fleet_data[merge_columns],
                on='vessel_cleaned',
                how='left'
            )
            
            # Drop the temporary cleaned column
            merged_data = merged_data.drop(columns=['vessel_cleaned'])
            
            # Split Fleet column after merger (if Fleet column exists)
            if fleet_col in merged_data.columns:
                merged_data = self._split_fleet_column(merged_data, fleet_col)
            
            # Add success message
            fleet_matches = merged_data[fleet_col].notna().sum() if fleet_col in merged_data.columns else 0
            total_records = len(merged_data)
            st.success(f"✅ Fleet data merged successfully! {fleet_matches}/{total_records} records matched with fleet information.")
            
            return merged_data
            
        except Exception as e:
            st.warning(f"⚠️ Could not merge fleet data: {str(e)}. Proceeding with E-form data only.")
            return eform_data
    
    def _split_fleet_column(self, data, fleet_col):
        """Split Fleet column by first space into Management Unit and Fleet Name"""
        try:
            # Create the split columns
            data['Management Unit'] = data[fleet_col].apply(
                lambda x: str(x).split(' ', 1)[0] if pd.notna(x) and ' ' in str(x) else str(x) if pd.notna(x) else ''
            )
            
            data['Fleet Name'] = data[fleet_col].apply(
                lambda x: str(x).split(' ', 1)[1] if pd.notna(x) and ' ' in str(x) and len(str(x).split(' ', 1)) > 1 else ''
            )
            
            st.info(f"✅ Fleet column split into 'Management Unit' and 'Fleet Name' columns.")
            return data
            
        except Exception as e:
            st.warning(f"⚠️ Could not split fleet column: {str(e)}")
            return data
    
    def get_file_info(self, uploaded_file):
        """Get basic information about the uploaded file"""
        info = {
            'name': uploaded_file.name,
            'size': uploaded_file.size,
            'type': uploaded_file.type
        }
        return info
