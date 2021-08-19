import snowflake.connector
import bodo
import time
from sqlalchemy.dialects import registry
registry.register('snowflake', 'snowflake.sqlalchemy', 'dialect')


@bodo.jit(distributed=["df"], cache=True)
def test():
    limit = 50_000_000
    t0 = time.time()
    cursor = snowflake.connector.connect(
        user='<user>',
        account='<account>',
        password='<pass>',
        warehouse='<XS warehouse>',
        database='<db>',
        schema='<schema>'
    ).cursor()
    sql = f'select * from WGS_SAMPLE_WGS limit {limit}'
    cursor.execute(sql)
    df = cursor.fetch_pandas_all()
    df = df.groupby("REF").sum()
    print(f"df creation + groupby + sum time: {round(time.time() - t0, 3)}")
    return df


if __name__ == '__main__':
    test()
