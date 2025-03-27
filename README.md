# FairTree

> [!NOTE]
> This code is relative to `Balancing Fairness and Interpretability in Clustering with FairParTree` published at XAI25. For futher development refear to [RuleTree main repository](https://github.com/fismimosa/RuleTree).

The revolution involving Machine Learning has transformed data analytics, making algorithms important in decision-making processes across various domains, even in sensitive scenarios. Indeed, traditional clustering algorithms often lack interpretability and exhibit biases, leading to discriminatory practices and opaque decision-making. 
To overcome these limitations, we introduce FairParTree, a fair and interpretable clustering algorithm that integrates fairness constraints directly into the clustering process, ensuring that the resulting clusters do not disproportionately disadvantage any particular group. 
By leveraging the structure of decision trees, FairParTree enhances the interpretability of clustering results by providing clear and understandable motivations for cluster assignments through rule-based explanations. 
We evaluate FairParTree against state-of-the-art competitors. Through extensive experiments, we show that it maintains strong performances w.r.t. fairness, interpretability, and clustering quality across different dataset sizes, thus positioning itself as a competitive, fair, and interpretable clustering algorithm.

## Setup

### Using PyPI

```bash
  pip install ruletree
```

### Manual Setup

```bash
git clone https://github.com/fismimosa/FairTree
cd FairTree
pip install -e .
```

Dependencies are listed in `requirements.txt`.


## Running the code

Examples can be found in the `main_fainess.py` python file.


## Docs and reference


You can find the software documentation in the [RuleTree repository](https://github.com/fismimosa/RuleTree).
You can cite this work with
```
@article{LANDI2025,
    TOOD
}
```


## Extending the algorithm

//TODO