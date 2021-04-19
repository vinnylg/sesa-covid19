import pandas as pd
from xlsxwriter.worksheet import (
    Worksheet, cell_number_tuple, cell_string_tuple)

def get_column_width(worksheet: Worksheet, column: int):
    """Get the max column width in a `Worksheet` column."""
    strings = getattr(worksheet, '_ts_all_strings', None)
    if strings is None:
        strings = worksheet._ts_all_strings = sorted(
            worksheet.str_table.string_table,
            key=worksheet.str_table.string_table.__getitem__)
    lengths = set()
    for _, colums_dict in worksheet.table.items():  # type: int, dict
        data = colums_dict.get(column)
        if not data:
            continue
        if type(data) is cell_string_tuple:
            iter_length = len(strings[data.string])
            if not iter_length:
                continue
            lengths.add(iter_length)
            continue
        if type(data) is cell_number_tuple:
            iter_length = len(str(data.number))
            if not iter_length:
                continue
            lengths.add(iter_length)
    if not lengths:
        return None
    return max(lengths)+5

def set_column_autowidth(worksheet: Worksheet, column: int):
    """
    Set the width automatically on a column in the `Worksheet`.
    !!! Make sure you run this function AFTER having all cells filled in
    the worksheet!
    """
    maxwidth = get_column_width(worksheet=worksheet, column=column)
    if maxwidth is None:
        return
    worksheet.set_column(first_col=column, last_col=column, width=maxwidth)

def auto_fit_columns(wk,df):
    for i, _ in enumerate(df.columns):
        set_column_autowidth(wk,i)


def normalize_hash(text):
	return "".join(filter(lambda x: (x >= '1' and x <= '9') or (x >= 'A' and x <= 'Z'), str(text).upper()))

def compare_sheets(dfA: pd.DataFrame, dfB: pd.DataFrame):
    dfA['hash'] = dfA.apply(lambda x: normalize_hash("".join([str(col) for col in x])), axis=1)
    dfB['hash'] = dfB.apply(lambda x: normalize_hash("".join([str(col) for col in x])), axis=1)

    A_in_B = dfA.loc[dfA['hash'].isin(dfB['hash'].values)]
    A_not_B = dfA.loc[~dfA['hash'].isin(dfB['hash'].values)]
    
    writer = pd.ExcelWriter("compare_sheets.xlsx",
                        engine='xlsxwriter',
                        datetime_format='dd/mm/yyyy',
                        date_format='dd/mm/yyyy')

    A_in_B.to_excel(writer,'A_in_B',index=None)
    worksheet = writer.sheets['A_in_B']
    auto_fit_columns(worksheet,A_in_B)

    A_not_B.to_excel(writer,'A_not_B',index=None)
    worksheet = writer.sheets['A_not_B']
    auto_fit_columns(worksheet,A_not_B)

    writer.save()


sheetA = pd.read_excel('sheets.xlsx','A')
sheetB = pd.read_excel('sheets.xlsx','B')
compare_sheets(sheetA,sheetB)