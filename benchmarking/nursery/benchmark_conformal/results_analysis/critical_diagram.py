# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License").
# You may not use this file except in compliance with the License.
# A copy of the License is located at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# or in the "license" file accompanying this file. This file is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied. See the License for the specific language governing
# permissions and limitations under the License.
from pathlib import Path

import pandas as pd
import scikit_posthocs as sp
from autorank import plot_stats, autorank
from pandas import Series

from typing import Union, List, Tuple, Dict, Set

import numpy as np
from matplotlib import colors, pyplot as plt
from matplotlib.axes import SubplotBase
from matplotlib.colorbar import ColorbarBase, Colorbar
from matplotlib.colors import ListedColormap
from matplotlib import pyplot
from pandas import DataFrame, Series
from seaborn import heatmap


def sign_array(p_values: Union[List, np.ndarray], alpha: float = 0.05) -> np.ndarray:
    """Significance array.

    Converts an array with p values to a significance array where
    0 is False (not significant), 1 is True (significant),
    and -1 is for diagonal elements.

    Parameters
    ----------
    p_values : Union[List, np.ndarray]
        Any object exposing the array interface and containing
        p values.

    alpha : float = 0.05
        Significance level. Default is 0.05.

    Returns
    -------
    result : numpy.ndarray
        Array where 0 is False (not significant), 1 is True (significant),
        and -1 is for diagonal elements.

    Examples
    --------
    >>> p_values = np.array([[ 1.        ,  0.00119517,  0.00278329],
                             [ 0.00119517,  1.        ,  0.18672227],
                             [ 0.00278329,  0.18672227,  1.        ]])
    >>> ph.sign_array(p_values)
    array([[1, 1, 1],
           [1, 1, 0],
           [1, 0, 1]])
    """
    p_values = np.array(p_values)
    p_values[p_values > alpha] = 0
    p_values[(p_values < alpha) & (p_values > 0)] = 1
    np.fill_diagonal(p_values, 1)

    return p_values


def sign_table(
    p_values: Union[List, np.ndarray, DataFrame], lower: bool = True, upper: bool = True
) -> Union[DataFrame, np.ndarray]:
    """Significance table.

    Returns table that can be used in a publication. P values are replaced
    with asterisks: \\* - p < 0.05, \\*\\* - p < 0.01, \\*\\*\\* - p < 0.001.

    Parameters
    ----------
    p_values : Union[List, np.ndarray, DataFrame]
        Any object exposing the array interface and containing
        p values.

    lower : bool
        Defines whether to return the lower triangle.

    upper : bool
        Defines whether to return the upper triangle.

    Returns
    -------
    result : Union[DataFrame, np.ndarray]
        P values masked with asterisks.

    Examples
    --------
    >>> p_values = np.array([[-1.        ,  0.00119517,  0.00278329],
                      [ 0.00119517, -1.        ,  0.18672227],
                      [ 0.00278329,  0.18672227, -1.        ]])
    >>> ph.sign_table(p_values)
    array([['-', '**', '**'],
           ['**', '-', 'NS'],
           ['**', 'NS', '-']], dtype=object)
    """
    if not any([lower, upper]):
        raise ValueError("Either lower or upper triangle must be returned")

    pv = (
        DataFrame(p_values, copy=True)
        if not isinstance(p_values, DataFrame)
        else p_values.copy()
    )

    ns = pv > 0.05
    three = (pv < 0.001) & (pv >= 0)
    two = (pv < 0.01) & (pv >= 0.001)
    one = (pv < 0.05) & (pv >= 0.01)

    pv = pv.astype(str)
    pv[ns] = "NS"
    pv[three] = "***"
    pv[two] = "**"
    pv[one] = "*"

    np.fill_diagonal(pv.values, "-")
    if not lower:
        pv.values[np.tril_indices(pv.shape[0], -1)] = ""
    elif not upper:
        pv.values[np.triu_indices(pv.shape[0], 1)] = ""

    return pv


