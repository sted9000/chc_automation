"""Parsing with REGEX"""
import datetime
import re

import yaml


def find_net_sales(text):
    # regular expression to find the net sales in the example string below
    # example string: 'Count:  177  Net Sales  $2,055.02  Guest Count:  177'
    pattern = r"Net Sales\s+\$([\d,]+\.\d\d)"
    match = re.search(pattern, text)
    if match:
        return float(match.group(1).replace(",", ""))


def find_customer_count(text):
    # regular expression to find the customer count in the example string below
    # example string: 'Net Sales  $2,055.02  Guest Count:  177  Order Average:'
    pattern = r"Guest Count:\s+(\d+)"
    match = re.search(pattern, text)
    if match:
        return int(match.group(1))


def find_store(text):
    # todo: add regex to find the store name in the example string below
    text = text.replace('\n', ' ')

    # import the store id from the config file
    store_id = yaml.safe_load(open("config.yml"))["store_id"]
    for key, value in store_id.items():
        if value in text.split('-')[0]:
            return key


def find_late_clock_out_times(text):
    text = text.replace('\n', ' ')
    # All text after 'Date'
    text = text.split('Date')[1]
    # extract all the times from the string
    # the times are in the format hh:mm AM or hh:mm PM
    pattern = r"(\d+:\d+ [AP]M)"
    match = re.findall(pattern, text)
    if match:
        # list of only the odd indexes
        clock_out = match[1::2]
        # see if any of the times are after 11:00 AM
        for time in clock_out:
            # convert the time to time object
            time = datetime.datetime.strptime(time, '%I:%M %p').time()
            # see if any of the times are after 2 AM but before 3 Am
            if datetime.time(1, 50) < time < datetime.time(2, 10):
                return True

    return False


def find_over_short(text):
    text = text.replace('\n', ' ')
    # All text before 'Grand Total'
    text = text.split('Grand Total')[0]
    # remove whitespace
    text = text.strip()
    # split the string into a list of items
    text = text.split(' ')
    # grab the last item in the list
    text = text[-1]
    # remove the dollar sign
    text = text.replace('$', '')
    # convert to float (notice that negative numbers have () around them)
    if '(' in text:
        return float(text.replace('(', '').replace(')', '')) * -1
    else:
        return float(text)


def find_lane_total_2(text):
    # regular expression to find the lane total 2 ave time in the example string below
    # example string: '11:37  Lane Total 2  169  04:12  9/14/2023 6:28:47 PM 9/14/2023'
    pattern = r"Lane Total 2\s+(\d+)\s+(\d+:\d+)"
    match = re.search(pattern, text)
    if match:
        return match.group(2)


def find_complete_per(text, store_id):
    # regular expression to find the complete % which is the first value in the parentheses after the store id note
    # that the value may be in the format xx.xx% or xx% so the regex must account for both store_id = ['100-',
    # '400-', '200-', '300-'] 100- Bridgewater DQ 21 (45%)  21 (45.65%)  0 (0%)  25 (54.35%)  0 400- Verona DQ  23 (
    # 50%)  23 (50%)  0 (0%)  23 (50%)  0
    pattern = f'{store_id}-' + r".*?\(([\d.%]+)\)"
    match = re.search(pattern, text)
    if match:
        return match.group(1)
