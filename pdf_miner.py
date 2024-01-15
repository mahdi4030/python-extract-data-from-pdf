from pathlib import Path
from typing import Iterable, Any

from pdfminer.high_level import extract_pages

process_mode = 0 # 0: No processing yet, 1: Processing, 2: Finished
processed_page_count = -1
current_page_number = 0
start_page_number = -1
index = -1
process_page = 0
offset_x = 0
start_title = "Platts North Sea Dated Brent, BFOE, CFD Bids, Offers, Trades"
text_result = []
current_text_columns = None
end_title_pos = None
first_column_index = -1

def merge_text_columns():
    global current_text_columns
    global text_result
    if current_text_columns is not None:
        for col, rows in enumerate(current_text_columns):
            if len(text_result) == 0 and col < first_column_index:
                continue
            if end_title_pos is not None and col > end_title_pos[0]:
                continue
            for ind, row in enumerate(rows):
                if end_title_pos is not None and col == end_title_pos[0] and ind >= end_title_pos[1]:
                    continue
                text_result.append(row)
    current_text_columns = [[] for _ in range(5)]

def check_font_type(o):
    if isinstance(o, Iterable):
        for i in o:
            font = check_font_type(i)
            if font > 0:
                return font
    else:
        if hasattr(o, 'fontname'):
            if o.fontname.endswith("-Bold"):
                return 2
            elif o.fontname.endswith("AkkuratLL-Light") and abs(o.size - 9) < 0.0001:
                return 1
            else:
                return 3
        else:
            return 0
    return 0

def extract_ltitem_hierarchy(o: Any, depth=0):
    global process_mode
    global processed_page_count
    global process_page
    global offset_x
    global current_page_number
    global start_page_number
    global first_column_index
    global end_title_pos
    if depth > 3:
        return
    if depth == 1:
        if process_mode == 2:
            return
        current_page_number += 1
        merge_text_columns()
        if process_mode == 1:
            process_page = 0
            processed_page_count += 1
    txt = get_optional_text(o)
    txt_line = "".join(txt.split("\n"))
    if current_page_number == 1:
        if txt_line.startswith(start_title):
            start_page_number = int(txt_line.split(" ")[-1])
    if current_page_number > 1 and start_page_number > current_page_number:
        return
    if txt_line == start_title:
        process_mode = 1
        process_page = 0
        processed_page_count = 0
        offset_x = o.x0
        return
    if processed_page_count > 0:
        offset_x = 100
    if process_mode == 1:
        if txt_line.endswith("by S&P Global Inc. All rights reserved.") or o.__class__.__name__ == "LTFigure":
            process_page += 1
    if process_mode >= 1 and o.__class__.__name__ == "LTTextBoxHorizontal" and process_page == 0:
        font_type = check_font_type(o)
        col = int(o.x0 / 225)
        if font_type == 2 and txt_line.startswith("Platts WTI Midland Crude DAP Europe") and end_title_pos is None:
            end_title_pos = (col, len(current_text_columns[col]))
            process_mode = 2
        elif font_type == 1:
            current_text_columns[col].append(txt)
            if first_column_index == -1:
                first_column_index = col
    if isinstance(o, Iterable):
        for i in o:
            extract_ltitem_hierarchy(i, depth=depth + 1)


def get_optional_text(o: Any) -> str:
    """Text of LTItem if available, otherwise empty string"""
    if hasattr(o, 'get_text'):
        txt = o.get_text().strip()
        return txt
    return ''

file_name = 'COM_20230711.pdf'
path = Path(file_name).expanduser()
pages = extract_pages(path)
extract_ltitem_hierarchy(pages)
merge_text_columns()
with open("".join(file_name.split(".")[:-1])+".txt", "w") as f:
    f.write("\n".join(text_result))