def sign_plot(
    x: Union[List, np.ndarray, DataFrame],
    g: Union[List, np.ndarray] = None,
    flat: bool = False,
    labels: bool = True,
    cmap: List = None,
    cbar_ax_bbox: List = None,
    ax: SubplotBase = None,
    **kwargs,
) -> Union[SubplotBase, Tuple[SubplotBase, Colorbar]]:
    """Significance plot, a heatmap of p values (based on Seaborn).

    Parameters
    ----------
    x : Union[List, np.ndarray, DataFrame]
        If flat is False (default), x must be an array, any object exposing
        the array interface, containing p values. If flat is True, x must be
        a sign_array (returned by :py:meth:`scikit_posthocs.sign_array`
        function).

    g : Union[List, np.ndarray]
        An array, any object exposing the array interface, containing
        group names.

    flat : bool
        If `flat` is True, plots a significance array as a heatmap using
        seaborn. If `flat` is False (default), plots an array of p values.
        Non-flat mode is useful if you need to  differentiate significance
        levels visually. It is the preferred mode.

    labels : bool
        Plot axes labels (default) or not.

    cmap : list
        1) If flat is False (default):
        List consisting of five elements, that will be exported to
        ListedColormap method of matplotlib. First is for diagonal
        elements, second is for non-significant elements, third is for
        p < 0.001, fourth is for p < 0.01, fifth is for p < 0.05.

        2) If flat is True:
        List consisting of three elements, that will be exported to
        ListedColormap method of matplotlib. First is for diagonal
        elements, second is for non-significant elements, third is for
        significant ones.
        3) If not defined, default colormaps will be used.

    cbar_ax_bbox : list
        Colorbar axes position rect [left, bottom, width, height] where
        all quantities are in fractions of figure width and height.
        Refer to `matplotlib.figure.Figure.add_axes` for more information.
        Default is [0.95, 0.35, 0.04, 0.3].

    ax : SubplotBase
        Axes in which to draw the plot, otherwise use the currently-active
        Axes.

    kwargs
        Keyword arguments to be passed to seaborn heatmap method. These
        keyword args cannot be used: cbar, vmin, vmax, center.

    Returns
    -------
    ax : matplotlib.axes._subplots.AxesSubplot
        Axes object with the heatmap.

    cbar : matplotlib.colorbar.Colorbar
        ColorBar object if `flat` is set to False.

    Examples
    --------
    >>> x = np.array([[ 1, 1, 1],
                      [ 1, 1, 0],
                      [ 1, 0, 1]])
    >>> ph.sign_plot(x, flat = True)
    """
    for key in ["cbar", "vmin", "vmax", "center"]:
        if key in kwargs:
            del kwargs[key]

    if isinstance(x, DataFrame):
        df = x.copy()
    else:
        x = np.array(x)
        g = g or np.arange(x.shape[0])
        df = DataFrame(np.copy(x), index=g, columns=g)

    dtype = df.values.dtype

    if not np.issubdtype(dtype, np.integer) and flat:
        raise ValueError("X should be a sign_array or DataFrame of integers")
    elif not np.issubdtype(dtype, np.floating) and not flat:
        raise ValueError("X should be an array or DataFrame of float p values")

    if not cmap and flat:
        # format: diagonal, non-significant, significant
        cmap = ["1", "#fbd7d4", "#1a9641"]
    elif not cmap and not flat:
        # format: diagonal, non-significant, p<0.001, p<0.01, p<0.05
        cmap = ["1", "#fbd7d4", "#005a32", "#238b45", "#a1d99b"]

    if flat:
        np.fill_diagonal(df.values, -1)
        hax = heatmap(
            df, vmin=-1, vmax=1, cmap=ListedColormap(cmap), cbar=False, ax=ax, **kwargs
        )
        if not labels:
            hax.set_xlabel("")
            hax.set_ylabel("")
        return hax

    else:
        df[(x < 0.001) & (x >= 0)] = 1
        df[(x < 0.01) & (x >= 0.001)] = 2
        df[(x < 0.05) & (x >= 0.01)] = 3
        df[(x >= 0.05)] = 0

        np.fill_diagonal(df.values, -1)

        if len(cmap) != 5:
            raise ValueError("Cmap list must contain 5 items")

        hax = heatmap(
            df,
            vmin=-1,
            vmax=3,
            cmap=ListedColormap(cmap),
            center=1,
            cbar=False,
            ax=ax,
            **kwargs,
        )
        if not labels:
            hax.set_xlabel("")
            hax.set_ylabel("")

        cbar_ax = hax.figure.add_axes(cbar_ax_bbox or [0.95, 0.35, 0.04, 0.3])
        cbar = ColorbarBase(
            cbar_ax,
            cmap=(ListedColormap(cmap[2:] + [cmap[1]])),
            norm=colors.NoNorm(),
            boundaries=[0, 1, 2, 3, 4],
        )
        cbar.set_ticks(
            list(np.linspace(0, 3, 4)),
            labels=["p < 0.001", "p < 0.01", "p < 0.05", "NS"],
        )

        cbar.outline.set_linewidth(1)
        cbar.outline.set_edgecolor("0.5")
        cbar.ax.tick_params(size=0)

        return hax, cbar


