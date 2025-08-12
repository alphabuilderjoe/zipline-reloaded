"""
Bundle for ingesting multi-timeframe CSV data.
"""
import os
import numpy as np
import pandas as pd
from logbook import Logger
from zipline.data.bundles import register
from zipline.utils.cli import maybe_show_progress
from zipline.data.multi_timeframe_bars import HDF5MultiTimeframeReader
from zipline.utils.calendar_utils import VALID_DATA_FREQUENCIES

log = Logger(__name__)


def multi_timeframe_csv_bundle(environ,
                               asset_db_writer,
                               minute_bar_writer,
                               daily_bar_writer,
                               adjustment_writer,
                               calendar,
                               start_session,
                               end_session,
                               cache,
                               show_progress,
                               output_dir,
                               # Additional parameters for multi-timeframe
                               multi_timeframe_writers=None):
    """
    Build a multi-timeframe bundle from CSV files.
    
    Expects a directory structure like:
    ZIPLINE_CSV_DIR/
        metadata.csv
        daily/
            AAPL.csv
            MSFT.csv
        minute/
            AAPL.csv
            MSFT.csv
        4h/
            AAPL.csv
            MSFT.csv
        1h/
            AAPL.csv
            MSFT.csv
    """
    csv_dir = environ.get('ZIPLINE_CSV_DIR', 'data/csv')
    
    if not os.path.exists(csv_dir):
        raise ValueError(f"CSV directory not found: {csv_dir}")
    
    # Read metadata
    metadata_path = os.path.join(csv_dir, 'metadata.csv')
    if os.path.exists(metadata_path):
        metadata_df = pd.read_csv(metadata_path)
    else:
        # Auto-generate metadata from available files
        metadata_df = _generate_metadata(csv_dir)
    
    # Write asset metadata
    asset_db_writer.write(
        equities=metadata_df[metadata_df['asset_type'] == 'equity'],
        futures=metadata_df[metadata_df['asset_type'] == 'future'],
        exchanges=pd.DataFrame({'exchange': ['NYSE'], 'timezone': ['US/Eastern']})
    )
    
    # Process each frequency
    frequencies_to_process = []
    
    # Standard frequencies
    if daily_bar_writer and os.path.exists(os.path.join(csv_dir, 'daily')):
        frequencies_to_process.append(('daily', daily_bar_writer))
    
    if minute_bar_writer and os.path.exists(os.path.join(csv_dir, 'minute')):
        frequencies_to_process.append(('minute', minute_bar_writer))
    
    # Multi-timeframe frequencies
    if multi_timeframe_writers:
        for frequency, writer in multi_timeframe_writers.items():
            freq_dir = os.path.join(csv_dir, frequency)
            if os.path.exists(freq_dir):
                frequencies_to_process.append((frequency, writer))
    
    # Process each frequency
    for frequency, writer in frequencies_to_process:
        log.info(f"Processing {frequency} data...")
        _process_frequency(
            csv_dir, frequency, writer, metadata_df,
            calendar, show_progress
        )
    
    # Write empty adjustments (or process if you have adjustment data)
    adjustment_writer.write()


def _generate_metadata(csv_dir):
    """Generate metadata from available CSV files."""
    symbols = set()
    
    # Scan all frequency directories
    for freq_dir in os.listdir(csv_dir):
        freq_path = os.path.join(csv_dir, freq_dir)
        if os.path.isdir(freq_path):
            for filename in os.listdir(freq_path):
                if filename.endswith('.csv'):
                    symbol = filename[:-4]
                    symbols.add(symbol)
    
    # Create metadata DataFrame
    metadata = []
    for i, symbol in enumerate(sorted(symbols)):
        metadata.append({
            'symbol': symbol,
            'asset_name': symbol,
            'start_date': '2000-01-01',  # You may want to detect this
            'end_date': '2030-12-31',    # You may want to detect this
            'first_traded': '2000-01-01',
            'auto_close_date': '2030-12-31',
            'asset_type': 'equity',
            'exchange': 'NYSE'
        })
    
    return pd.DataFrame(metadata)


def _process_frequency(csv_dir, frequency, writer, metadata_df,
                      calendar, show_progress):
    """Process all assets for a given frequency."""
    freq_dir = os.path.join(csv_dir, frequency)
    
    # Get list of files to process
    files_to_process = [
        f for f in os.listdir(freq_dir) 
        if f.endswith('.csv')
    ]
    
    with maybe_show_progress(
        files_to_process,
        show_progress,
        label=f'Loading {frequency} data',
    ) as it:
        for filename in it:
            symbol = filename[:-4]
            
            # Find sid for symbol
            sid_row = metadata_df[metadata_df['symbol'] == symbol]
            if sid_row.empty:
                log.warning(f"No metadata found for symbol: {symbol}")
                continue
            
            sid = sid_row.index[0]
            
            # Read CSV data
            filepath = os.path.join(freq_dir, filename)
            df = pd.read_csv(
                filepath,
                parse_dates=['datetime'],
                index_col='datetime'
            )
            
            # Ensure we have all required columns
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in required_columns:
                if col not in df.columns:
                    df[col] = np.nan
            
            # Write the data
            writer.write_sid(sid, df)


# Register the bundle
def register_multi_timeframe_bundle():
    """Register the multi-timeframe CSV bundle."""
    register(
        'multi-timeframe-csv',
        multi_timeframe_csv_bundle,
        calendar_name='NYSE',
        start_session=pd.Timestamp('2000-01-01', tz='UTC'),
        end_session=pd.Timestamp('2030-12-31', tz='UTC'),
        # This tells zipline to create writers for these frequencies
        create_writers=True,
        minutes_per_day=390
    )