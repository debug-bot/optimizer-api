import ipywidgets as ipw
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from ipywidgets import GridspecLayout, AppLayout, Layout, HBox
from ipydatagrid import DataGrid
from .optimizer import Optimizer
import plotly.io as pio
from IPython.display import display, HTML
import io
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


import warnings

warnings.filterwarnings("ignore")

pio.templates.default = "plotly_dark"

bond_rating_order = [
    "AAA",
    "AA+",
    "AA",
    "AA-",
    "A+",
    "A",
    "A-",
    "BBB+",
    "BBB",
    "BBB-",
    "BB+",
    "BB",
    "BB-",
    "B+",
    "B",
    "B-",
    "CCC",
    "CC",
    "C",
]
maturity_order = [
    "Less than 1y",
    "1y-3y",
    "3y-5y",
    "5y-7y",
    "7y-10y",
    "Greater than 10y",
]
esg_order = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC"]


def flatten_double_dict(dictionary, parent_key="", sep="_"):
    flattened_dict = {}
    for key, value in dictionary.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        if isinstance(value, dict):
            flattened_dict.update(flatten_double_dict(value, new_key, sep=sep))
        else:
            flattened_dict[new_key] = value
    return flattened_dict


def update_subdicts(dictionary):
    for key, subdict in dictionary.items():
        keys_ = []
        for subkey, value in subdict.items():
            if value == 0.05:
                keys_.append(subkey)

        for key in keys_:
            subdict.pop(key, None)
        subdict["main"] = 0.05


