import pandas as pd
import pathlib

files = pathlib.Path("data").glob("*_trab.csv")
df_vsns = pd.read_csv("data/vs_ns_angles.csv", index_col=0)

dfs = []
for f in files:
    df = pd.read_csv(f, index_col=0)
    df["name"] = len(df) * [f.stem]
    df["ns_angle_orig"] = len(df) * [
        df_vsns[df_vsns["name"] == f.stem]["neckshaft"].values[0]
    ]
    df["vs_angle_orig"] = len(df) * [
        df_vsns[df_vsns["name"] == f.stem]["version"].values[0]
    ]

    print(df)
    dfs.append(df)

dfs = pd.concat(dfs)

dfs.to_parquet("trab_rays.parquet")
