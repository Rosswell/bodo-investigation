# installation
install conda + bodo + all the rest of the dependencies [conda/bodo installation just uses the official bodo docs](https://docs.bodo.ai/latest/source/install.html)
```shell
curl https://repo.continuum.io/miniconda/Miniconda3-latest-MacOSX-x86_64.sh -L -o miniconda.sh
chmod +x miniconda.sh
./miniconda.sh -b
export PATH=$HOME/miniconda3/bin:$PATH
conda create -n Bodo python
conda activate Bodo
conda install -c bodo.ai -c conda-forge --file requirements.txt
```

# testing files
- `sqlalchemy_bodo_test.py`
  - test bodo functionality with `pd.read_sql()` 
  - run with `mpiexec -n 4` for 4 cores
- `sqlalchemy_test.py`
  - test normal functionality with `pd.read_sql()` 
  - extremely inefficient at > 10M rows, so excluded from comparison, as it is by far the worst option
- `pyarrow_test.py`
  - test normal functionality with `fetch_pandas_all()` 
  - pyarrow-backed snowflake implementation
- `pyarrow_bodo_test.py`
  - test bodo functionality with `fetch_pandas_all()` 
  - run with `mpiexec -n 4` for 4 cores
  - does not currently work because of some JIT issue, see below for stacktrace
- `multiprocessing_pyarrow_test.py`
  - just using native multiprocessing with pyarrow
  - replicates bodo's query chunking across the number of processes used

# time testing:

## looping for n=3
```shell
# test all implementations
export loop=(1 2 3) &&\
for i in "${loop[@]}"; do 
    echo "--pyarrow_test--" && time python pyarrow_test.py
    echo "--sqlalchemy_bodo_test--" && time mpiexec -n 4 python sqlalchemy_bodo_test.py
    echo "--multiprocessing_pyarrow_test--" && time python multiprocessing_pyarrow_test.py
done
```

# memory testing:

i tried using filprofiler, but it does not sum the memory usage of the separate threads from mpiexec, so for that 
reason, i switched to mprof, which produced very similar results, plus the ability to sum the threads' memory usage. 
mprof results are what is reflected in the graph

fil-profiler
```shell
# test all implementations
echo "--pyarrow_test--"; time python -m filprofiler run pyarrow_test.py &&\
echo "--sqlalchemy_test--"; time python -m filprofiler run sqlalchemy_test.py &&\
echo "--sqlalchemy_bodo_test--"; time mpiexec -n 4 python -m filprofiler run sqlalchemy_bodo_test.py &&\
echo "--multiprocessing_pyarrow_test--"; time python -m filprofiler run multiprocessing_pyarrow_test.py
```
mprof 
- there is some error when running mprof with multiprocessing, but it doesn't actually affect the output, i think it's 
just its ability to write to stdout after the profiling is completed
```shell
mprof run --multiprocess --include-children mpiexec -n 4 python sqlalchemy_bodo_test.py; mprof plot
mprof run --multiprocess --include-children pyarrow_test.py; mprof plot
mprof run --multiprocess --include-children multiprocessing_pyarrow_test.py; mprof plot
```

# results
graphs and associated data [can be found in the performance_metrics dir](/performance_metrics)

speed testing was measured as an average of 3 runs of the script being tested, and numbers are in seconds.

memory testing was measure with `mprof`, and represents the peak memory usage of the script. peak memory is used because
this is a measurement of the likelihood of hitting an OOM error, which guides our resource allocation processes, as
this is a scenario that completely blocks the ability to move forward from that point. 

![Time performance](/performance_metrics/time_performance_graph.png)

![Peak memory performance](/performance_metrics/peak_memory_usage_graph.png)

# other misc bodo issues
- issues interpreting query string: needed to add quotes to db and schema, and remove semicolon
```shell
Traceback (most recent call last):
  File "/Users/rblanchard/repos/bodo-investigation/performance_profiling.py", line 464, in <module>
    df = profile(lambda: profiler.num_to_class[method_num](conn, sql, chunksize_ratio=chunksize_ratio, limit=limit), mem_prof_dir)
  File "/Users/rblanchard/miniconda3/envs/Bodo/lib/python3.9/site-packages/filprofiler/api.py", line 43, in profile
    return code_to_profile()
  File "/Users/rblanchard/repos/bodo-investigation/performance_profiling.py", line 464, in <lambda>
    df = profile(lambda: profiler.num_to_class[method_num](conn, sql, chunksize_ratio=chunksize_ratio, limit=limit), mem_prof_dir)
  File "/Users/rblanchard/miniconda3/envs/Bodo/lib/python3.9/site-packages/bodo/numba_compat.py", line 744, in _compile_for_args
    nop__rou = self._compile_for_args(*args)
  File "/Users/rblanchard/miniconda3/envs/Bodo/lib/python3.9/site-packages/bodo/numba_compat.py", line 803, in _compile_for_args
    raise e
  File "/Users/rblanchard/miniconda3/envs/Bodo/lib/python3.9/site-packages/bodo/numba_compat.py", line 715, in _compile_for_args
    nop__rou = self.compile(tuple(shpc__rwuca))
  File "/Users/rblanchard/miniconda3/envs/Bodo/lib/python3.9/site-packages/bodo/numba_compat.py", line 874, in compile
    cres = self._compiler.compile(args, return_type)
  File "/Users/rblanchard/miniconda3/envs/Bodo/lib/python3.9/site-packages/numba/core/dispatcher.py", line 79, in compile
    status, retval = self._compile_cached(args, return_type)
  File "/Users/rblanchard/miniconda3/envs/Bodo/lib/python3.9/site-packages/numba/core/dispatcher.py", line 93, in _compile_cached
    retval = self._compile_core(args, return_type)
  File "/Users/rblanchard/miniconda3/envs/Bodo/lib/python3.9/site-packages/numba/core/dispatcher.py", line 106, in _compile_core
    cres = compiler.compile_extra(self.targetdescr.typing_context,
  File "/Users/rblanchard/miniconda3/envs/Bodo/lib/python3.9/site-packages/numba/core/compiler.py", line 606, in compile_extra
    return pipeline.compile_extra(func)
  File "/Users/rblanchard/miniconda3/envs/Bodo/lib/python3.9/site-packages/numba/core/compiler.py", line 353, in compile_extra
    return self._compile_bytecode()
  File "/Users/rblanchard/miniconda3/envs/Bodo/lib/python3.9/site-packages/numba/core/compiler.py", line 415, in _compile_bytecode
    return self._compile_core()
  File "/Users/rblanchard/miniconda3/envs/Bodo/lib/python3.9/site-packages/numba/core/compiler.py", line 395, in _compile_core
    raise e
  File "/Users/rblanchard/miniconda3/envs/Bodo/lib/python3.9/site-packages/numba/core/compiler.py", line 386, in _compile_core
    pm.run(self.state)
  File "/Users/rblanchard/miniconda3/envs/Bodo/lib/python3.9/site-packages/bodo/numba_compat.py", line 1382, in passmanager_run
    raise e
  File "/Users/rblanchard/miniconda3/envs/Bodo/lib/python3.9/site-packages/bodo/numba_compat.py", line 1368, in passmanager_run
    self._runPass(oavlj__hxj, hhgze__eix, state)
  File "/Users/rblanchard/miniconda3/envs/Bodo/lib/python3.9/site-packages/numba/core/compiler_lock.py", line 35, in _acquire_compile_lock
    return func(*args, **kwargs)
  File "/Users/rblanchard/miniconda3/envs/Bodo/lib/python3.9/site-packages/numba/core/compiler_machinery.py", line 289, in _runPass
    mutated |= check(pss.run_pass, internal_state)
  File "/Users/rblanchard/miniconda3/envs/Bodo/lib/python3.9/site-packages/numba/core/compiler_machinery.py", line 262, in check
    mangled = func(compiler_state)
  File "/Users/rblanchard/miniconda3/envs/Bodo/lib/python3.9/site-packages/bodo/compiler.py", line 188, in run_pass
    evbx__tsc.run()
  File "bodo/transforms/untyped_pass.pyx", line 122, in bodo.transforms.untyped_pass.UntypedPass.run
  File "bodo/transforms/untyped_pass.pyx", line 186, in bodo.transforms.untyped_pass.UntypedPass._run_assign
  File "bodo/transforms/untyped_pass.pyx", line 732, in bodo.transforms.untyped_pass.UntypedPass._run_call
  File "bodo/transforms/untyped_pass.pyx", line 984, in bodo.transforms.untyped_pass.UntypedPass._handle_pd_read_sql
  File "bodo/transforms/untyped_pass.pyx", line 2331, in bodo.transforms.untyped_pass._get_sql_df_type_from_db
  File "/Users/rblanchard/miniconda3/envs/Bodo/lib/python3.9/site-packages/pandas/io/sql.py", line 521, in read_sql
    return pandas_sql.read_query(
  File "/Users/rblanchard/miniconda3/envs/Bodo/lib/python3.9/site-packages/pandas/io/sql.py", line 1308, in read_query
    result = self.execute(*args)
  File "/Users/rblanchard/miniconda3/envs/Bodo/lib/python3.9/site-packages/pandas/io/sql.py", line 1176, in execute
    return self.connectable.execution_options().execute(*args, **kwargs)
  File "<string>", line 2, in execute
  File "/Users/rblanchard/miniconda3/envs/Bodo/lib/python3.9/site-packages/sqlalchemy/util/deprecations.py", line 390, in warned
    return fn(*args, **kwargs)
  File "/Users/rblanchard/miniconda3/envs/Bodo/lib/python3.9/site-packages/sqlalchemy/engine/base.py", line 3108, in execute
    return connection.execute(statement, *multiparams, **params)
  File "/Users/rblanchard/miniconda3/envs/Bodo/lib/python3.9/site-packages/sqlalchemy/engine/base.py", line 1248, in execute
    return self._exec_driver_sql(
  File "/Users/rblanchard/miniconda3/envs/Bodo/lib/python3.9/site-packages/sqlalchemy/engine/base.py", line 1547, in _exec_driver_sql
    ret = self._execute_context(
  File "/Users/rblanchard/miniconda3/envs/Bodo/lib/python3.9/site-packages/sqlalchemy/engine/base.py", line 1814, in _execute_context
    self._handle_dbapi_exception(
  File "/Users/rblanchard/miniconda3/envs/Bodo/lib/python3.9/site-packages/sqlalchemy/engine/base.py", line 1995, in _handle_dbapi_exception
    util.raise_(
  File "/Users/rblanchard/miniconda3/envs/Bodo/lib/python3.9/site-packages/sqlalchemy/util/compat.py", line 207, in raise_
    raise exception
  File "/Users/rblanchard/miniconda3/envs/Bodo/lib/python3.9/site-packages/sqlalchemy/engine/base.py", line 1771, in _execute_context
    self.dialect.do_execute(
  File "/Users/rblanchard/miniconda3/envs/Bodo/lib/python3.9/site-packages/sqlalchemy/engine/default.py", line 717, in do_execute
    cursor.execute(statement, parameters)
  File "/Users/rblanchard/miniconda3/envs/Bodo/lib/python3.9/site-packages/snowflake/connector/cursor.py", line 693, in execute
    Error.errorhandler_wrapper(
  File "/Users/rblanchard/miniconda3/envs/Bodo/lib/python3.9/site-packages/snowflake/connector/errors.py", line 258, in errorhandler_wrapper
    cursor.errorhandler(connection, cursor, error_class, error_value)
  File "/Users/rblanchard/miniconda3/envs/Bodo/lib/python3.9/site-packages/snowflake/connector/errors.py", line 188, in default_errorhandler
    raise error_class(
sqlalchemy.exc.ProgrammingError: (snowflake.connector.errors.ProgrammingError) 001003 (42000): SQL compilation error:
syntax error line 1 at position 76 unexpected ';'.
[SQL: select * from (select * from "WGS_SAMPLE_WGS" limit 10000;) x LIMIT 100]
```
- mpiexec required changing /etc/hosts, adding a line for my computer name:
```
127.0.0.1    rblanchard-MD6R
```
due to the following error
```shell
Fatal error in MPI_Init_thread: Invalid group, error stack:
MPIR_Init_thread(586)..............:
MPID_Init(224).....................: channel initialization failed
MPIDI_CH3_Init(105)................:
MPID_nem_init(324).................:
MPID_nem_tcp_init(175).............:
MPID_nem_tcp_get_business_card(401):
MPID_nem_tcp_init(373).............: gethostbyname failed, rblanchard-MD6R (errno 0)
```
- Numba (pickling?) issues when decorating functions within a class:
```shell
Traceback (most recent call last):
  File "/Users/rblanchard/repos/bodo-investigation/performance_profiling.py", line 464, in <module>
    df = profile(lambda: profiler.num_to_class[method_num](conn, sql, chunksize_ratio=chunksize_ratio, limit=limit), mem_prof_dir)
  File "/Users/rblanchard/miniconda3/envs/Bodo/lib/python3.9/site-packages/filprofiler/api.py", line 43, in profile
    return code_to_profile()
  File "/Users/rblanchard/repos/bodo-investigation/performance_profiling.py", line 464, in <lambda>
    df = profile(lambda: profiler.num_to_class[method_num](conn, sql, chunksize_ratio=chunksize_ratio, limit=limit), mem_prof_dir)
  File "/Users/rblanchard/miniconda3/envs/Bodo/lib/python3.9/site-packages/bodo/numba_compat.py", line 808, in _compile_for_args
    raise error
numba.core.errors.TypingError: non-precise type pyobject
...
This error may have been caused by the following argument(s):
- argument 0: Cannot determine Numba type of <class '__main__.Profiler'>
- argument 1: Cannot determine Numba type of <class 'snowflake.connector.connection.SnowflakeConnection'>
```
- Numba (pickling?) issues when using the snowflake connector:
```shell
Traceback (most recent call last):
  File "/Users/rblanchard/repos/bodo-investigation/pyarrow_bodo_test.py", line 29, in <module>
Traceback (most recent call last):
  File "/Users/rblanchard/repos/bodo-investigation/pyarrow_bodo_test.py", line 29, in <module>
Traceback (most recent call last):
  File "/Users/rblanchard/repos/bodo-investigation/pyarrow_bodo_test.py", line 29, in <module>
    test()
  File "/Users/rblanchard/miniconda3/envs/Bodo/lib/python3.9/site-packages/bodo/numba_compat.py", line 808, in _compile_for_args
    test()
  File "/Users/rblanchard/miniconda3/envs/Bodo/lib/python3.9/site-packages/bodo/numba_compat.py", line 808, in _compile_for_args
    test()
  File "/Users/rblanchard/miniconda3/envs/Bodo/lib/python3.9/site-packages/bodo/numba_compat.py", line 808, in _compile_for_args
Traceback (most recent call last):
  File "/Users/rblanchard/repos/bodo-investigation/pyarrow_bodo_test.py", line 29, in <module>
    test()
  File "/Users/rblanchard/miniconda3/envs/Bodo/lib/python3.9/site-packages/bodo/numba_compat.py", line 808, in _compile_for_args
    raise error
bodo.utils.typing.BodoError: Cannot call non-JIT function 'Connect' from JIT function (convert to JIT or use objmode).

File "pyarrow_bodo_test.py", line 12:
def test():
    <source elided>
    limit = 1_000_000
    cursor = snowflake.connector.connect(
```