def _find_maximal_cliques(adj_matrix: DataFrame) -> List[Set]:
    """Wrapper function over the recursive Bron-Kerbosch algorithm.

    Will be used to find points that are under the same crossbar in critical
    difference diagrams.

    Parameters
    ----------
    adj_matrix : pandas.DataFrame
        Binary matrix with 1 if row item and column item do NOT significantly
        differ. Values in the main diagonal are not considered.

    Returns
    -------
    list[set]
        Largest fully connected subgraphs, represented as sets of indices of
        adj_matrix.

    Raises
    ------
    ValueError
        If the input matrix is empty or not symmetric.
        If the input matrix is not binary.

    """
    if (adj_matrix.index != adj_matrix.columns).any():
        raise ValueError("adj_matrix must be symmetric, indices do not match")
    if not adj_matrix.isin((0, 1)).values.all():
        raise ValueError("Input matrix must be binary")
    if adj_matrix.empty or not (adj_matrix.T == adj_matrix).values.all():
        raise ValueError("Input matrix must be non-empty and symmetric")

    result = []
    _bron_kerbosch(
        current_clique=set(),
        candidates=set(adj_matrix.index),
        visited=set(),
        adj_matrix=adj_matrix,
        result=result,
    )
    return result


def _bron_kerbosch(
    current_clique: Set,
    candidates: Set,
    visited: Set,
    adj_matrix: DataFrame,
    result: List[Set],
) -> None:
    """Recursive algorithm to find the maximal fully connected subgraphs.

    See [1]_ for more information.

    Parameters
    ----------
    current_clique : set
        A set of vertices known to be fully connected.
    candidates : set
        Set of vertices that could potentially be added to the clique.
    visited : set
        Set of vertices already known to be part of another previously explored
        clique, that is not current_clique.
    adj_matrix : pandas.DataFrame
        Binary matrix with 1 if row item and column item do NOT significantly
        differ. Diagonal must be zeroed.
    result : list[set]
        List where to append the maximal cliques.

    Returns
    -------
    None

    References
    ----------
    .. [1] https://en.wikipedia.org/wiki/Bron%E2%80%93Kerbosch_algorithm
    """
    while candidates:
        v = candidates.pop()
        _bron_kerbosch(
            current_clique | {v},
            # Restrict candidate vertices to the neighbors of v
            {n for n in candidates if adj_matrix.loc[v, n]},
            # Restrict visited vertices to the neighbors of v
            {n for n in visited if adj_matrix.loc[v, n]},
            adj_matrix,
            result,
        )
        visited.add(v)

    # We do not need to report a clique if a children call aready did it.
    if not visited:
        # If this is not a terminal call, i.e. if any clique was reported.
        result.append(current_clique)


