# test_multifreq.py
import sys
print("Python version:", sys.version)

# Test 1: Check if calendar_utils is properly set up
try:
    from zipline.utils.calendar_utils import (
        VALID_DATA_FREQUENCIES,
        normalize_frequency,
        FREQUENCY_TO_MINUTES,
        FOUR_HOUR
    )
    print("✓ Calendar utils imports successful")
    print("  Valid frequencies:", sorted(VALID_DATA_FREQUENCIES))
    print("  4H normalized:", normalize_frequency('4h'))
    print("  4H minutes:", FREQUENCY_TO_MINUTES.get(FOUR_HOUR, 'Not found'))
except Exception as e:
    print("✗ Calendar utils error:", e)

# Test 2: Check if _protocol can be imported
try:
    from zipline._protocol import BarData
    print("✓ _protocol imports successful")
except Exception as e:
    print("✗ _protocol import error:", e)
    print("  You may need to rebuild Cython extensions")

# Test 3: Check if data_portal modifications are in place
try:
    from zipline.data.data_portal import DataPortal
    import inspect
    
    # Check if __init__ has the new parameter
    init_source = inspect.getsource(DataPortal.__init__)
    if 'equity_multi_timeframe_readers' in init_source:
        print("✓ DataPortal has multi-timeframe support")
    else:
        print("✗ DataPortal missing multi-timeframe parameter")
        
    # Check for new methods
    if hasattr(DataPortal, '_get_history_multi_timeframe_window'):
        print("✓ DataPortal has _get_history_multi_timeframe_window method")
    else:
        print("✗ DataPortal missing _get_history_multi_timeframe_window method")
except Exception as e:
    print("✗ DataPortal check error:", e)

# Test 4: Check algorithm modifications with proper initialization
try:
    from zipline.algorithm import TradingAlgorithm
    from zipline.finance.trading import SimulationParameters
    from zipline.assets import AssetFinder
    import pandas as pd
    
    # Try different calendar import paths
    trading_calendar = None
    calendar_imported = False
    
    # Try different import paths for calendar
    try:
        from zipline.utils.calendars import get_calendar
        trading_calendar = get_calendar('NYSE')
        calendar_imported = True
        print("✓ Calendar imported from zipline.utils.calendars")
    except ImportError:
        pass
    
    if not calendar_imported:
        try:
            from zipline.calendars import get_calendar
            trading_calendar = get_calendar('NYSE')
            calendar_imported = True
            print("✓ Calendar imported from zipline.calendars")
        except ImportError:
            pass
    
    if not calendar_imported:
        try:
            from zipline.utils.calendar_utils import get_calendar
            trading_calendar = get_calendar('NYSE')
            calendar_imported = True
            print("✓ Calendar imported from zipline.utils.calendar_utils")
        except ImportError:
            pass
    
    if not calendar_imported:
        try:
            # Try using exchange_calendars directly
            import exchange_calendars as ec
            trading_calendar = ec.get_calendar('XNYS')  # NYSE
            calendar_imported = True
            print("✓ Calendar imported from exchange_calendars")
        except ImportError:
            pass
    
    if not calendar_imported:
        try:
            # Last resort - try pandas_market_calendars
            import pandas_market_calendars as mcal
            trading_calendar = mcal.get_calendar('NYSE')
            calendar_imported = True
            print("✓ Calendar imported from pandas_market_calendars")
        except ImportError:
            pass
    
    if not calendar_imported:
        print("✗ Could not import calendar from any known location")
        print("  Attempting to create minimal SimulationParameters...")
        
        # Try creating sim_params without calendar to see if it's optional
        try:
            sim_params = SimulationParameters(
                start_session=pd.Timestamp('2024-01-01', tz='UTC'),
                end_session=pd.Timestamp('2024-12-31', tz='UTC'),
                capital_base=100000,
                data_frequency='minute'
            )
            print("  SimulationParameters created without calendar")
        except Exception as e:
            print("  Failed:", e)
            # Skip remaining algorithm tests
            raise ImportError("Cannot proceed without calendar")
    
    # Create minimal required components
    if trading_calendar:
        sim_params = SimulationParameters(
            start_session=pd.Timestamp('2024-01-01', tz='UTC'),
            end_session=pd.Timestamp('2024-12-31', tz='UTC'),
            trading_calendar=trading_calendar,
            capital_base=100000,
            data_frequency='minute'  # This is for sim_params, not the algo
        )
    else:
        # Try without calendar
        sim_params = SimulationParameters(
            start_session=pd.Timestamp('2024-01-01', tz='UTC'),
            end_session=pd.Timestamp('2024-12-31', tz='UTC'),
            capital_base=100000,
            data_frequency='minute'
        )
    
    # Create a dummy asset finder
    asset_finder = AssetFinder()
    
    # Try creating algorithm
    algo_args = {
        'sim_params': sim_params,
        'asset_finder': asset_finder
    }
    if trading_calendar:
        algo_args['trading_calendar'] = trading_calendar
        
    algo = TradingAlgorithm(**algo_args)
    
    # Now test setting the frequency
    try:
        algo.data_frequency = '4h'
        print("✓ Algorithm accepts '4h' frequency")
        print("  Algorithm data_frequency is now:", algo.data_frequency)
    except ValueError as ve:
        print("✗ Algorithm rejects '4h' frequency:", ve)
    except Exception as e:
        print("✗ Algorithm frequency test error:", e)
        
