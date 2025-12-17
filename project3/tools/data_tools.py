def inspect_dataset(df):
    return {
        "num_rows": df.shape[0],
        "num_columns": df.shape[1],
        "columns": df.dtypes.astype(str).to_dict(),
        "missing_values": df.isnull().sum().to_dict()
    }
