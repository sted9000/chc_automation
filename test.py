from process import process_timecard, process_till_history

download = './data/till-history-2023-10-18.pdf'
# extract the store from the download string

process_till_history(download)