class OptimizerApp:
    def __init__(self):
        self.data = []
        self.comparison = []
        self.history = []
        self.datagrid_hist = []
        self.datagrid1 = []
        self.datagrid2 = []
        self.datagrid3 = []
        self.datagrid4 = []
        self.datagrid5 = []
        self.datagrid6 = []
        self.datagrid7 = []
        self.datagrid8 = []
        self.show_mapping = 0
        self.solution = False
        self.error = None
        self.message = ""

    def get_starting_data(self, df):
        self.df = df.copy()
        try:
            output = self.df[
                [
                    "ISIN",
                    "SecDes",
                    "Ticker",
                    "Issuer",
                    "Sector",
                    "Subsector",
                    "Seniority",
                    "MaturityB",
                    "Issuer Country",
                    "ESG_RATING",
                    "SBR",
                    "WARF",
                    "Decarb",
                    "Curr. Spread",
                    "Yield",
                    "Duration",
                    "YTM",
                    "SRC",
                    "ESG_SCORE",
                    "CI",
                ]
            ]
        except:
            output = self.df[
                [
                    "ISIN",
                    "Ticker",
                    "Sector",
                    "Seniority",
                    "MaturityB",
                    "Issuer Country",
                    "ESG_RATING",
                    "SBR",
                    "WARF",
                    "Decarb",
                    "Curr. Spread",
                    "Yield",
                    "Duration",
                    "YTM",
                    "SRC",
                    "ESG_SCORE",
                    "CI",
                ]
            ]

        self.data = output.copy()

        self.df_1 = (
            pd.DataFrame(
                self.df.groupby(["Sector"])["Notional Amount"].sum()
                * 100
                / self.df["Notional Amount"].sum()
            )
            .rename(columns={"Notional Amount": "Percentage before optimization"})
            .sort_values("Percentage before optimization", ascending=False)
        )
        self.df_1 = self.df_1.reset_index()
        self.df_1 = self.df_1.rename(columns={"Sector": "Sector of bonds"})
        # self.df_1 = self.df_1.set_index("Sector of bonds")

        self.df_1["Percentage before optimization"] = self.df_1[
            "Percentage before optimization"
        ].apply(lambda x: np.round(x,2))

        self.df_2 = (
            pd.DataFrame(
                self.df.groupby(["Seniority"])["Notional Amount"].sum()
                * 100
                / self.df["Notional Amount"].sum()
            )
            .rename(columns={"Notional Amount": "Percentage before optimization"})
            .sort_values("Percentage before optimization", ascending=False)
        )

        self.df_2["Percentage before optimization"] = self.df_2[
            "Percentage before optimization"
        ].apply(lambda x: np.round(x,2))

        self.df_3 = (
            pd.DataFrame(
                self.df.groupby(["SBR"])["Notional Amount"].sum()
                * 100
                / self.df["Notional Amount"].sum()
            )
            .rename(columns={"Notional Amount": "Percentage before optimization"})
            .sort_values("Percentage before optimization", ascending=False)
        )

        self.df_3["Percentage before optimization"] = self.df_3[
            "Percentage before optimization"
        ].apply(lambda x: np.round(x,2))
        self.df_3 = self.df_3.reindex(bond_rating_order).dropna()

        self.df_4 = (
            pd.DataFrame(
                self.df.groupby(["ESG_RATING"])["Notional Amount"].sum()
                * 100
                / self.df["Notional Amount"].sum()
            )
            .rename(columns={"Notional Amount": "Percentage before optimization"})
            .sort_values("Percentage before optimization", ascending=False)
        )

        self.df_4["Percentage before optimization"] = self.df_4[
            "Percentage before optimization"
        ].apply(lambda x: np.round(x,2))
        self.df_4 = self.df_4.reindex(esg_order)

        self.df_5 = (
            pd.DataFrame(
                self.df.groupby(["Issuer Country"])["Notional Amount"].sum()
                * 100
                / self.df["Notional Amount"].sum()
            )
            .rename(columns={"Notional Amount": "Percentage before optimization"})
            .sort_values("Percentage before optimization", ascending=False)
        )

        self.df_5["Percentage before optimization"] = self.df_5[
            "Percentage before optimization"
        ].apply(lambda x: np.round(x,2))

        self.df_6 = (
            pd.DataFrame(
                self.df.groupby(["MaturityB"])["Notional Amount"].sum()
                * 100
                / self.df["Notional Amount"].sum()
            )
            .rename(columns={"Notional Amount": "Percentage before optimization"})
            .sort_values("Percentage before optimization", ascending=False)
        )

        self.df_6["Percentage before optimization"] = self.df_6[
            "Percentage before optimization"
        ].apply(lambda x: np.round(x,2))
        self.df_6 = self.df_6.reindex(maturity_order)

        self.df_7 = (
            pd.DataFrame(
                self.df.groupby(["Ticker"])["Notional Amount"].sum()
                * 100
                / self.df["Notional Amount"].sum()
            )
            .rename(columns={"Notional Amount": "Percentage before optimization"})
            .sort_values("Percentage before optimization", ascending=False)
        )

        self.df_7["Percentage before optimization"] = self.df_7[
            "Percentage before optimization"
        ].apply(lambda x: np.round(x,2))

        # if 'Cashflow' in self.df.columns:
        #     self.df_9 = self.df.drop_duplicates(subset=["MaturityYear"])[["MaturityYear","Cashflow"]].sort_values(by="MaturityYear").set_index('MaturityYear').rename(columns={"Cashflow":"Cashflow before optimization"})
        #     fig9 = go.Figure()
        #     fig9.add_trace(go.Bar(x=self.df_9.index, y=self.df_9['Cashflow before optimization']))
        #     self.axs9 = go.FigureWidget(data = fig9)
        #     self.df_9['Cashflow before optimization'] = self.df_9['Cashflow before optimization'].apply(lambda x : np.round(x,2))
        #     self.datagrid9 = DataGrid(self.df_9.sort_index(ascending=True),editable = True,layout=ipw.Layout(width = "auto",height = "1000px"))
        #     self.datagrid9.auto_fit_columns = True
        #     self.widgets["CashFlows"] = self.datagrid9
        # else:
        #     self.widgets["CashFlows_"] = ipw.Output()

        self.df_8 = pd.DataFrame(
            {
                "Metrics": [
                    "Yield",
                    "Duration",
                    "Maturity",
                    "ESG_SCORE",
                    "CI",
                    "Decarb",
                    "WARF",
                ],
                "Average": [
                    (self.df["Yield"] * self.df["Notional Amount"]).sum()
                    / self.df["Notional Amount"].sum(),
                    # (self.df["Curr. Spread"] *  self.df['Notional Amount']).sum()/self.df['Notional Amount'].sum(),
                    (self.df["Duration"] * self.df["Notional Amount"]).sum()
                    / self.df["Notional Amount"].sum(),
                    (self.df["YTM"] * self.df["Notional Amount"]).sum()
                    / self.df["Notional Amount"].sum(),
                    # (self.df["SRC"] *  self.df['Notional Amount']).sum()/self.df['Notional Amount'].sum(),
                    (self.df["ESG_SCORE"] * self.df["Notional Amount"]).sum()
                    / self.df["Notional Amount"].sum(),
                    (self.df["CI"] * self.df["Notional Amount"]).sum()
                    / self.df["Notional Amount"].sum(),
                    (self.df["Decarb"] * self.df["Notional Amount"]).sum()
                    / self.df["Notional Amount"].sum(),
                    (self.df["WARF"] * self.df["Notional Amount"]).sum()
                    / self.df["Notional Amount"].sum(),
                ],
            }
        ).rename(columns={"Average": "Average before optimization"})
        # round to 2 decimal places Average before optimization
        self.df_8["Average before optimization"] = self.df_8[
            "Average before optimization"
        ].apply(lambda x: np.round(x, 2))

        return self.get_data()

    def get_data(self):

        try:
            
            sectors = self.df_1.reset_index().rename(columns={"Sector of bonds_x": "name", "Percentage before optimization": "pbo", "Percentage after optimization": "pao", "Sector of bonds": "name"}).to_dict(orient="records")
            seniorities = self.df_2.reset_index().rename(columns={"Seniority": "name", "Percentage before optimization": "pbo", "Percentage after optimization": "pao"}).to_dict(orient="records")
            ratings = self.df_3.reset_index().rename(columns={"SBR": "name", "Percentage before optimization": "pbo", "Percentage after optimization": "pao"}).to_dict(orient="records")
            esg_ratings = self.df_4.reset_index().rename(columns={"ESG_RATING": "name", "Percentage before optimization": "pbo", "Percentage after optimization": "pao"}).to_dict(orient="records")
            countries = self.df_5.reset_index().rename(columns={"Issuer Country": "name", "Percentage before optimization": "pbo", "Percentage after optimization": "pao"}).to_dict(orient="records")
            maturities = self.df_6.reset_index().rename(columns={"MaturityB": "name", "Percentage before optimization": "pbo", "Percentage after optimization": "pao"}).to_dict(orient="records")
            tickers = self.df_7.reset_index().rename(columns={"Ticker": "name", "Percentage before optimization": "pbo", "Percentage after optimization": "pao"}).to_dict(orient="records")
            comparison = self.df_8.reset_index().rename(columns={"Metrics_x": "name", "Average before optimization": "abo", "Average after optimization": "aao", "Metrics": "name"}).to_dict(orient="records")
            try:
                old_history = self.hist_df.reset_index().to_dict(orient="records")
                # Convert the data into the desired format
                history = []
                for hist in old_history:
                    for key, value in hist.items():
                        # Check if the value is a number and round it if it is
                        if isinstance(value, (int, float)):
                            value = round(value, 2)
                        history.append({"key": key, "simulation": value})
            except:
                history = []

            # combine all this data into a single dictionary and return it so that can be sent as response to the frontend
            optimizer_data = {
                "sectors": sectors,
                "seniorities": seniorities,
                "ratings": ratings,
                "esg_ratings": esg_ratings,
                "countries": countries,
                "maturities": maturities,
                "tickers": tickers,
                "comparison": comparison,
                "history": history,
                "error": self.error,
                "message": self.message,
                "solution": self.solution,
            }
        except:
            optimizer_data = {
                "sectors": [],
                "seniorities": [],
                "ratings": [],
                "esg_ratings": [],
                "countries": [],
                "maturities": [],
                "tickers": [],
                "comparison": [],
                "history": [],
                "error": self.error,
                "message": self.message,
                "solution": self.solution,
            }

        return optimizer_data

    def get_optimizer_data(
        self, metrics, buffers, filters_metrics, filters_groups, simulation_name, df
    ):
        self.df = df.copy()
        self.metrics = metrics
        self.buffers = buffers
        self.filters_metrics = filters_metrics
        self.filters_groups = filters_groups
        self.simulation_name = simulation_name
        try:
            self.run_optimizer()
        except Exception as e:
            self.error = f"An error occurred: {str(e)}"
            self.message = "Optimization failed. Please try again."
            print(f"An error occurred: {str(e)}")
        return self.get_data()

    def read_data(self):
        return (self.metrics, self.buffers, self.filters_metrics, self.filters_groups)

    def run_optimizer(self):

        # try:

        metrics, buffers, filters_metrics, filters_groups = self.read_data()

        # save all above prints to a txt file
        # with open('metrics.py', 'w') as f:
        #     print('metrics=',metrics, file=f)
        #     print('buffers=',buffers, file=f)
        #     print('filters_metrics=',filters_metrics, file=f)
        #     print('filters_groups=',filters_groups, file=f)

        if metrics["MaxMin"] == "Maximize":
            maxmin = True
        else:
            maxmin = False

        df_filtered = self.df.copy()
        df_filtered = df_filtered[
                (df_filtered["Yield"] <= filters_metrics["Yield_upper_filter"])
                & (df_filtered["Yield"] >= filters_metrics["Yield_lower_filter"])
                & (
                    df_filtered["Curr. Spread"]
                    <= filters_metrics["Spread_upper_filter"]
                )
                & (
                    df_filtered["Curr. Spread"]
                    >= filters_metrics["Spread_lower_filter"]
                )
                & (df_filtered["Duration"] <= filters_metrics["Duration_upper_filter"])
                & (df_filtered["Duration"] >= filters_metrics["Duration_lower_filter"])
                & (df_filtered["SRC"] <= filters_metrics["SCR_upper_filter"])
                & (df_filtered["SRC"] >= filters_metrics["SCR_lower_filter"])
                & (
                    df_filtered["ESG_SCORE"]
                    <= filters_metrics["ESG_SCORE_upper_filter"]
                )
                & (
                    df_filtered["ESG_SCORE"]
                    >= filters_metrics["ESG_SCORE_lower_filter"]
                )
                & (df_filtered["CI"] <= filters_metrics["CI_upper_filter"])
                & (df_filtered["CI"] >= filters_metrics["CI_lower_filter"])
                & (df_filtered["YTM"] <= filters_metrics["Maturity_upper_filter"])
                & (df_filtered["YTM"] >= filters_metrics["Maturity_lower_filter"])
                & (df_filtered["WARF"] <= filters_metrics["WARF_upper_filter"])
                & (df_filtered["WARF"] >= filters_metrics["WARF_lower_filter"])
            ]

        for key, subdict in filters_groups.items():
            filters_groups[key] = [x for x in subdict.keys() if subdict[x] is True]

        subkeys_to_keep = [
                value for sublist in filters_groups.values() for value in sublist
            ]

        filtered_buffers = {
                key: {
                    subkey: buffers[key][subkey]
                    for subkey in subkeys_to_keep
                    if subkey in buffers[key]
                }
                for key in buffers
            }

        # if 'Cashflow' in self.df.columns:
        #     filtered_buffers['buffer_Cashflows'] = buffers['buffer_Cashflows']

        df_filtered = df_filtered[
                (df_filtered["Sector"].isin(filters_groups["Sectors_filter"]))
                & (df_filtered["SBR"].isin(filters_groups["Ratings_filter"]))
                & (df_filtered["Seniority"].isin(filters_groups["Seniority_filter"]))
                & (df_filtered["MaturityB"].isin(filters_groups["Maturity_filter"]))
                & (df_filtered["Issuer Country"].isin(filters_groups["Country_filter"]))
                & (df_filtered["ESG_RATING"].isin(filters_groups["ESG_RATING_filter"]))
                & (df_filtered["Ticker"].isin(filters_groups["Ticker_filter"]))
            ]

        OP = Optimizer(
                thresholds={
                    "Yield": [metrics["Yield_lower"], metrics["Yield_upper"]],
                    "Spreads": [metrics["Spread_lower"], metrics["Spread_upper"]],
                    "Duration": [metrics["Duration_lower"], metrics["Duration_upper"]],
                    "Maturity": [metrics["Maturity_lower"], metrics["Maturity_upper"]],
                    "Risk Charge": [metrics["SCR_lower"], metrics["SCR_upper"]],
                    "ESG_SCORE": [
                        metrics["ESG_SCORE_lower"],
                        metrics["ESG_SCORE_upper"],
                    ],
                    "CI": [metrics["CI_lower"], metrics["CI_upper"]],
                    "WARF": [metrics["WARF_lower"], metrics["WARF_upper"]],
                    "Decarb": [metrics["Decarb_lower"], metrics["Decarb_upper"]],
                    "PnL": [metrics["PnL_lower"], metrics["PnL_upper"]],
                    "Weight": [metrics["weight_lower"], metrics["weight_upper"]],
                },
                buffers=filtered_buffers,
                weights=[metrics["weight_lower"], metrics["weight_upper"]],
                recommendation=metrics["recommendation"],
                turnover=metrics["turnover"],
                nonzero=metrics["nonzero"],
                size=metrics["size"],
                unit=metrics["unit"],
                fixed_size=metrics["fixed_size"],
            )

        if "Cashflow" in self.df.columns:
            output, too_strict, order, multi, bounds = OP.optimize(
                    df_filtered.copy(),
                    total=metrics["size"],
                    var=metrics["Objet"],
                    maximize=maxmin,
                    optimizer=metrics["solver"],
                    output_strict=True,
                    constraints=["buffer_Sectors"],
                )
        else:
            output, too_strict, order, multi, bounds = OP.optimize(
                    df_filtered.copy(),
                    total=metrics["size"],
                    var=metrics["Objet"],
                    maximize=maxmin,
                    optimizer=metrics["solver"],
                    output_strict=True,
                    constraints=[
                        "buffer_Sectors",
                        "buffer_Ratings",
                        "buffer_Seniorities",
                        "buffer_Maturities",
                        "buffer_Countries",
                        "buffer_ESG_Ratings",
                        "buffer_Tickers",
                        "Duration",
                        "Yield",
                        "Spreads",
                        "WARF",
                        "Decarb",
                        "ESG_SCORE",
                        "Risk Charge",
                        "CI",
                        "Maturity",
                        "size",
                        "nonzero",
                    ],
                )

        log = {}

        metrics["turnover_lower"] = metrics["turnover"][0]
        metrics["turnover_upper"] = metrics["turnover"][1]
        del metrics["turnover"]

        if too_strict == 0:

            self.output_df = output

            df_1 = (
                    pd.DataFrame(output.groupby(["Sector"])["final_wt"].sum() * 100)
                    .rename(columns={"final_wt": "Percentage after optimization"})
                    .sort_values("Percentage after optimization", ascending=False)
                )
            df_1 = df_1.reset_index()
            df_1 = df_1.rename(columns={"Sector": "Sector of bonds"})
            # df_1 = df_1.set_index("Sector of bonds")
            fig1 = go.Figure()
            self.df_1 = (
                    pd.DataFrame(
                        output.groupby(["Sector"])["Notional Amount"].sum()
                        * 100
                        / output["Notional Amount"].sum()
                    )
                    .rename(
                        columns={"Notional Amount": "Percentage before optimization"}
                    )
                    .sort_values("Percentage before optimization", ascending=False)
                    .dropna()
                )
            self.df_1["Percentage before optimization"] = self.df_1[
                    "Percentage before optimization"
                ].apply(lambda x: np.round(x,2))
            self.df_1 = self.df_1.reset_index()
            self.df_1 = self.df_1.rename(columns={"Sector": "Sector of bonds"})
            # self.df_1 = self.df_1.set_index("Sector of bonds")

            df_1["Percentage after optimization"] = df_1[
                    "Percentage after optimization"
                ].apply(lambda x: np.round(x,2))
            df_1 = pd.merge(self.df_1, df_1, left_index=True, right_index=True)
            df_1 = df_1.rename(index={"Sector": "Sector of bonds"})

            df_2 = (
                    pd.DataFrame(output.groupby(["Seniority"])["final_wt"].sum() * 100)
                    .rename(columns={"final_wt": "Percentage after optimization"})
                    .sort_values("Percentage after optimization", ascending=False)
                )
            self.df_2 = (
                    pd.DataFrame(
                        output.groupby(["Seniority"])["Notional Amount"].sum()
                        * 100
                        / output["Notional Amount"].sum()
                    )
                    .rename(
                        columns={"Notional Amount": "Percentage before optimization"}
                    )
                    .sort_values("Percentage before optimization", ascending=False)
                    .dropna()
                )
            self.df_2["Percentage before optimization"] = self.df_2[
                    "Percentage before optimization"
                ].apply(lambda x: np.round(x,2))

            df_2["Percentage after optimization"] = df_2[
                    "Percentage after optimization"
                ].apply(lambda x: np.round(x,2))
            df_2 = pd.merge(self.df_2, df_2, left_index=True, right_index=True)

            df_3 = (
                    pd.DataFrame(output.groupby(["SBR"])["final_wt"].sum() * 100)
                    .rename(columns={"final_wt": "Percentage after optimization"})
                    .sort_values("Percentage after optimization", ascending=False)
                )
            self.df_3 = (
                    pd.DataFrame(
                        output.groupby(["SBR"])["Notional Amount"].sum()
                        * 100
                        / output["Notional Amount"].sum()
                    )
                    .rename(
                        columns={"Notional Amount": "Percentage before optimization"}
                    )
                    .sort_values("Percentage before optimization", ascending=False)
                )
            self.df_3["Percentage before optimization"] = self.df_3[
                    "Percentage before optimization"
                ].apply(lambda x: np.round(x,2))
            self.df_3 = self.df_3.reindex(bond_rating_order).dropna()

            df_3["Percentage after optimization"] = df_3[
                    "Percentage after optimization"
                ].apply(lambda x: np.round(x,2))
            df_3 = pd.merge(self.df_3, df_3, left_index=True, right_index=True)

            df_4 = (
                    pd.DataFrame(output.groupby(["ESG_RATING"])["final_wt"].sum() * 100)
                    .rename(columns={"final_wt": "Percentage after optimization"})
                    .sort_values("Percentage after optimization", ascending=False)
                )
            self.df_4 = (
                    pd.DataFrame(
                        output.groupby(["ESG_RATING"])["Notional Amount"].sum()
                        * 100
                        / output["Notional Amount"].sum()
                    )
                    .rename(
                        columns={"Notional Amount": "Percentage before optimization"}
                    )
                    .sort_values("Percentage before optimization", ascending=False)
                )
            self.df_4["Percentage before optimization"] = self.df_4[
                    "Percentage before optimization"
                ].apply(lambda x: np.round(x,2))
            self.df_4 = self.df_4.reindex(esg_order).dropna()

            df_4["Percentage after optimization"] = df_4[
                    "Percentage after optimization"
                ].apply(lambda x: np.round(x,2))
            df_4 = pd.merge(self.df_4, df_4, left_index=True, right_index=True)

            df_5 = (
                    pd.DataFrame(
                        output.groupby(["Issuer Country"])["final_wt"].sum() * 100
                    )
                    .rename(columns={"final_wt": "Percentage after optimization"})
                    .sort_values("Percentage after optimization", ascending=False)
                )
            df_5["Percentage after optimization"] = df_5[
                    "Percentage after optimization"
                ].apply(lambda x: np.round(x,2))
            self.df_5 = (
                    pd.DataFrame(
                        output.groupby(["Issuer Country"])["Notional Amount"].sum()
                        * 100
                        / output["Notional Amount"].sum()
                    )
                    .rename(
                        columns={"Notional Amount": "Percentage before optimization"}
                    )
                    .sort_values("Percentage before optimization", ascending=False)
                    .dropna()
                )
            self.df_5["Percentage before optimization"] = self.df_5[
                    "Percentage before optimization"
                ].apply(lambda x: np.round(x,2))
            df_5 = pd.merge(self.df_5, df_5, left_index=True, right_index=True)

            df_6 = (
                    pd.DataFrame(output.groupby(["MaturityB"])["final_wt"].sum() * 100)
                    .rename(columns={"final_wt": "Percentage after optimization"})
                    .sort_values("Percentage after optimization", ascending=False)
                )
            self.df_6 = (
                    pd.DataFrame(
                        output.groupby(["MaturityB"])["Notional Amount"].sum()
                        * 100
                        / output["Notional Amount"].sum()
                    )
                    .rename(
                        columns={"Notional Amount": "Percentage before optimization"}
                    )
                    .sort_values("Percentage before optimization", ascending=False)
                )
            self.df_6["Percentage before optimization"] = self.df_6[
                    "Percentage before optimization"
                ].apply(lambda x: np.round(x,2))
            self.df_6 = self.df_6.reindex(maturity_order).dropna()

            df_6["Percentage after optimization"] = df_6[
                    "Percentage after optimization"
                ].apply(lambda x: np.round(x,2))
            df_6 = pd.merge(self.df_6, df_6, left_index=True, right_index=True)

            df_7 = (
                    pd.DataFrame(output.groupby(["Ticker"])["final_wt"].sum() * 100)
                    .rename(columns={"final_wt": "Percentage after optimization"})
                    .sort_values("Percentage after optimization", ascending=False)
                )
            self.df_7 = (
                    pd.DataFrame(
                        output.groupby(["Ticker"])["Notional Amount"].sum()
                        * 100
                        / output["Notional Amount"].sum()
                    )
                    .rename(
                        columns={"Notional Amount": "Percentage before optimization"}
                    )
                    .sort_values("Percentage before optimization", ascending=False)
                    .dropna()
                )
            self.df_7["Percentage before optimization"] = self.df_7[
                    "Percentage before optimization"
                ].apply(lambda x: np.round(x,2))
            df_7["Percentage after optimization"] = df_7[
                    "Percentage after optimization"
                ].apply(lambda x: np.round(x,2))
            df_7 = pd.merge(self.df_7, df_7, left_index=True, right_index=True)
            print(df_7.head())
            print(df_7.to_dict(orient="index"))

            self.datagrid7 = DataGrid(
                    df_7.sort_index(ascending=True),
                    editable=True,
                    layout=ipw.Layout(width="auto", height="1000px"),
                )
            self.datagrid7.auto_fit_columns = True

            output["initial"] = output["Notional Amount"]
            output["change"] = output["final"] - output["initial"]

            df_8 = pd.DataFrame(
                    {
                        "Metrics": [
                            "Yield",
                            "Duration",
                            "Maturity",
                            "ESG_SCORE",
                            "CI",
                            "Decarb",
                            "WARF",
                        ],
                        "Average after optimization": [
                            (output["Yield"] * output["final_wt"]).sum(),
                            (output["Duration"] * output["final_wt"]).sum(),
                            (output["YTM"] * output["final_wt"]).sum(),
                            (output["ESG_SCORE"] * output["final_wt"]).sum(),
                            (output["CI"] * output["final_wt"]).sum(),
                            (output["Decarb"] * output["final_wt"]).sum(),
                            (output["WARF"] * output["final_wt"]).sum(),
                        ],
                    }
                )
            log.update(
                    {
                        "Yield": (output["Yield"] * output["final_wt"]).sum(),
                        "Duration": (output["Duration"] * output["final_wt"]).sum(),
                        "Maturity": (output["YTM"] * output["final_wt"]).sum(),
                        "ESG_SCORE": (output["ESG_SCORE"] * output["final_wt"]).sum(),
                        "CI": (output["CI"] * output["final_wt"]).sum(),
                        "Decarb": (output["Decarb"] * output["final_wt"]).sum(),
                        "WARF": (output["WARF"] * output["final_wt"]).sum(),
                    }
                )

            log["Simulation Name"] = self.simulation_name

            self.history.append(log)
            hist_df = pd.DataFrame(self.history)

            duplicates = hist_df.duplicated("Simulation Name")
            counts = hist_df.groupby("Simulation Name").cumcount() + 1
            hist_df.loc[duplicates, "Simulation Name"] = (
                    hist_df.loc[duplicates, "Simulation Name"]
                    + "_"
                    + counts.astype(str)
                )

            # hist_df = hist_df.set_index("Simulation Name")
            self.df_8 = (
                    pd.DataFrame(
                        {
                            "Metrics": [
                                "Yield",
                                "Duration",
                                "Maturity",
                                "ESG_SCORE",
                                "CI",
                                "Decarb",
                                "WARF",
                            ],
                            "Average": [
                                (output["Yield"] * output["Notional Amount"]).sum()
                                / output["Notional Amount"].sum(),
                                # (output["Curr. Spread"] *  output['Notional Amount']).sum()/output['Notional Amount'].sum(),
                                (output["Duration"] * output["Notional Amount"]).sum()
                                / output["Notional Amount"].sum(),
                                (output["YTM"] * output["Notional Amount"]).sum()
                                / output["Notional Amount"].sum(),
                                # (output["SRC"] *  output['Notional Amount']).sum()/output['Notional Amount'].sum(),
                                (output["ESG_SCORE"] * output["Notional Amount"]).sum()
                                / output["Notional Amount"].sum(),
                                (output["CI"] * output["Notional Amount"]).sum()
                                / output["Notional Amount"].sum(),
                                (output["Decarb"] * output["Notional Amount"]).sum()
                                / output["Notional Amount"].sum(),
                                (output["WARF"] * output["Notional Amount"]).sum()
                                / output["Notional Amount"].sum(),
                            ],
                        }
                    ).rename(columns={"Average": "Average before optimization"})
                    
                )

            df_8 = pd.merge(self.df_8, df_8, left_index=True, right_index=True)
            # round 2nd and 3rd columns to 2 decimal places
            df_8["Average before optimization"] = df_8[
                    "Average before optimization"
                ].apply(lambda x: np.round(x, 2))
            df_8["Average after optimization"] = df_8[
                    "Average after optimization"
                ].apply(lambda x: np.round(x, 2))

            self.message = "Solution found !"
            self.solution = True

            try:
                output = output[
                        [
                            "ISIN",
                            "SecDes",
                            "Ticker",
                            "Issuer",
                            "Sector",
                            "Subsector",
                            "Seniority",
                            "MaturityB",
                            "Issuer Country",
                            "ESG_RATING",
                            "SBR",
                            "WARF",
                            "Decarb",
                            "Curr. Spread",
                            "Yield",
                            "Duration",
                            "YTM",
                            "SRC",
                            "ESG_SCORE",
                            "CI",
                            "Notional Amount",
                            "initial_wt",
                            "final_wt",
                            "final",
                        ]
                    ]
            except:
                output = output[
                        [
                            "ISIN",
                            "Ticker",
                            "Sector",
                            "Seniority",
                            "MaturityB",
                            "Issuer Country",
                            "ESG_RATING",
                            "SBR",
                            "WARF",
                            "Decarb",
                            "Curr. Spread",
                            "Yield",
                            "Duration",
                            "YTM",
                            "SRC",
                            "ESG_SCORE",
                            "CI",
                            "Notional Amount",
                            "initial_wt",
                            "final_wt",
                            "final",
                            "MaturityYear",
                        ]
                    ]

            prev_pf = set(output[output["initial_wt"] != 0]["ISIN"])
            curr_pf = set(output[output["final"] != 0]["ISIN"])
            changes = len(prev_pf.symmetric_difference(curr_pf))
            print("Turnover rate: ", changes / len(prev_pf) * 100)

            self.df_1 = df_1
            self.df_2 = df_2
            self.df_3 = df_3
            self.df_4 = df_4
            self.df_5 = df_5
            self.df_6 = df_6
            self.df_7 = df_7
            self.df_8 = df_8
            self.hist_df = hist_df

            print(self.df_8.head())
            print(self.hist_df.head())

        else:

            for key in bounds:
                try:
                    bounds[key] = np.round(bounds[key], 2)
                except:
                    for key_ in bounds[key]:
                        bounds[key][key_] = np.round(bounds[key][key_], 2)
            if metrics["recommendation"] == True:
                self.message = (
                        f"Optimal solution not found. Strict constraints : {[item for sublist in list(order .values()) for item in sublist] }."
                        + f"<br>Recommended thresholds: {bounds}"
                    )

            else:
                self.message = "Optimization failed. Please try again."

    # except Exception as e:
    #     self.error = f"An error occurred: {str(e)}"
    #     self.message = "Optimization failed. Please try again."
    #     print(e)


# df = pd.read_csv(r"data.csv")

# from output import *

# O = OptimizerApp()
# simulation_name = "Simulation"
# # starting_data = O.get_starting_data(df)
# optimizer_data = O.get_optimizer_data(
#     metrics, buffers, filters_metrics, filters_groups, simulation_name, df
# )
# # print(starting_data['comparison'], starting_data['history'])
# print('comparison', optimizer_data['comparison'][:2])
# print('history', optimizer_data['history'][:2])
# print('error', optimizer_data['error'])
# print('ticker', optimizer_data['tickers'][:2])
# print('sectors', optimizer_data['sectors'][:2])