def critical_difference_diagram(
    ranks: Union[dict, Series],
    sig_matrix: DataFrame,
    *,
    ax: SubplotBase = None,
    alpha: float = 0.05,
    label_fmt_left: str = "{label} ({rank:.2g})",
    label_fmt_right: str = "({rank:.2g}) {label}",
    label_props: dict = None,
    marker_props: dict = None,
    elbow_props: dict = None,
    crossbar_props: dict = None,
    text_h_margin: float = 0.01,
) -> Dict[str, list]:
    """Plot a Critical Difference diagram from ranks and post-hoc results.

    The diagram arranges the average ranks of multiple groups on the x axis
    in order to facilitate performance comparisons between them. The groups
    that could not be statistically deemed as different are linked by a
    horizontal crossbar [1]_, [2]_.

    ::

                      rank markers
         X axis ---------O----O-------------------O-O------------O---------
                         |----|                   | |            |
                         |    |                   |---crossbar---|
                clf1 ----|    |                   | |            |---- clf3
                clf2 ---------|                   | |----------------- clf4
                                                  |------------------- clf5
                    |____|
                text_h_margin

    In the drawing above, the two crossbars indicate that clf1 and clf2 cannot
    be statistically differentiated, the same occurring between clf3, clf4 and
    clf5. However, clf1 and clf2 are each significantly lower ranked than clf3,
    clf4 and clf5.

    Parameters
    ----------
    ranks : dict or Series
        Indicates the rank value for each sample or estimator (as keys or index).

    sig_matrix : DataFrame
        The corresponding p-value matrix outputted by post-hoc tests, with
        indices matching the labels in the ranks argument.

    ax : matplotlib.SubplotBase, optional
        The object in which the plot will be built. Gets the current Axes
        by default (if None is passed).

    label_fmt_left : str, optional
        The format string to apply to the labels on the left side. The keywords
        label and rank can be used to specify the sample/estimator name and
        rank value, respectively, by default '{label} ({rank:.2g})'.

    label_fmt_right : str, optional
        The same, but for the labels on the right side of the plot.
        By default '({rank:.2g}) {label}'.

    label_props : dict, optional
        Parameters to be passed to pyplot.text() when creating the labels,
        by default None.

    marker_props : dict, optional
        Parameters to be passed to pyplot.scatter() when plotting the rank
        markers on the axis, by default None.

    elbow_props : dict, optional
        Parameters to be passed to pyplot.plot() when creating the elbow lines,
        by default None.

    crossbar_props : dict, optional
        Parameters to be passed to pyplot.plot() when creating the crossbars
        that indicate lack of statistically significant difference. By default
        None.

    text_h_margin : float, optional
        Space between the text labels and the nearest vertical line of an
        elbow, by default 0.01.

    Returns
    -------
    dict[str, list[matplotlib.Artist]]
        Lists of Artists created.

    Examples
    --------
    See the :doc:`/tutorial`.

    References
    ----------
    .. [1] Demšar, J. (2006). Statistical comparisons of classifiers over multiple
            data sets. The Journal of Machine learning research, 7, 1-30.

    .. [2] https://mirkobunse.github.io/CriticalDifferenceDiagrams.jl/stable/
    """
    elbow_props = elbow_props or {}
    marker_props = {"zorder": 3, **(marker_props or {})}
    label_props = {"va": "center", **(label_props or {})}
    crossbar_props = {
        "color": "k",
        "zorder": 3,
        "linewidth": 2,
        **(crossbar_props or {}),
    }

    ax = ax or pyplot.gca()
    ax.yaxis.set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.xaxis.set_ticks_position("top")
    ax.spines["top"].set_position("zero")

    # lists of artists to be returned
    markers = []
    elbows = []
    labels = []
    crossbars = []

    # True if pairwise comparison is NOT significant
    adj_matrix = DataFrame(
        1 - sign_array(sig_matrix, alpha=alpha),
        index=sig_matrix.index,
        columns=sig_matrix.columns,
        dtype=bool,
    )

    ranks = Series(ranks)  # Standardize if ranks is dict
    points_left, points_right = np.array_split(ranks.sort_values(), 2)

    # Sets of points under the same crossbar
    crossbar_sets = _find_maximal_cliques(adj_matrix)

    # Sort by lowest rank and filter single-valued sets
    crossbar_sets = sorted(
        (x for x in crossbar_sets if len(x) > 1), key=lambda x: ranks[list(x)].min()
    )

    # Create stacking of crossbars: for each level, try to fit the crossbar,
    # so that it does not intersect with any other in the level. If it does not
    # fit in any level, create a new level for it.
    crossbar_levels: list[list[set]] = []
    for bar in crossbar_sets:
        for level, bars_in_level in enumerate(crossbar_levels):
            if not any(bool(bar & bar_in_lvl) for bar_in_lvl in bars_in_level):
                ypos = -level - 1
                bars_in_level.append(bar)
                break
        else:
            ypos = -len(crossbar_levels) - 1
            crossbar_levels.append([bar])

        crossbars.append(
            ax.plot(
                # Adding a separate line between each pair enables showing a
                # marker over each elbow with crossbar_props={'marker': 'o'}.
                [ranks[i] for i in bar],
                [ypos] * len(bar),
                **crossbar_props,
            )
        )

    lowest_crossbar_ypos = -len(crossbar_levels)

    def plot_items(points, xpos, label_fmt, label_props):
        """Plot each marker + elbow + label."""
        ypos = lowest_crossbar_ypos - 1
        for label, rank in points.items():
            elbow, *_ = ax.plot(
                [xpos, rank, rank],
                [ypos, ypos, 0],
                **elbow_props,
            )
            elbows.append(elbow)
            curr_color = elbow.get_color()
            markers.append(ax.scatter(rank, 0, **{"color": curr_color, **marker_props}))
            labels.append(
                ax.text(
                    xpos,
                    ypos,
                    label_fmt.format(label=label, rank=rank),
                    **{"color": curr_color, **label_props},
                )
            )
            ypos -= 1

    plot_items(
        points_left,
        xpos=points_left.iloc[0] - text_h_margin,
        label_fmt=label_fmt_left,
        label_props={"ha": "right", **label_props},
    )
    plot_items(
        points_right[::-1],
        xpos=points_right.iloc[-1] + text_h_margin,
        label_fmt=label_fmt_right,
        label_props={"ha": "left", **label_props},
    )

    return {
        "markers": markers,
        "elbows": elbows,
        "labels": labels,
        "crossbars": crossbars,
    }


