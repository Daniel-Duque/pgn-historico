def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')

