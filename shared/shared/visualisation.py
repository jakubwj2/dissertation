import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.figure import Figure
from matplotlib.lines import Line2D


def visualize_predictions(
    responses: np.ndarray,
    ids: np.ndarray,
    probabilities: np.ndarray,
    mask: np.ndarray,
    dataset_name: str,
    model_name: str,
) -> Figure:
    assert responses.shape == ids.shape == probabilities.shape == mask.shape, (
        "Shapes don't match"
    )

    responses = responses[mask]
    ids = ids[mask]
    probabilities = probabilities[mask]

    df = pd.DataFrame(
        {"ids": ids, "responses": responses, "probabilities": probabilities}
    )
    df["ids"] = df["ids"].astype(int)
    sorted_concepts = sorted(df["ids"].unique(), key=lambda x: int(x))

    fig, ax = plt.subplots(figsize=(16, 10))

    # knowledge tracing lines
    sns.lineplot(
        data=df,
        x=df.index,
        y="probabilities",
        hue="ids",
        hue_order=sorted_concepts,
        palette="tab10",
        ax=ax,
        legend=False,
    )

    colors = sns.color_palette("tab10", len(sorted_concepts))
    handles = [
        Line2D([], [], color=color, linewidth=1.5, label=concept)
        for color, concept in zip(colors, sorted_concepts)
    ]

    leg1 = ax.legend(
        handles=handles,
        labels=sorted_concepts,
        loc="lower right",
        title="Topic ID",
        title_fontsize=20,
        fontsize=12,
        ncol=2,
    )
    ax.add_artist(leg1)

    # response markers
    sns.scatterplot(
        data=df,
        x=df.index,
        y="probabilities",
        hue="responses",
        palette={True: "lime", False: "red"},
        marker="o",
        s=75,
        legend=False,
        ax=ax,
    )

    handle_config = {
        "xdata": [],
        "ydata": [],
        "marker": "o",
        "linestyle": "None",
        "markersize": 10,
    }

    leg2 = ax.legend(
        handles=[
            Line2D(color="lime", label="Correct", **handle_config),
            Line2D(color="red", label="Incorrect", **handle_config),
        ],
        loc="lower right",
        title="Responses",
        title_fontsize=20,
        fontsize=12,
        bbox_to_anchor=(0.85, 0),
    )
    # ax.add_artist(leg1)
    ax.add_artist(leg2)

    # mastery threshold line
    num_concepts = len(ids)
    sns.lineplot(
        x=[-num_concepts * 0.025, num_concepts * 1.025],
        y=[0.5, 0.5],
        color="gray",
        linestyle="--",
        ax=ax,
    )

    ax.set_ylim(0, 1)
    ax.set_xlim(-num_concepts * 0.05, num_concepts * 1.05)
    ax.set_ylabel("Predicted Mastery", fontsize=20)
    ax.set_xlabel("Attempt Index", fontsize=20)
    ax.set_title(
        f"Mastery for One Student ({model_name.upper()}, {dataset_name.upper()})",
        size=35,
    )

    return fig
