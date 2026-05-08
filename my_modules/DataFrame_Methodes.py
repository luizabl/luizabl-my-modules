import pandas as pd #pandas==2.1.0

__version__ = "1.0.0"

#------------------------------------------------------------------------------------
#                                                                                   -
#                         Funções úteis para manipular df                           -
#                                                                                   -
#------------------------------------------------------------------------------------

def Pandas_add_row(df, row_data:list|dict):
    """Custom method for adding a row to a dataframe"""
    if isinstance(row_data, dict):
        new_row = pd.DataFrame(row_data,index=[0])
    elif isinstance(row_data, list):
        if(len(row_data) <=0):
            return df

        if len(row_data) != len(df.columns):
            raise ValueError(f"Row data doesn't match DataFrame columns: row_data_coluns_count|df_coluns_count {len(row_data)}|{len(df.columns)}")
        new_row = pd.DataFrame([row_data], columns=df.columns)
    else:
        raise ValueError(f"Row data format {type(row_data)} not supported")

    return pd.concat([df, new_row], ignore_index=True)


def Pandas_add_rows(df, rows_data:list|dict):
    """Custom method for adding varios rows to a dataframe
    args:
        - rows_data: list of dict or list of list or dict
        ex:
        rows_data = [
            {"col1":1,"col2":2},
            {"col1":3,"col2":4},
            {"col1":5,"col2":6}
        ]
        or
        rows_data = [
            [1,2],
            [3,4],
            [5,6]
        ]
        or
        rows_data = {
            "col1":[1,3,5],
            "col2":[2,4,6]
        }

    """
    if isinstance(rows_data, dict):
        new_rows = pd.DataFrame(rows_data)
    elif isinstance(rows_data, list):
        if(len(rows_data) <=0):
            print("Empty rows data")
            return df
        if isinstance(rows_data[0], dict):
            new_rows = pd.DataFrame(rows_data, columns=df.columns)
        elif isinstance(rows_data[0], list):
            new_rows = pd.DataFrame(rows_data, columns=df.columns)
        else:
            raise ValueError(f"Rows data format{type(rows_data[0])} not supported")
    else:
        raise ValueError(f"Rows data format{type(rows_data)} not supported")

    return pd.concat([df, new_rows], ignore_index=True)
