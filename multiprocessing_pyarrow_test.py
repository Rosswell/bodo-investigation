import multiprocessing as mp
import pandas as pd
import time
from math import ceil
import snowflake.connector
from sqlalchemy.dialects import registry
registry.register('snowflake', 'snowflake.sqlalchemy', 'dialect')


def test(start, end, total_limit):
    cursor = snowflake.connector.connect(
        user='<user>',
        account='<account>',
        password='<pass>',
        warehouse='<XS warehouse>',
        database='<db>',
        schema='<schema>'
    ).cursor()
    sql = f"select pos, chrstart, chrstop, qual, ref, an, crf, dp, gc, mq, mq0, ns, qd, rfgq_all from (" \
          f"select row_number() over (order by 1) as row_num, * from (select * from WGS_SAMPLE_WGS limit {total_limit})) " \
          f"where row_num >={start} and row_num <{end + 1}"
    cursor.execute(sql)
    df = cursor.fetch_pandas_all()
    df = df.groupby("REF").sum()
    return df


if __name__ == '__main__':
    processes = 12
    total_limit = 50_000_000
    print(f'running {total_limit} rows with {processes} processes')
    nums = list(range(0, total_limit + int(ceil(total_limit / processes)), int(ceil(total_limit / processes))))
    arg_list = [(nums[i], nums[i+1], total_limit) for i in range(len(nums) - 1)]
    pool = mp.Pool(processes=processes)
    t0 = time.time()
    tasks = [pool.apply_async(test, args) for args in arg_list]
    results = pd.concat([p.get() for p in tasks])
    print(f"df creation + groupby + sum time: {round(time.time() - t0, 3)}")
