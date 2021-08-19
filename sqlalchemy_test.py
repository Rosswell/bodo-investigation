import pandas as pd
import time
from sqlalchemy.dialects import registry
registry.register('snowflake', 'snowflake.sqlalchemy', 'dialect')


def test():
    limit = 50_000_000
    t0 = time.time()
    df = pd.read_sql(f'select * from WGS_SAMPLE_WGS limit {limit}', "snowflake://invitae.us-east-1.snowflakecomputing.com:443?user=<user>&password=<pass>&account=<account>&warehouse=<XS warehouse>&db=<db>&schema=<schema>")
    df = df.groupby("ref").sum()
    print(f"df creation + groupby + sum time: {round(time.time() - t0, 3)}")
    return df


if __name__ == '__main__':
    test()
