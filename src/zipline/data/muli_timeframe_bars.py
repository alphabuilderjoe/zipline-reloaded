"""
Multi-timeframe bar readers for handling various intraday frequencies.
"""
import bcolz
import numpy as np
import pandas as pd
from os import path

from zipline.data.bar_reader import BarReader
from zipline.utils.calendar_utils import FREQUENCY_TO_MINUTES
from zipline.utils.cli import maybe_show_progress


class MultiTimeframeBarReader(BarReader):
    """
    Reader for multi-timeframe bar data stored in bcolz format.
    
    Parameters
    ----------
    rootdir : str
        Root directory containing the bcolz files.
    frequency : str
        The frequency of the bars (e.g., '4h', '1h', '30m').
    """
    
    def __init__(self, rootdir, frequency):
        self._rootdir = rootdir
        self._frequency = frequency
        self._minutes_per_bar = FREQUENCY_TO_MINUTES[frequency]
        
        # Load metadata
        self._load_metadata()
        
    def _load_metadata(self):
        """Load metadata about stored assets and date ranges."""
        metadata_path = path.join(self._rootdir, 'metadata.json')
        if path.exists(metadata_path):
            import json
            with open(metadata_path, 'r') as f:
                self._metadata = json.load(f)
        else:
            self._metadata = {}
            
    def load_raw_arrays(self, columns, start_dt, end_dt, sids):
        """
        Load raw data arrays for the given parameters.
        
        Parameters
        ----------
        columns : list[str]
            List of column names to load.
        start_dt : pd.Timestamp
            Start datetime for the query.
        end_dt : pd.Timestamp
            End datetime for the query.
        sids : list[int]
            List of security IDs to load.
            
        Returns
        -------
        dict[str, np.ndarray]
            Dictionary mapping column names to data arrays.
        """
        # Calculate number of bars
        trading_calendar = self._trading_calendar
        sessions = trading_calendar.sessions_in_range(start_dt, end_dt)
        
        # For intraday bars, calculate total number of bars
        bars_per_day = 390 // self._minutes_per_bar  # 390 minutes in trading day
        total_bars = len(sessions) * bars_per_day
        
        # Initialize output arrays
        output = {}
        for column in columns:
            output[column] = np.full(
                (total_bars, len(sids)), 
                np.nan,
                dtype=np.float64
            )
        
        # Load data for each sid
        for sid_idx, sid in enumerate(sids):
            sid_path = path.join(self._rootdir, f"{sid}")
            if not path.exists(sid_path):
                continue
                
            # Load bcolz arrays
            for column in columns:
                column_path = path.join(sid_path, column)
                if path.exists(column_path):
                    array = bcolz.open(column_path, mode='r')
                    # Copy data to output array
                    # (Implementation depends on your data storage format)
                    output[column][:, sid_idx] = array[:]
                    
        return output
        
    def get_value(self, sid, dt, field):
        """
        Get a single value for the given sid, datetime, and field.
        
        Parameters
        ----------
        sid : int
            Security ID.
        dt : pd.Timestamp
            Datetime for the query.
        field : str
            Field name to retrieve.
            
        Returns
        -------
        float
            The value for the given parameters.
        """
        sid_path = path.join(self._rootdir, f"{sid}", field)
        if not path.exists(sid_path):
            return np.nan
            
        # Load the specific value
        # (Implementation depends on your indexing scheme)
        array = bcolz.open(sid_path, mode='r')
        # Find the index for the given datetime
        # Return the value
        
    def get_last_traded_dt(self, sid, dt):
        """
        Get the last datetime for which we have trade data for this sid.
        
        Parameters
        ----------
        sid : int
            Security ID.
        dt : pd.Timestamp
            Datetime to search from.
            
        Returns
        -------
        pd.Timestamp
            Last traded datetime.
        """
        # Implementation to find last traded datetime
        pass


class HDF5MultiTimeframeReader(BarReader):
    """
    Alternative reader using HDF5 format for better performance.
    """
    
    def __init__(self, filepath, frequency):
        self._filepath = filepath
        self._frequency = frequency
        self._minutes_per_bar = FREQUENCY_TO_MINUTES[frequency]
        self._store = None
        
    def _ensure_open(self):
        """Ensure HDF5 store is open."""
        if self._store is None:
            self._store = pd.HDFStore(self._filepath, mode='r')
            
    def load_raw_arrays(self, columns, start_dt, end_dt, sids):
        """Load data from HDF5 store."""
        self._ensure_open()
        
        output = {}
        for column in columns:
            data_list = []
            for sid in sids:
                key = f"/{self._frequency}/{sid}/{column}"
                if key in self._store:
                    df = self._store.select(
                        key,
                        where='index >= start_dt and index <= end_dt'
                    )
                    data_list.append(df.values)
                else:
                    # No data for this sid/column
                    data_list.append(np.full(len(df), np.nan))
                    
            output[column] = np.column_stack(data_list)
            
        return output