def draw_cd_diagram(
    df: pd.DataFrame,
    method_column: str,
    rank_column: str,
    alpha: float = 0.05,
    title: str = None,
    folder: str = None,
):
    """
    :param df: dataframe that contains all methods results
    :param method_column: column that contains the method name
    :param rank_column: column that contains the rank, values should be in [0, 1] where lower is better.
    :param alpha: statistical significancy for statistical tests
    :param title: title of the figure
    :param folder: folder to write the figure to
    :return:
    """
    avg_rank = (
        df[[method_column, rank_column]].groupby(method_column).mean()[rank_column]
    )
    test_results_wilcox = sp.posthoc_wilcoxon(
        df, val_col=rank_column, group_col=method_column, p_adjust="holm"
    )
    fig, ax = plt.subplots(figsize=(9, 3))
    cdd = critical_difference_diagram(
        avg_rank,
        test_results_wilcox,
        ax=ax,
        alpha=alpha,
        label_props={"color": "black", "fontweight": "bold"},
        crossbar_props={"color": "black", "marker": "."},
        marker_props={"marker": ".", "s": 1, "color": "black", "edgecolor": "black"},
        elbow_props={"color": "black"},
        label_fmt_left="{label}",
        label_fmt_right="{label}",
    )
    if title:
        font = {
            "family": "sans-serif",
            "color": "black",
            "weight": "normal",
            "size": 22,
        }
        fig.suptitle(title, fontdict=font)
    fig.tight_layout()

    folder = Path(folder) if folder is not None else Path("figures/")
    title = title.replace("@", "-").replace("%", "")
    filename = folder / f"cd-diagram-{title}.pdf"
    print(f"Saving critical diagram in {filename}")
    fig.savefig(filename, bbox_inches="tight")