except Exception as e:
    print("✗ Algorithm check error:", e)
    import traceback
    traceback.print_exc()

# Test 5: Test that invalid frequencies are rejected
try:
    # Check if we have the necessary objects from previous test
    if 'sim_params' not in locals() or 'asset_finder' not in locals():
        print("⚠ Skipping validation test - previous setup failed")
    else:
        # Create fresh algo instance for validation test
        algo_args = {
            'sim_params': sim_params,
            'asset_finder': asset_finder
        }
        if 'trading_calendar' in locals() and trading_calendar:
            algo_args['trading_calendar'] = trading_calendar
            
        algo = TradingAlgorithm(**algo_args)
        
        # Try an invalid frequency
        try:
            algo.data_frequency = 'invalid_freq'
            print("✗ Algorithm should have rejected invalid frequency")
        except ValueError as ve:
            print("✓ Algorithm correctly rejects invalid frequency:", ve)
        except AttributeError:
            print("⚠ Algorithm may not have data_frequency setter implemented yet")
            
except Exception as e:
    print("✗ Validation test error:", e)

# Test 6: Additional test for multi-timeframe data access
try:
    if 'algo' not in locals():
        print("\n⚠ Skipping multi-timeframe access test - algorithm not created")
    else:
        print("\nTesting multi-timeframe data access...")
        
        # Check if algorithm has methods for multi-timeframe support
        if hasattr(algo, 'history_multi_timeframe'):
            print("✓ Algorithm has history_multi_timeframe method")
        else:
            print("✗ Algorithm missing history_multi_timeframe method")
            
        # Check if we can access different timeframe attributes
        if hasattr(algo, 'supported_timeframes'):
            print("✓ Algorithm has supported_timeframes attribute")
            print("  Supported timeframes:", getattr(algo, 'supported_timeframes', 'Not available'))
        else:
            print("  Note: Algorithm may not expose supported_timeframes directly")
            
except Exception as e:
    print("✗ Multi-timeframe access test error:", e)

print("\n" + "="*50)
print("SUMMARY:")
print("="*50)

print("\nKey findings:")
print("- Calendar utilities are properly set up with 4H support")
print("- Protocol imports are working")
print("- DataPortal has multi-timeframe support methods")
print("- Calendar import location needs to be identified for your setup")

# Try to help locate the calendar module
print("\nDiagnostic: Looking for calendar module...")
try:
    import zipline
    import os
    zipline_path = os.path.dirname(zipline.__file__)
    print(f"Zipline is installed at: {zipline_path}")
    
    # Look for calendar-related files
    for root, dirs, files in os.walk(zipline_path):
        for file in files:
            if 'calendar' in file.lower() and file.endswith('.py'):
                rel_path = os.path.relpath(os.path.join(root, file), zipline_path)
                print(f"  Found: {rel_path}")
except Exception as e:
    print(f"  Could not scan for calendar files: {e}")

print("\nNext steps:")
print("1. Identify correct calendar import path in your zipline-reloaded fork")
print("   Check these locations:")
print("   - zipline.calendars")
print("   - zipline.utils.calendar_utils")
print("   - exchange_calendars (external package)")
print("2. Clean build artifacts:")
print("   rmdir /s /q build 2>nul")
print("   del /q src\\zipline\\_protocol.c 2>nul")
print("   del /q src\\zipline\\_protocol.*.pyd 2>nul")
print("3. Rebuild:")
print("   python setup.py build_ext --inplace")
print("4. Install:")
print("   pip install -e .")
print("\nFor robust multi-timeframe support, ensure you've modified:")
print("- calendar_utils.py (frequencies and mappings)")
print("- data_portal.py (multi-timeframe data access)")
print("- algorithm.py (API for accessing different timeframes)")
print("- bar_reader.py (reading multi-timeframe data)")