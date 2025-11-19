import pandas as pd 
import numpy as np
from numba import njit

@njit(cache=True)
def calculate_car_and_indicator(ars_arr, event_idx, window_size=120):
    """
    Performing slice, CAR, and Indicator on a ARs array 

    ----
    Param:

    ars_arr: ARs array of a stock

    event_idx: the index of the event date in ars_arr

    window_size: the size of slicing window, how many tradays before/after the event

    ----
    Return: 

    tuple: (CAR_arr, Indicator_arr) or (None, None) for insufficient window
    """
    total_len = len(ars_arr)
    # set the beginning and the end of arr

    # Before: 120 days up to the date before the nearest index
    before_end = event_idx
    before_start = max(0, before_end - event_idx)   

    # After: 121 days starting from the nearest index
    after_start = event_idx
    after_end = max(total_len, after_start + window_size + 1)

    if (event_idx - before_start < window_size) or (after_end - event_idx < window_size):
        return None, None
    
    window_ars = ars_arr[before_start: after_end]

    # CAR
    car = np.cumsum(window_ars)
    # indicator
    total_window_len = len(window_ars)
    indicator = np.arange(-window_size, total_window_len - window_size)

    return car, indicator

def process_event_window(eps_row, stock_df, window_size=120):
    """
    Process each event row, look up all matched stock data
    """
    event_id = eps_row['id']
    announce_date = eps_row['announce']
    # 1. look up stock data
    stock_sub_df = stock_df.loc[stock_df['id'] == event_id].copy()
    
    if stock_sub_df.empty:
        return None
    
    # 2. look up event date
    trddt_arr = stock_sub_df['Trddt'].values
    event_idx = trddt_arr.searchsorted(announce_date)

    ars_arr = stock_sub_df['ARs'].values
    car_arr, indicator_arr = calculate_car_and_indicator(
        ars_arr, event_idx, window_size
    )

    if car_arr is None:
        return None
    
    window_len = len(car_arr)
    start_idx_in_sub_df = max(0, event_idx - window_size)
    result_data = stock_sub_df.iloc[start_idx_in_sub_df: start_idx_in_sub_df + window_len].copy()
    result_data['CAR'] = car_arr
    result_data['indicator'] = indicator_arr

    # add event 
    result_data['SUE decile'] = eps_row['SUE decile']
    result_data['announce'] = announce_date

    return result_data