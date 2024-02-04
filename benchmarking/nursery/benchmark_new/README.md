# Benchmark Automl submission

## Installation

```
conda create --name synetune python=3.9
pip install 'syne-tune[extra,dev]'
```

To run all experiments, you can run the following:


```bash
python benchmarking/nursery/benchmark_new/benchmark_main.py --experiment_tag "my-new-experiment" --num_seeds 2
```

Which will run all combinations of methods/benchmark/seeds on your local computer for 2 seeds.

Once all evaluations are done, you can pull results by running:

```python benchmarking/nursery/benchmark_new/results_analysis/show_results.py --experiment_tag "my-new-experiment"``` 

you will obtain a plot like showing the confidence intervals of performance over time of all methods on all benchmarks
and also a table showing the average ranks of methods.

You can also only run only one scheduler by doing `python benchmarking/nursery/benchmark_new/benchmark_main.py --method RS`, see
`benchmark_main.py` to see all options supported.


To evaluate other methods/benchmarks, you can edit the following files:
* `baselines.py`: dictionary of HPO methods to be evaluated 
* `benchmark_definitions.py`: dictionary of simulated benchmark to evaluate
* `benchmark_main.py`: script to launch evaluations, run all combinations by default
* `launch_remote.py`: script to launch evaluations on a remote instance
* `show_results.py`: script to plot results obtained 
* `requirements.txt`: dependencies to be installed when running on a remote machine.