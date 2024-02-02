import ipywidgets as ipw
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from ipywidgets import GridspecLayout, AppLayout, Layout, HBox
from ipydatagrid import DataGrid
from optimizer import *
import plotly.io as pio
from IPython.display import display, HTML
import io
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import warnings
warnings.filterwarnings('ignore')

pio.templates.default = "plotly_dark"

bond_rating_order = ['AAA', 'AA+', 'AA', 'AA-', 'A+', 'A', 'A-', 'BBB+', 'BBB', 'BBB-', 'BB+','BB','BB-','B+','B','B-','CCC','CC','C']   
maturity_order = ['Less than 1y', '1y-3y', '3y-5y', '5y-7y', '7y-10y', 'Greater than 10y']
esg_order = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC']

df = pd.read_csv(r"data.csv")

def flatten_double_dict(dictionary, parent_key='', sep='_'):
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
        subdict['main'] = 0.05

class optimizerAPP(ipw.VBox,ipw.HBox):
    
    def __init__(self):
        
        super().__init__()
        self.widgets = {}
        self.datagrid = []
        self.data = []
        self.df = df.copy()
        self.axs1 = []
        self.axs2 = []
        self.axs3 = []
        self.axs4 = []
        self.axs5 = []
        self.axs6 = []
        self.axs7 = []
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
        self._build_view()
    
    def update_portfolio_dropdown(self,change):
        if self.widgets["salesbuys_"].value == 'Portfolio Sales':
            self.widgets["PORTFOLIO_"].disabled = False
            self.widgets["PORTFOLIO_"].options = ['GVIE FONDS GENERAL ASSURES', 'GVIE FONDS PROPRES', 'GVIE EURO EPARGNE', 'GVIE FRANCE 2', 'GENERALI IARD']
            self.widgets["PORTFOLIO_"].value = ('GVIE FONDS GENERAL ASSURES',)
            self.widgets["LabelPTF"].value = 'Portfolio'
        else:
            self.widgets["PORTFOLIO_"].disabled = False
            self.widgets["PORTFOLIO_"].options = ['EUR IG', 'EUR IG Sen', 'EUR HY']
            self.widgets["PORTFOLIO_"].value = ('EUR IG',)
            self.widgets["LabelPTF"].value = 'Index'
        
    def _build_view(self):
        
        custom_css = """
        <style>
            .p-Accordion .p-Widget.p-Accordion-child .p-Collapse-header {
                background-color: grey !important;
            }

            .custom-toggle-buttons .jupyter-widgets.widget-toggle-button button.widget-toggle-button {
                background-color: #4CAF50; /* Background color for selected button */
                color: #fff; /* Text color for selected button */
            }

            .custom-toggle-buttons .jupyter-widgets.widget-toggle-button button.widget-toggle-button:not(.active) {
                background-color: #ddd; /* Background color for not selected button */
                color: #333; /* Text color for not selected button */
            }
        </style>
        """
        
        display(HTML(custom_css))
        
        common_layout = Layout(width='auto', height='1600px')
        
        if self.show_mapping == 0:
                       
            self.widgets["MaxMin"] = ipw.ToggleButtons(value='Maximize', options=['Maximize', "Minimize"], layout=Layout(height='30px', width='auto'))
            self.widgets["salesbuys_"] = ipw.Dropdown(value='Purchases', options=['Portfolio Sales', 'Purchases', 'Arbitrages'], layout=Layout(height='30px', width='auto'))
            self.widgets["PORTFOLIO_"] = ipw.SelectMultiple(value=('EUR IG',), options=['EUR IG', 'EUR IG Sen', 'EUR HY'], layout=Layout(height='50px', width='auto'))
            #self.widgets["PORTFOLIO_"] = ipw.SelectMultiple(value=('GVIE FONDS GENERAL ASSURES',), options=['GVIE FONDS GENERAL ASSURES', 'GVIE FONDS PROPRES', 'GVIE EURO EPARGNE', 'GVIE FRANCE 2', 'GENERALI IARD'], layout=Layout(height='50px', width='auto'))
            self.widgets['Objet'] = ipw.Dropdown(value = 'Yield',options=['Yield', 
                                                                          'Duration', 
                                                                          'Total Return', 
                                                                          'Excess Return', 
                                                                          'Cash Flow Matching', 
                                                                          'Decarbonization', 
                                                                          'ESG Score',
                                                                          'Carbon Intensity (EVIC)',
                                                                          'Carbon Intensity (Sales)'
                                                                         ],
                                                 layout=Layout(height='30px', width='auto'))
            
            self.widgets['size'] = ipw.FloatText(value = int(self.df['Notional Amount'].sum()/1e9),description = 'Ptf. size, bn: ',step=1,
                                                style = {'description_width': '100px'},layout=Layout(height='auto', width='160px'))
            self.widgets['nonzero'] = ipw.FloatText(value = int(len(self.df)/2),description = 'Non zero weight: ',step=10,
                                                style = {'description_width': '100px'},layout=Layout(height='auto', width='160px'))
            self.widgets['turnover_lower'] = ipw.FloatText(value = 0,description = 'Turnover rate, %:',step=1,
                                                style = {'description_width': '100px'},layout=Layout(height='auto', width='160px'))
            
            self.widgets['turnover_upper'] = ipw.FloatText(value = 100,step=1,layout=Layout(height='auto', width='50px'))
            
            self.widgets['Yield_lower'] = ipw.FloatText(value = 0,description = 'Yield, %: ',step=0.1,
                                                style = {'description_width': '100px'},layout=Layout(height='auto', width='160px'))
            self.widgets['Yield_upper'] = ipw.FloatText(value = 5,layout=Layout(height='auto', width='50px'),step=0.1)
                    
            self.widgets['Spread_lower'] = ipw.FloatText(value = 0,description = 'ASW, bps: ',
                                                style = {'description_width': '100px'},layout=Layout(height='auto', width='160px'))
            self.widgets['Spread_upper'] = ipw.FloatText(value = 500,layout=Layout(height='auto', width='50px'))
            
            self.widgets['Duration_lower'] = ipw.FloatText(value = 0,description = 'Duration: ',
                                                style = {'description_width': '100px'},layout=Layout(height='auto', width='160px'),step=0.1)
            self.widgets['Duration_upper'] = ipw.FloatText(value = 10,layout=Layout(height='auto', width='50px'),step=0.1)
            
            self.widgets['Maturity_lower'] = ipw.FloatText(value = 0,description = 'Maturity, yrs: ',
                                                style = {'description_width': '100px'},layout=Layout(height='auto', width='160px'),step=0.1)
            self.widgets['Maturity_upper'] = ipw.FloatText(value = 10,layout=Layout(height='auto', width='50px'),step=0.1)
            
            self.widgets['SCR_lower'] = ipw.FloatText(value = 0,description = 'SCR, %: ',
                                                style = {'description_width': '100px'},layout=Layout(height='auto', width='160px'),step=0.01)
            self.widgets['SCR_upper'] = ipw.FloatText(value = 0.9,layout=Layout(height='auto', width='50px'),step=0.01)
    
            self.widgets['ESG_SCORE_lower'] = ipw.FloatText(value = 0,description = 'ESG Score: ',
                                                style = {'description_width': '100px'},layout=Layout(height='auto', width='160px'),step=0.5)
            self.widgets['ESG_SCORE_upper'] = ipw.FloatText(value = 10,layout=Layout(height='auto', width='50px'),step=0.5)
            
            self.widgets['CI_lower'] = ipw.FloatText(value = 0,description = 'CI, tCO2/EURmn: ',
                                                style = {'description_width': '100px'},layout=Layout(height='auto', width='160px'))
            self.widgets['CI_upper'] = ipw.FloatText(value = 200,layout=Layout(height='auto', width='50px'))
 
            self.widgets['Decarb_lower'] = ipw.FloatText(value = 0,description = 'Decarb, %',
                                                style = {'description_width': '100px'},layout=Layout(height='auto', width='160px'))
            self.widgets['Decarb_upper'] = ipw.FloatText(value = 200,layout=Layout(height='auto', width='50px'))

            self.widgets['WARF_lower'] = ipw.FloatText(value = 0,description = 'WARF: ',
                                                style = {'description_width': '100px'},layout=Layout(height='auto', width='160px'))
            self.widgets['WARF_upper'] = ipw.FloatText(value = 400,layout=Layout(height='auto', width='50px'))
            
            self.widgets['PnL_lower'] = ipw.FloatText(value = 0,description = 'P&L: ',
                                                style = {'description_width': '100px'},layout=Layout(height='auto', width='160px'))
            self.widgets['PnL_upper'] = ipw.FloatText(value = 400,layout=Layout(height='auto', width='50px'))
            
            self.widgets['weight_lower'] = ipw.FloatText(value = 0,description = 'Weights: ',
                                                style = {'description_width': '100px'},layout=Layout(height='auto', width='160px'),step=0.001)
            self.widgets['weight_upper'] = ipw.FloatText(value = 0.5,layout=Layout(height='auto', width='60px'),step=0.001)
            
            self.widgets['buffer_SectorsLEFT'] = ipw.VBox([ipw.Label(value='Buffer:')] +[ ipw.FloatText(value = 0.05,description = x+ ": ",step=0.01,
                                                layout=Layout(height='30px', width='150px'),style = {'description_width': '80px'}) for x in np.sort(self.df["Sector"].unique()) ], layout=ipw.Layout(justify_content='flex-start',align_items='flex-end'))
            df_sectors = pd.DataFrame(self.df.groupby(['Sector'])['Notional Amount'].sum()/self.df['Notional Amount'].sum())
            self.widgets['buffer_SectorsM'] = ipw.VBox([ipw.Label(value='Lower:')] + [ ipw.FloatText(value = max(np.round(df_sectors[df_sectors.index == x]["Notional Amount"].iloc[0] - 0.05,2),0),
                                                layout=Layout(height='30px', width='50px')) for x in np.sort(self.df["Sector"].unique()) ], layout=ipw.Layout(justify_content='flex-start'),align_items='flex-end')
            self.widgets['buffer_SectorsRight'] = ipw.VBox([ipw.Label(value='Upper:')] +[ ipw.FloatText(value = min(np.round(df_sectors[df_sectors.index == x]["Notional Amount"].iloc[0] + 0.05,2),1),
                                                layout=Layout(height='30px', width='50px')) for x in np.sort(self.df["Sector"].unique()) ], layout=ipw.Layout(justify_content='flex-start',align_items='flex-end'))
            def update_sectors(*args):
                buffers = dict(zip( np.sort(self.df["Sector"].unique()) ,[x.value for x in self.widgets['buffer_SectorsLEFT'].children][1:]))
                self.widgets['buffer_SectorsM'].children =[ipw.Label(value='Lower:')] + [ ipw.FloatText(value = max(np.round(df_sectors[df_sectors.index == x]["Notional Amount"].iloc[0] - buffers[x],2),0),
                                                layout=Layout(height='30px', width='50px')) for x in np.sort(self.df["Sector"].unique()) ]
                self.widgets['buffer_SectorsRight'].children =[ipw.Label(value='Upper:')] + [ ipw.FloatText(value = min(np.round(df_sectors[df_sectors.index == x]["Notional Amount"].iloc[0] + buffers[x],2),1),
                                                layout=Layout(height='30px', width='50px')) for x in np.sort(self.df["Sector"].unique()) ]
            for child in self.widgets["buffer_SectorsLEFT"].children: 
                child.observe(update_sectors, 'value')
            self.widgets["buffer_Sectors"] = ipw.HBox([self.widgets['buffer_SectorsLEFT'],self.widgets["buffer_SectorsM"],self.widgets['buffer_SectorsRight']], layout=ipw.Layout(justify_content='flex-start',align_items='flex-end'))
                        
            df_ratings = pd.DataFrame(self.df.groupby(['SBR'])['Notional Amount'].sum()/self.df['Notional Amount'].sum())
            df_ratings = df_ratings.reindex(bond_rating_order)
            self.widgets['buffer_RatingsLEFT'] = ipw.VBox([ipw.Label(value='Buffer:')] +[ ipw.FloatText(value = 0.05,description = x + ": ",step=0.01,
                                                layout=Layout(height='30px', width='150px'),style = {'description_width': '80px'}) for x in df_ratings.index.tolist()], layout=ipw.Layout(justify_content='flex-start',align_items='flex-end'))
            self.widgets['buffer_RatingsM'] = ipw.VBox([ipw.Label(value='Lower:')] + [ ipw.FloatText(value = max(np.round(df_ratings[df_ratings.index == x]["Notional Amount"].iloc[0] - 0.05,2),0),
                                                layout=Layout(height='30px', width='50px')) for x in df_ratings.index.tolist() ], layout=ipw.Layout(justify_content='flex-start',align_items='flex-end'))
            self.widgets['buffer_RatingsRight'] = ipw.VBox([ipw.Label(value='Upper:')] +[ ipw.FloatText(value = min(np.round(df_ratings[df_ratings.index == x]["Notional Amount"].iloc[0] + 0.05,2),1),
                                                layout=Layout(height='30px', width='50px')) for x in df_ratings.index.tolist() ], layout=ipw.Layout(justify_content='flex-start',align_items='flex-end'))
            def update_Ratings(*args):
                buffers = dict(zip(df_ratings.index.tolist(),[x.value for x in self.widgets['buffer_RatingsLEFT'].children][1:]))
                self.widgets['buffer_RatingsM'].children =[ipw.Label(value='Lower:')] +  [ipw.FloatText(value = max(np.round(df_ratings[df_ratings.index == x]["Notional Amount"].iloc[0] - buffers[x],2),0),
                                                layout=Layout(height='30px', width='50px')) for x in df_ratings.index.tolist() ]
                self.widgets['buffer_RatingsRight'].children =[ipw.Label(value='Upper:')] + [ipw.FloatText(value = min(np.round(df_ratings[df_ratings.index == x]["Notional Amount"].iloc[0] + buffers[x],2),1),
                                                layout=Layout(height='30px', width='50px')) for x in df_ratings.index.tolist() ]
            for child in self.widgets["buffer_RatingsLEFT"].children: 
                child.observe(update_Ratings, 'value')
            self.widgets["buffer_Ratings"] = ipw.HBox([self.widgets['buffer_RatingsLEFT'],self.widgets["buffer_RatingsM"],self.widgets['buffer_RatingsRight']], layout=ipw.Layout(justify_content='flex-start',align_items='flex-end'))
                  
            self.widgets['buffer_SenioritiesLEFT'] = ipw.VBox([ipw.Label(value='Buffer:')] + [ ipw.FloatText(value = 0.05,description = x+ ": ",step=0.01,
                                                layout=Layout(height='30px', width='150px'),style = {'description_width': '80px'}) for x in self.df["Seniority"].unique() ], layout=ipw.Layout(justify_content='flex-start',align_items='flex-end'))
            df_sen = pd.DataFrame(self.df.groupby(['Seniority'])['Notional Amount'].sum()/self.df['Notional Amount'].sum())
            self.widgets['buffer_SenioritiesM'] = ipw.VBox([ipw.Label(value='Lower:')] + [ ipw.FloatText(value = max(np.round(df_sen[df_sen.index == x]["Notional Amount"].iloc[0] - 0.05,2),0),
                                                layout=Layout(height='30px', width='50px')) for x in self.df["Seniority"].unique() ], layout=ipw.Layout(justify_content='flex-start',align_items='flex-end'))
            self.widgets['buffer_SenioritiesRight'] = ipw.VBox([ipw.Label(value='Upper:')] + [ ipw.FloatText(value = min(np.round(df_sen[df_sen.index == x]["Notional Amount"].iloc[0] + 0.05,2),1),
                                                layout=Layout(height='30px', width='50px')) for x in self.df["Seniority"].unique() ], layout=ipw.Layout(justify_content='flex-start',align_items='flex-end'))
            def update_Seniorities(*args):
                buffers = dict(zip(self.df["Seniority"].unique().tolist(),[x.value for x in self.widgets['buffer_SenioritiesLEFT'].children][1:]))
                self.widgets['buffer_SenioritiesM'].children =[ipw.Label(value='Lower:')] +  [ipw.FloatText(value = max(np.round(df_sen[df_sen.index == x]["Notional Amount"].iloc[0] - buffers[x],2),0),
                                                layout=Layout(height='30px', width='50px')) for x in self.df["Seniority"].unique()]
                self.widgets['buffer_SenioritiesRight'].children =[ipw.Label(value='Upper:')] +  [ipw.FloatText(value = min(np.round(df_sen[df_sen.index == x]["Notional Amount"].iloc[0] + buffers[x],2),1),
                                                layout=Layout(height='30px', width='50px')) for x in self.df["Seniority"].unique()]
            for child in self.widgets["buffer_SenioritiesLEFT"].children: 
                child.observe(update_Seniorities, 'value')
            self.widgets["buffer_Seniorities"] = ipw.HBox([self.widgets['buffer_SenioritiesLEFT'],self.widgets["buffer_SenioritiesM"],self.widgets['buffer_SenioritiesRight']], layout=ipw.Layout(justify_content='flex-start',align_items='flex-end'))
                
            df_mat = pd.DataFrame(self.df.groupby(['MaturityB'])['Notional Amount'].sum()/self.df['Notional Amount'].sum())
            df_mat = df_mat.reindex(maturity_order)
            self.widgets['buffer_MaturitiesLEFT'] = ipw.VBox([ipw.Label(value='Buffer:')] +[ ipw.FloatText(value = 0.05,description = x + ": ",step=0.01,
                                                layout=Layout(height='30px', width='150px'),style = {'description_width': '80px'}) for x in maturity_order ], layout=ipw.Layout(justify_content='flex-start',align_items='flex-end'))
            self.widgets['buffer_MaturitiesM'] = ipw.VBox([ipw.Label(value='Lower:')] +[ ipw.FloatText(value = max(np.round(df_mat[df_mat.index == x]["Notional Amount"].iloc[0] - 0.05,2),0),
                                                layout=Layout(height='30px', width='50px')) for x in maturity_order ], layout=ipw.Layout(justify_content='flex-start',align_items='flex-end'))
            self.widgets['buffer_MaturitiesRight'] = ipw.VBox([ipw.Label(value='Upper:')] +[ ipw.FloatText(value = min(np.round(df_mat[df_mat.index == x]["Notional Amount"].iloc[0] + 0.05,2),1),
                                                layout=Layout(height='30px', width='50px')) for x in maturity_order ], layout=ipw.Layout(justify_content='flex-start',align_items='flex-end'))
            def update_Maturities(*args):
                buffers = dict(zip(maturity_order,[x.value for x in self.widgets['buffer_MaturitiesLEFT'].children][1:]))
                self.widgets['buffer_MaturitiesM'].children =[ipw.Label(value='Lower:')] + [ipw.FloatText(value = max(np.round(df_mat[df_mat.index == x]["Notional Amount"].iloc[0] - buffers[x],2),0),
                                                layout=Layout(height='30px', width='50px')) for x in maturity_order ]
                self.widgets['buffer_MaturitiesRight'].children =[ipw.Label(value='Upper:')] + [ipw.FloatText(value = min(np.round(df_mat[df_mat.index == x]["Notional Amount"].iloc[0] + buffers[x],2),1),
                                                layout=Layout(height='30px', width='50px')) for x in maturity_order ]
            for child in self.widgets["buffer_MaturitiesLEFT"].children: 
                child.observe(update_Maturities, 'value')
            self.widgets["buffer_Maturities"] = ipw.HBox([self.widgets['buffer_MaturitiesLEFT'],self.widgets["buffer_MaturitiesM"],self.widgets['buffer_MaturitiesRight']], layout=ipw.Layout(justify_content='flex-start',align_items='flex-end'))
            
            self.widgets['buffer_CountriesLEFT'] = ipw.VBox([ipw.Label(value='Buffer:')] +[ ipw.FloatText(value = 0.05,description = x+ ': ',step=0.01,
                                                layout=Layout(height='30px', width='150px'),style = {'description_width': '80px'}) for x in np.sort(self.df["Issuer Country"].unique()) ], layout=ipw.Layout(justify_content='flex-start',align_items='flex-end'))
            df_cty = pd.DataFrame(self.df.groupby(['Issuer Country'])['Notional Amount'].sum()/self.df['Notional Amount'].sum())
            self.widgets['buffer_CountriesM'] = ipw.VBox([ipw.Label(value='Lower:')] +[ ipw.FloatText(value = max(np.round(df_cty[df_cty.index == x]["Notional Amount"].iloc[0] - 0.05,2),0),
                                                layout=Layout(height='30px', width='50px')) for x in np.sort(self.df["Issuer Country"].unique()) ], layout=ipw.Layout(justify_content='flex-start',align_items='flex-end'))
            self.widgets['buffer_CountriesRight'] = ipw.VBox([ipw.Label(value='Upper:')] + [ ipw.FloatText(value = min(np.round(df_cty[df_cty.index == x]["Notional Amount"].iloc[0] + 0.05,2),1),
                                                layout=Layout(height='30px', width='50px')) for x in np.sort(self.df["Issuer Country"].unique()) ], layout=ipw.Layout(justify_content='flex-start',align_items='flex-end'))
            def update_cty(*args):
                buffers = dict(zip(np.sort(self.df["Issuer Country"].unique()),[x.value for x in self.widgets['buffer_CountriesLEFT'].children][1:]))
                self.widgets['buffer_CountriesM'].children = [ipw.Label(value='Lower:')] +[ipw.FloatText(value = max(np.round(df_cty[df_cty.index == x]["Notional Amount"].iloc[0] - buffers[x],2),0),
                                                layout=Layout(height='30px', width='50px')) for x in np.sort(self.df["Issuer Country"].unique())]
                self.widgets['buffer_CountriesRight'].children =[ipw.Label(value='Upper:')] +  [ipw.FloatText(value = min(np.round(df_cty[df_cty.index == x]["Notional Amount"].iloc[0] + buffers[x],2),1),
                                                layout=Layout(height='30px', width='50px')) for x in np.sort(self.df["Issuer Country"].unique())]
            for child in self.widgets["buffer_CountriesLEFT"].children: 
                child.observe(update_cty, 'value')
            self.widgets["buffer_Countries"] = ipw.HBox([self.widgets['buffer_CountriesLEFT'],self.widgets["buffer_CountriesM"],self.widgets['buffer_CountriesRight']], layout=ipw.Layout(justify_content='flex-start',align_items='flex-end'))   
            
            df_esg = pd.DataFrame(self.df.groupby(['ESG_RATING'])['Notional Amount'].sum()/self.df['Notional Amount'].sum())
            df_esg = df_esg.reindex(esg_order)
            self.widgets['buffer_ESG_RatingsLEFT'] = ipw.VBox([ipw.Label(value='Buffer:')] +[ ipw.FloatText(value = 0.05,description = x + ": ",step=0.01,
                                                layout=Layout(height='30px', width='150px'),style = {'description_width': '80px'}) for x in esg_order ], layout=ipw.Layout(justify_content='flex-start',align_items='flex-end'))
            self.widgets['buffer_ESG_RatingsM'] = ipw.VBox([ipw.Label(value='Lower:')] +[ ipw.FloatText(value = max(np.round(df_esg[df_esg.index == x]["Notional Amount"].iloc[0] - 0.05,2),0),
                                                layout=Layout(height='30px', width='60px')) for x in esg_order ], layout=ipw.Layout(justify_content='flex-start',align_items='flex-end'))
            self.widgets['buffer_ESG_RatingsRight'] = ipw.VBox([ipw.Label(value='Upper:')] + [ ipw.FloatText(value = min(np.round(df_esg[df_esg.index == x]["Notional Amount"].iloc[0] + 0.05,2),1),
                                                layout=Layout(height='30px', width='50px')) for x in esg_order], layout=ipw.Layout(justify_content='flex-start',align_items='flex-end'))
            def update_esg(*args):
                buffers = dict(zip(esg_order,[x.value for x in self.widgets['buffer_ESG_RatingsLEFT'].children][1:]))
                self.widgets['buffer_ESG_RatingsM'].children = [ipw.Label(value='Lower:')] +[ipw.FloatText(value = max(np.round(df_esg[df_esg.index == x]["Notional Amount"].iloc[0] - buffers[x],2),0),
                                                layout=Layout(height='30px', width='60px'),style = {'description_width': '150px'}) for x in esg_order]
                self.widgets['buffer_ESG_RatingsRight'].children =[ipw.Label(value='Upper:')] +  [ipw.FloatText(value = min(np.round(df_esg[df_esg.index == x]["Notional Amount"].iloc[0] + buffers[x],2),1),
                                                layout=Layout(height='30px', width='50px'),style = {'description_width': '150px'}) for x in esg_order]
            for child in self.widgets["buffer_ESG_RatingsLEFT"].children: 
                child.observe(update_esg, 'value')
            self.widgets["buffer_ESG_Ratings"] = ipw.HBox([self.widgets['buffer_ESG_RatingsLEFT'],self.widgets["buffer_ESG_RatingsM"],self.widgets['buffer_ESG_RatingsRight']], layout=ipw.Layout(justify_content='flex-start',align_items='flex-end'))
        
            self.widgets['buffer_TickersLEFT'] = ipw.VBox([ipw.Label(value='Buffer:')] +[ ipw.FloatText(value = 0.05,description = x + ": ",step=0.01,
                                                layout=Layout(height='30px', width='150px'),style = {'description_width': '80px'}) for x in np.sort(self.df["Ticker"].unique().tolist()) ], layout=ipw.Layout(justify_content='flex-end',align_items='flex-end'))
            df_tick = pd.DataFrame(self.df.groupby(['Ticker'])['Notional Amount'].sum()/self.df['Notional Amount'].sum())
            self.widgets['buffer_TickersM'] = ipw.VBox([ipw.Label(value='Lower:')] +[ ipw.FloatText(value = max(np.round(df_tick[df_tick.index == x]["Notional Amount"].iloc[0] - 0.05,2),0),
                                                layout=Layout(height='30px', width='60px'),style = {'description_width': '150px'}) for x in np.sort(self.df["Ticker"].unique().tolist()) ], layout=ipw.Layout(justify_content='flex-start'))
            self.widgets['buffer_TickersRight'] = ipw.VBox([ipw.Label(value='Upper:')] + [ ipw.FloatText(value = min(np.round(df_tick[df_tick.index == x]["Notional Amount"].iloc[0] + 0.05,2),1),
                                                layout=Layout(height='30px', width='50px'),style = {'description_width': '150px'}) for x in np.sort(self.df["Ticker"].unique().tolist()) ], layout=ipw.Layout(justify_content='flex-start',align_items='flex-start'))
            def update_tick(*args):
                buffers = dict(zip(np.sort(self.df["Ticker"].unique()),[x.value for x in self.widgets['buffer_TickersLEFT'].children][1:]))
                self.widgets['buffer_TickersM'].children = [ipw.Label(value='Lower:')] +[ipw.FloatText(value = max(np.round(df_tick[df_tick.index == x]["Notional Amount"].iloc[0] - buffers[x],2),0),
                                                layout=Layout(height='30px', width='60px'),style = {'description_width': '150px'}) for x in np.sort(self.df["Ticker"].unique().tolist())]
                self.widgets['buffer_TickersRight'].children =[ipw.Label(value='Upper:')] +  [ipw.FloatText(value = min(np.round(df_tick[df_tick.index == x]["Notional Amount"].iloc[0] + buffers[x],2),1),
                                                layout=Layout(height='30px', width='50px'),style = {'description_width': '150px'}) for x in np.sort(self.df["Ticker"].unique().tolist())]
            for child in self.widgets["buffer_TickersLEFT"].children: 
                child.observe(update_tick, 'value')
            self.widgets["buffer_Tickers"] = ipw.HBox([self.widgets['buffer_TickersLEFT'],self.widgets["buffer_TickersM"],self.widgets['buffer_TickersRight']], layout=ipw.Layout(justify_content='flex-start',align_items='flex-start'))
            
            
#             if "Cashflow" in self.df.columns:
#                 self.widgets['buffer_CashFlowsLEFT'] = ipw.VBox([ipw.Label(value='Buffer:')] +[ ipw.FloatText(value = 0,description = str(x) + ": ",step= np.round(self.df[self.df["MaturityYear"] == x]["Cashflow"].iloc[0]/10,1),
#                                                     layout=Layout(height='30px', width='150px'),style = {'description_width': '80px'}) for x in np.sort(self.df["MaturityYear"].unique().tolist()) ], layout=ipw.Layout(justify_content='flex-end',align_items='flex-end'))
#                 df_cash = self.df.drop_duplicates(subset=["MaturityYear"])[["MaturityYear","Cashflow"]].sort_values(by="MaturityYear").set_index("MaturityYear")
#                 self.widgets['buffer_CashFlowsM'] = ipw.VBox([ipw.Label(value='Lower:')] +[ ipw.FloatText(value = 0,
#                                                     layout=Layout(height='30px', width='50px'),style = {'description_width': '150px'}) for x in np.sort(self.df["MaturityYear"].unique().tolist()) ], layout=ipw.Layout(justify_content='flex-start'))
#                 self.widgets['buffer_CashFlowsRight'] = ipw.VBox([ipw.Label(value='Upper:')] + [ ipw.FloatText(value = np.round(df_cash[df_cash.index == x]["Cashflow"].iloc[0] + 0,1),
#                                                     layout=Layout(height='30px', width='60px'),style = {'description_width': '150px'}) for x in np.sort(self.df["MaturityYear"].unique().tolist()) ], layout=ipw.Layout(justify_content='flex-start',align_items='flex-start'))
#                 def update_CashFlows(*args):
#                     buffers = dict(zip(np.sort(self.df["MaturityYear"].unique()),[x.value for x in self.widgets['buffer_CashFlowsLEFT'].children][1:]))
#                     self.widgets['buffer_CashFlowsM'].children = [ipw.Label(value='Lower:')] +[ipw.FloatText(value = 0 - buffers[x],
#                                                     layout=Layout(height='30px', width='50px'),style = {'description_width': '150px'}) for x in np.sort(self.df["MaturityYear"].unique().tolist())]
#                     self.widgets['buffer_CashFlowsRight'].children =[ipw.Label(value='Upper:')] +  [ipw.FloatText(value = np.round(df_cash[df_cash.index == x]["Cashflow"].iloc[0] + 0,1),
#                                                     layout=Layout(height='30px', width='60px'),style = {'description_width': '150px'}) for x in np.sort(self.df["MaturityYear"].unique().tolist())]
#                 for child in self.widgets["buffer_CashFlowsLEFT"].children: 
#                     child.observe(update_CashFlows, 'value')
#                 self.widgets["buffer_CashFlows"] = ipw.HBox([self.widgets['buffer_CashFlowsLEFT'],self.widgets["buffer_CashFlowsM"],self.widgets['buffer_CashFlowsRight']], layout=ipw.Layout(justify_content='flex-start',align_items='flex-start'))
            
#             else:
#                 self.widgets['buffer_CashFlows'] = ipw.FloatText(value = 0.05,description = 'CashFlows',
#                                                 layout=Layout(height='auto', width='auto'))
               
            self.widgets["Objective"] = ipw.VBox([self.widgets["MaxMin"], self.widgets['Objet']], layout=ipw.Layout(justify_content='flex-start'), height= "auto")
            self.widgets["salesbuys"] = ipw.VBox([self.widgets['salesbuys_']], layout=ipw.Layout(justify_content='flex-start'), height= "auto")
            self.widgets["PORTFOLIO"] = ipw.VBox([self.widgets['PORTFOLIO_']], layout=ipw.Layout(justify_content='flex-start'), height= "auto")  
            self.widgets["turnover"] = ipw.HBox([self.widgets["turnover_lower"],self.widgets['turnover_upper']], layout=ipw.Layout(justify_content='flex-start'))          
            self.widgets["Yield"] = ipw.HBox([self.widgets["Yield_lower"],self.widgets['Yield_upper']], layout=ipw.Layout(justify_content='flex-start'))            
            self.widgets["Spread"] = ipw.HBox([self.widgets["Spread_lower"],self.widgets['Spread_upper']], layout=ipw.Layout(justify_content='flex-start'))           
            self.widgets["Duration"] = ipw.HBox([self.widgets["Duration_lower"],self.widgets['Duration_upper']], layout=ipw.Layout(justify_content='flex-start'))          
            self.widgets["Maturity"] = ipw.HBox([self.widgets["Maturity_lower"],self.widgets['Maturity_upper']], layout=ipw.Layout(justify_content='flex-start'))           
            self.widgets["SCR"] = ipw.HBox([self.widgets["SCR_lower"],self.widgets['SCR_upper']], layout=ipw.Layout(justify_content='flex-start'))          
            self.widgets["ESG Score"] = ipw.HBox([self.widgets["ESG_SCORE_lower"],self.widgets['ESG_SCORE_upper']], layout=ipw.Layout(justify_content='flex-start'))          
            self.widgets["CI"] = ipw.HBox([self.widgets["CI_lower"],self.widgets['CI_upper']], layout=ipw.Layout(justify_content='flex-start'))   
            self.widgets["WARF"] = ipw.HBox([self.widgets["WARF_lower"],self.widgets['WARF_upper']], layout=ipw.Layout(justify_content='flex-start'))
            self.widgets["Decarb"] = ipw.HBox([self.widgets["Decarb_lower"],self.widgets['Decarb_upper']], layout=ipw.Layout(justify_content='flex-start'))
            self.widgets["PnL"] = ipw.HBox([self.widgets["PnL_lower"],self.widgets['PnL_upper']], layout=ipw.Layout(justify_content='flex-start'))
            self.widgets["Weight"] = ipw.HBox([self.widgets["weight_lower"],self.widgets['weight_upper']], layout=ipw.Layout(justify_content='flex-start'))           
            
            self.widgets["Metrics"] = ipw.VBox([self.widgets['size']
                                                ,self.widgets['nonzero']
                                                ,self.widgets['turnover']
                                                ,self.widgets["Yield"]
                                                ,self.widgets['Spread']
                                                ,self.widgets["Duration"]
                                                ,self.widgets["Maturity"]
                                                ,self.widgets["SCR"]
                                                #,self.widgets["ESG Score"]
                                                #,self.widgets["CI"]
                                                ,self.widgets["WARF"]
                                                ,self.widgets["PnL"]
                                                ,self.widgets["Weight"]
                                                ], 
                                               layout=ipw.Layout(justify_content='flex-start',align_item = "flex-start",width = "auto",height = "auto"))
            
            self.widgets["ESG Metrics"] = ipw.VBox([self.widgets["ESG Score"],
                                                self.widgets["CI"],
                                                self.widgets["Decarb"]
                                                ], 
                                               layout=ipw.Layout(justify_content='flex-start',align_item = "flex-start",width = "auto",height = "auto"))
            
            self.widgets["RUN"] = ipw.Button(description = "Run Optimizer",button_style = '',layout=Layout(height='40px', width='auto'),style={"color":'#D3D3D3',"font_weight":"bold","button_color":"#808080","description_color":"white"})
            self.widgets["RUN"].on_click(self.run_optimizer)
    
            self.widgets["solution"] = ipw.HTML(layout={'border': '1px solid black','height':'120px',"width":"auto"})
            
            self.widgets["Constraints_"] =  ipw.Accordion([self.widgets['Metrics']
                                                ,self.widgets["buffer_Sectors"]
                                                ,self.widgets['buffer_Ratings']
                                                ,self.widgets["buffer_Seniorities"]
                                                ,self.widgets["buffer_Maturities"]
                                                ,self.widgets["buffer_Countries"]
                                                ,self.widgets["buffer_Tickers"]
                                                #,self.widgets['buffer_CashFlows']
                                               ]).add_class("parentstyle")
            
            self.widgets["ESG_Constraints_"] =  ipw.Accordion([self.widgets['ESG Metrics'],
                                                self.widgets["buffer_ESG_Ratings"]
                                               ]).add_class("parentstyle")
            
            self.widgets["Constraints_"].selected_index = None
            self.widgets["ESG_Constraints_"].selected_index = None
            
            display(HTML("<style>.parentstyle > .p-Accordion-child > .p-Collapse-header{background-color:#D3D3D3}</style>"))
            
            self.widgets["Constraints_"].selected_style = {'background-color': 'lightgray'}
            self.widgets["Constraints_"].set_title(0, 'Key Metrics')
            self.widgets["Constraints_"].set_title(1, 'Sectors')
            self.widgets["Constraints_"].set_title(2, 'Ratings')
            self.widgets["Constraints_"].set_title(3, 'Seniorities')
            self.widgets["Constraints_"].set_title(4, 'Maturities')
            self.widgets["Constraints_"].set_title(5, 'Countries')
            #self.widgets["Constraints_"].set_title(6, 'ESG_Ratings')
            self.widgets["Constraints_"].set_title(6, 'Tickers')
            #self.widgets["Constraints_"].set_title(7, 'CashFlows')
            
            self.widgets["ESG_Constraints_"].selected_style = {'background-color': 'lightgray'}
            self.widgets["ESG_Constraints_"].set_title(0, 'ESG Metrics')
            self.widgets["ESG_Constraints_"].set_title(1, 'ESG_Ratings')
                            
            self.widgets["Constraints"] = ipw.Accordion([self.widgets["Constraints_"]],layout=ipw.Layout(justify_content='flex-start',width = "auto",height = "300px")).add_class("parentstyle")
            self.widgets["Constraints"].set_title(0, 'Constraints')
            
            self.widgets["ESG_Constraints"] = ipw.Accordion([self.widgets["ESG_Constraints_"]],layout=ipw.Layout(justify_content='flex-start',width = "auto",height = "300px")).add_class("parentstyle")
            self.widgets["ESG_Constraints"].set_title(0, 'ESG_Constraints')
            
            self.widgets['Yield_lower_filter'] = ipw.FloatText(value = np.round(self.df["Yield"].min()-1,1),description = 'Yield, %: ',step=0.1,
                                                style = {'description_width': '100px'},layout=Layout(height='auto', width='160px'))
            self.widgets['Yield_upper_filter'] = ipw.FloatText(value = np.round(self.df["Yield"].max()+1,1) ,layout=Layout(height='auto', width='60px'),step=0.1)
                    
            self.widgets['Spread_lower_filter'] = ipw.FloatText(value = np.round(self.df["Curr. Spread"].min()-1,1),description = 'ASW, bps: ',
                                                style = {'description_width': '100px'},layout=Layout(height='auto', width='160px'))
            self.widgets['Spread_upper_filter'] = ipw.FloatText(value = np.round(self.df["Curr. Spread"].max()+1,1),layout=Layout(height='auto', width='60px'))
            
            self.widgets['Duration_lower_filter'] = ipw.FloatText(value = np.round(self.df["Duration"].min()-1,1),description = 'Duration: ',
                                                style = {'description_width': '100px'},layout=Layout(height='auto', width='160px'),step=0.1)
            self.widgets['Duration_upper_filter'] = ipw.FloatText(value = np.round(self.df["Duration"].max()+1,1),layout=Layout(height='auto', width='60px'),step=0.1)
            
            self.widgets['Maturity_lower_filter'] = ipw.FloatText(value = np.round(self.df["YTM"].min()-1,1),description = 'Maturity, yrs: ',
                                                style = {'description_width': '100px'},layout=Layout(height='auto', width='160px'),step=0.1)
            self.widgets['Maturity_upper_filter'] = ipw.FloatText(value = np.round(self.df["YTM"].max()+1,1),layout=Layout(height='auto', width='60px'),step=0.1)
            
            self.widgets['SCR_lower_filter'] = ipw.FloatText(value = np.round(self.df["SRC"].min()-1,1),description = 'SCR, %: ',
                                                style = {'description_width': '100px'},layout=Layout(height='auto', width='160px'),step=0.01)
            self.widgets['SCR_upper_filter'] = ipw.FloatText(value = np.round(self.df["SRC"].max()+1,1),layout=Layout(height='auto', width='60px'),step=0.01)
    
            self.widgets['ESG_SCORE_lower_filter'] = ipw.FloatText(value = np.round(self.df["ESG_SCORE"].min()-1,1),description = 'ESG Score: ',
                                                style = {'description_width': '100px'},layout=Layout(height='auto', width='160px'),step=0.5)
            self.widgets['ESG_SCORE_upper_filter'] = ipw.FloatText(value = np.round(self.df["ESG_SCORE"].max()+1,1),layout=Layout(height='auto', width='60px'),step=0.5)
            
            self.widgets['CI_lower_filter'] = ipw.FloatText(value = np.round(self.df["CI"].min()-1,1),description = 'CI, tCO2/EURmn: ',
                                                style = {'description_width': '100px'},layout=Layout(height='auto', width='160px'))
            self.widgets['CI_upper_filter'] = ipw.FloatText(value = np.round(self.df["CI"].max()+1,1),layout=Layout(height='auto', width='60px'))
            
            self.widgets['WARF_lower_filter'] = ipw.FloatText(value = np.round(self.df["WARF"].min()-1,1),description = 'WARF: ',
                                                style = {'description_width': '100px'},layout=Layout(height='auto', width='160px'))
    
            self.widgets['WARF_upper_filter'] = ipw.FloatText(value = np.round(self.df["WARF"].max()+1,1),layout=Layout(height='auto', width='60px'))           
            
            self.widgets["Yield_filter"] = ipw.HBox([self.widgets["Yield_lower_filter"],self.widgets['Yield_upper_filter']], layout=ipw.Layout(justify_content='flex-start'))
            self.widgets["Spread_filter"] = ipw.HBox([self.widgets["Spread_lower_filter"],self.widgets['Spread_upper_filter']], layout=ipw.Layout(justify_content='flex-start'))            
            self.widgets["Duration_filter"] = ipw.HBox([self.widgets["Duration_lower_filter"],self.widgets['Duration_upper_filter']], layout=ipw.Layout(justify_content='flex-start'))           
            self.widgets["Maturity_filter"] = ipw.HBox([self.widgets["Maturity_lower_filter"],self.widgets['Maturity_upper_filter']], layout=ipw.Layout(justify_content='flex-start'))           
            self.widgets["SCR_filter"] = ipw.HBox([self.widgets["SCR_lower_filter"],self.widgets['SCR_upper_filter']], layout=ipw.Layout(justify_content='flex-start'))           
            self.widgets["ESG Score_filter"] = ipw.HBox([self.widgets["ESG_SCORE_lower_filter"],self.widgets['ESG_SCORE_upper_filter']], layout=ipw.Layout(justify_content='flex-start'))          
            self.widgets["CI_filter"] = ipw.HBox([self.widgets["CI_lower_filter"],self.widgets['CI_upper_filter']], layout=ipw.Layout(justify_content='flex-start'))           
            self.widgets["WARF_filter"] = ipw.HBox([self.widgets["WARF_lower_filter"],self.widgets['WARF_upper_filter']], layout=ipw.Layout(justify_content='flex-start'))                      
            self.widgets["Metrics_filter"] = ipw.VBox([
                                                self.widgets["Yield_filter"]
                                                ,self.widgets['Spread_filter']
                                                ,self.widgets["Duration_filter"]
                                                ,self.widgets["Maturity_filter"]
                                                ,self.widgets["SCR_filter"]
                                                ,self.widgets["ESG Score_filter"]
                                                ,self.widgets["CI_filter"]
                                                ,self.widgets["WARF_filter"]], 
                layout=ipw.Layout(justify_content='flex-start',width = "auto",height = "auto"))
            
            self.widgets['Sectors_filter'] = ipw.GridBox([ ipw.Checkbox(value = True,description = x,
                                                layout=Layout(height='30px', width='150px'),style = {'description_width': 'auto'}) for x in np.sort(self.df["Sector"].unique()) ], layout=ipw.Layout(grid_template_columns="repeat(2, 140px)"))
            
            def update_setcots_filter(*args):
                filtered_out = [x.description for x in self.widgets['Sectors_filter'].children if x.value == False]
                index = []
                for i, child in enumerate(self.widgets['buffer_SectorsLEFT'].children):
                    if child.description[:len(child.description)-2] in filtered_out:
                        child.value = 0
                        index.append(i)
                    else:
                        if i >=1:
                            child.value = 0.05
                for i, child in enumerate(self.widgets['buffer_SectorsM'].children):
                    if i in index:
                        child.value = 0
                for i, child in enumerate(self.widgets['buffer_SectorsRight'].children):
                    if i in index:
                        child.value = 0
            for child in self.widgets["Sectors_filter"].children: 
                child.observe(update_setcots_filter, 'value')
                        
            self.widgets['Ratings_filter'] = ipw.GridBox([ ipw.Checkbox(value = True,description = x,
                                                layout=Layout(height='30px', width='150px'),style = {'description_width': 'auto'}) for x in sorted(self.df["SBR"].unique().tolist(),key = lambda x : bond_rating_order.index(x)) ],layout=ipw.Layout(grid_template_columns="repeat(3, 90px)"))
            def update_ratings_filter(*args):
                filtered_out = [x.description for x in self.widgets['Ratings_filter'].children if x.value == False]
                index = []
                for i, child in enumerate(self.widgets['buffer_RatingsLEFT'].children):
                    if child.description[:len(child.description)-2] in filtered_out:
                        child.value = 0
                        index.append(i)
                    else:
                        if i >=1:
                            child.value = 0.05
                for i, child in enumerate(self.widgets['buffer_RatingsM'].children):
                    if i in index:
                        child.value = 0
                for i, child in enumerate(self.widgets['buffer_RatingsRight'].children):
                    if i in index:
                        child.value = 0
            for child in self.widgets["Ratings_filter"].children: 
                child.observe(update_ratings_filter, 'value')            
            
            self.widgets['Seniority_filter'] = ipw.GridBox([ ipw.Checkbox(value = True,description = x,
                                                layout=Layout(height='30px', width='150px'),style = {'description_width': 'auto'}) for x in np.sort(self.df["Seniority"].unique()) ], layout=ipw.Layout(grid_template_columns="repeat(3, 90px)"))
            def update_seniority_filter(*args):
                filtered_out = [x.description for x in self.widgets['Seniority_filter'].children if x.value == False]
                index = []
                for i, child in enumerate(self.widgets['buffer_SenioritiesLEFT'].children):
                    if child.description[:len(child.description)-2] in filtered_out:
                        child.value = 0
                        index.append(i)
                    else:
                        if i >=1:
                            child.value = 0.05
                for i, child in enumerate(self.widgets['buffer_SenioritiesM'].children):
                    if i in index:
                        child.value = 0
                for i, child in enumerate(self.widgets['buffer_SenioritiesRight'].children):
                    if i in index:
                        child.value = 0
            for child in self.widgets["Seniority_filter"].children: 
                child.observe(update_seniority_filter, 'value')
                       
            self.widgets['Maturity_filter'] = ipw.GridBox([ ipw.Checkbox(value = True,description = x,
                                                layout=Layout(height='30px', width='150px'),style = {'description_width': 'auto'}) for x in sorted(self.df["MaturityB"].unique().tolist(),key = lambda x : maturity_order.index(x))], layout=ipw.Layout(grid_template_columns="repeat(2, 140px)"))
            def update_maturity_filter(*args):
                filtered_out = [x.description for x in self.widgets['Maturity_filter'].children if x.value == False]
                index = []
                for i, child in enumerate(self.widgets['buffer_MaturitiesLEFT'].children):
                    if child.description[:len(child.description)-2] in filtered_out:
                        child.value = 0
                        index.append(i)
                    else:
                        if i >=1:
                            child.value = 0.05
                for i, child in enumerate(self.widgets['buffer_MaturitiesM'].children):
                    if i in index:
                        child.value = 0
                for i, child in enumerate(self.widgets['buffer_MaturitiesRight'].children):
                    if i in index:
                        child.value = 0
            for child in self.widgets["Maturity_filter"].children: 
                child.observe(update_maturity_filter, 'value')
                       
            self.widgets['Country_filter'] = ipw.GridBox([ ipw.Checkbox(value = True,description = x,
                                                layout=Layout(height='30px', width='150px'),style = {'description_width': 'auto'}) for x in np.sort(self.df["Issuer Country"].unique()) ], layout=ipw.Layout(grid_template_columns="repeat(2, 140px)"))
            def update_country_filter(*args):
                filtered_out = [x.description for x in self.widgets['Country_filter'].children if x.value == False]
                index = []
                for i, child in enumerate(self.widgets['buffer_CountriesLEFT'].children):
                    if child.description[:len(child.description)-2] in filtered_out:
                        child.value = 0
                        index.append(i)
                    else:
                        if i >=1:
                            child.value = 0.05
                for i, child in enumerate(self.widgets['buffer_CountriesM'].children):
                    if i in index:
                        child.value = 0
                for i, child in enumerate(self.widgets['buffer_CountriesRight'].children):
                    if i in index:
                        child.value = 0
            for child in self.widgets["Country_filter"].children: 
                child.observe(update_country_filter, 'value')
            
            self.widgets['ESG_RATING_filter'] = ipw.GridBox([ ipw.Checkbox(value = True,description = x,
                                                layout=Layout(height='30px', width='150px'),style = {'description_width': 'auto'}) for x in sorted(self.df["ESG_RATING"].unique().tolist(),key = lambda x : esg_order.index(x)) ], layout=ipw.Layout(grid_template_columns="repeat(3, 90px)"))
            def update_esg_filter(*args):
                filtered_out = [x.description for x in self.widgets['ESG_RATING_filter'].children if x.value == False]
                index = []
                for i, child in enumerate(self.widgets['buffer_ESG_RatingsLEFT'].children):
                    if child.description[:len(child.description)-2] in filtered_out:
                        child.value = 0
                        index.append(i)
                    else:
                        if i >=1:
                            child.value = 0.05
                for i, child in enumerate(self.widgets['buffer_ESG_RatingsM'].children):
                    if i in index:
                        child.value = 0
                for i, child in enumerate(self.widgets['buffer_ESG_RatingsRight'].children):
                    if i in index:
                        child.value = 0
            for child in self.widgets["ESG_RATING_filter"].children: 
                child.observe(update_esg_filter, 'value')
            
            
            self.widgets['Ticker_filter'] = ipw.GridBox([ ipw.Checkbox(value = True,description = x,
                                                layout=Layout(height='30px', width='150px'),style = {'description_width': 'auto'}) for x in np.sort(self.df["Ticker"].unique()) ], layout=ipw.Layout(grid_template_columns="repeat(3, 90px)"))
            def update_ticker_filter(*args):
                filtered_out = [x.description for x in self.widgets['Ticker_filter'].children if x.value == False]
                index = []
                for i, child in enumerate(self.widgets['buffer_TickersLEFT'].children):
                    if child.description[:len(child.description)-2] in filtered_out:
                        child.value = 0
                        index.append(i)
                    else:
                        if i >=1:
                            child.value = 0.05
                for i, child in enumerate(self.widgets['buffer_TickersM'].children):
                    if i in index:
                        child.value = 0
                for i, child in enumerate(self.widgets['buffer_TickersRight'].children):
                    if i in index:
                        child.value = 0
            for child in self.widgets["Ticker_filter"].children: 
                child.observe(update_ticker_filter, 'value')
            
            self.widgets['filters_accordions'] = ipw.Accordion([self.widgets['Metrics_filter']
                                                ,self.widgets['Sectors_filter']
                                                ,self.widgets['Ratings_filter']
                                                ,self.widgets['Seniority_filter']
                                                ,self.widgets['Maturity_filter']
                                                ,self.widgets['Country_filter']
                                                ,self.widgets['ESG_RATING_filter']
                                                ,self.widgets['Ticker_filter']
                                                               ]
                                                              
                                                              ).add_class("parentstyle")
            
            self.widgets["filters_accordions"].set_title(0, 'Metrics')
            self.widgets["filters_accordions"].set_title(1, 'Sectors')
            self.widgets["filters_accordions"].set_title(2, 'Ratings')
            self.widgets["filters_accordions"].set_title(3, 'Seniorities')
            self.widgets["filters_accordions"].set_title(4, 'Maturities')
            self.widgets["filters_accordions"].set_title(5, 'Countries')
            self.widgets["filters_accordions"].set_title(6, 'ESG Ratings')
            self.widgets["filters_accordions"].set_title(7, 'Tickers')
    
            self.widgets["Filters"] = ipw.Accordion([self.widgets["filters_accordions"]], style={"color":'#D3D3D3',"font_weight":"bold","button_color":"#808080","description_color":"white"}, layout=ipw.Layout(justify_content='flex-start',width = "auto",height = "300px")).add_class("parentstyle")
            self.widgets["Filters"].set_title(0, 'Filters')
    
            self.widgets["LabelObj"] = ipw.Label(value = 'Objective function')
            self.widgets["LabelPTF"] = ipw.Label(value = 'Index')
            self.widgets["LabelFilter"] = ipw.Label(value = "Filters")
            self.widgets["LabelCons"] = ipw.Label(value = 'Constraints',style = {'description_width': 'initial', 'font-weight': 'bold', 'font-size': '64px', 'font-family': 'Arial'})
            self.widgets["LabelESGCons"] = ipw.Label(value = 'ESG Constraints',style = {'description_width': 'initial', 'font-weight': 'bold', 'font-size': '64px', 'font-family': 'Arial'})
            self.widgets["LabelSol"] = ipw.Label(value = 'Parameters')
            self.widgets["LabelName"] = ipw.Label(value = "Simulation Name")
            
            self.widgets["SimuName"] = ipw.Text(value = "Simulation 1", layout=Layout(height='auto', width='auto'))
            
            self.widgets["solver"] = ipw.Dropdown(value='cvxpy',description = "Solver: ",
                                                       options = ['cvxpy',"cvxopt","pulp"],
                                                layout=Layout(height='auto', width='auto'))
            
            self.widgets['recommendation'] = ipw.Checkbox(value = False, description = "Checks",layout=Layout(height='auto', width='auto'))
            
            self.widgets["unit"] = ipw.Dropdown(value='Million',description = "Unit: ",
                                                       options = ['Million',"None"],
                                                layout=Layout(height='auto', width='auto'))
            
            self.widgets['fixed_size'] = ipw.Checkbox(value = True, description = "Fixed size",layout=Layout(height='auto', width='auto'))
            
            self.widgets["parameters"] = ipw.VBox([self.widgets["solver"],self.widgets["unit"],self.widgets['recommendation'], self.widgets['fixed_size']], layout=ipw.Layout(justify_content='flex-start',width = "auto", height = "auto"))
            
        if self.show_mapping == 1:
            columns = ['Sector', 'SBR', 'Seniority', 'MaturityB', 'Issuer Country', 'ESG_RATING', 'Ticker', 'Duration', 'Yield', 'WARF', 'Decarb', 'ESG_SCORE', 'SRC', 'CI', 'YTM', 'Curr. Spread', 'Notional Amount']
            vectorizer = TfidfVectorizer()
            corpus = columns + self.df.columns.tolist()
            X = vectorizer.fit_transform(corpus)
            threshold = 0.4
    
            dict_corr = {}
            
            for x in range(len(columns)):
                diff = 0
                for y in range(len(self.df.columns.tolist())):
                    dict_corr[columns[x]] = ""
                    if(cosine_similarity(X[x],X[len(columns)+y])>float(threshold)):
                        if cosine_similarity(X[x],X[len(columns)+y])>diff:
                            diff = cosine_similarity(X[x],X[len(columns)+y])
                            dict_corr[columns[x]] = self.df.columns.tolist()[y]
                        
            self.widgets['mapping'] = ipw.VBox([ipw.Dropdown(description = x,options = [dict_corr[x]] + self.df.columns.tolist()) for x in columns])
            
            for child in self.widgets['mapping'].children:
                if child.description in self.df.columns.tolist():
                    child.value = child.description
            
            self.widgets['reset'] = ipw.Button(description = 'Rename columns',button_style = '',layout=Layout(height='40px', width='auto'),style={"color":'#D3D3D3',"font_weight":"bold","button_color":"#A9A9A9","description_color":"white"})
            self.widgets['reset'].on_click(self.reset)
        
        self.widgets["salesbuys_"].observe(self.update_portfolio_dropdown, names='value')
        
        if self.show_mapping == 0:
            self.widgets["LEFT"] = ipw.VBox([self.widgets["LabelObj"]
                                                ,self.widgets["Objective"]
                                                ,self.widgets["salesbuys_"]
                                                ,self.widgets["LabelPTF"]
                                                ,self.widgets["PORTFOLIO_"]
                                                ,self.widgets["LabelFilter"]
                                                ,self.widgets["Filters"]
                                                ,self.widgets["LabelCons"]
                                                ,self.widgets['Constraints']
                                                ,self.widgets["LabelESGCons"]
                                                ,self.widgets['ESG_Constraints']
                                                ,self.widgets["LabelSol"]
                                                ,self.widgets["parameters"]
                                                ,self.widgets["LabelName"] 
                                                ,self.widgets["SimuName"]
                                                #self.widgets["upload"]
                                                ,self.widgets["RUN"]
                                                ,self.widgets["solution"]
                                               ], 
                                               
                                               layout=ipw.Layout(justify_content='flex-start',height="1600px",width="400px")
                                           )
                                           
        if self.show_mapping == 1:
            self.widgets["LEFT"] = ipw.VBox([self.widgets['mapping'],
                                             self.widgets['reset']
                                               ], layout=ipw.Layout(justify_content='flex-start',height="1600px",width="400px"))
            self.children = [self.widgets["LEFT"]]
        
        if self.show_mapping == 0:
            try:
                output = self.df[["ISIN","SecDes","Ticker","Issuer","Sector",'Subsector',"Seniority","MaturityB","Issuer Country","ESG_RATING",'SBR','WARF', 'Decarb', 'Curr. Spread',"Yield","Duration","YTM","SRC","ESG_SCORE","CI"]]
            except:
                output = self.df[["ISIN","Ticker","Sector","Seniority","MaturityB","Issuer Country","ESG_RATING",'SBR','WARF','Decarb', 'Curr. Spread',"Yield","Duration","YTM","SRC","ESG_SCORE","CI"]]
            
            self.data = output.copy()
            datagrid = DataGrid(output,editable = True,layout=ipw.Layout(width = "1200px",height = "1000px"))
            datagrid.auto_fit_columns = True
            self.datagrid = datagrid
            
                    
            self.df_1 = pd.DataFrame(self.df.groupby(['Sector'])['Notional Amount'].sum() *100 /self.df['Notional Amount'].sum()).rename(columns={"Notional Amount":'Percentage before optimization'}).sort_values('Percentage before optimization',ascending = False)
            self.df_1 = self.df_1.reset_index()
            self.df_1 = self.df_1.rename(columns={'Sector' : 'Sector of bonds'})
            self.df_1 = self.df_1.set_index("Sector of bonds")
            fig1 = go.Figure()
            fig1.add_trace(go.Bar(x=self.df_1.index, y=self.df_1['Percentage before optimization']))
            self.axs1 = go.FigureWidget(data = fig1)
            self.df_1['Percentage before optimization'] = self.df_1['Percentage before optimization'].apply(lambda x : f"{np.round(x,2)}%")
            self.datagrid1 = DataGrid(self.df_1.sort_index(ascending=True),editable = True,layout=ipw.Layout(width = "auto",height = "1000px"))
            self.datagrid1.auto_fit_columns = True
            self.widgets["Sectors_"] = self.datagrid1
            
            
            self.df_2 = pd.DataFrame(self.df.groupby(['Seniority'])['Notional Amount'].sum() *100 /self.df['Notional Amount'].sum()).rename(columns={"Notional Amount":'Percentage before optimization'}).sort_values('Percentage before optimization',ascending = False)
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(x=self.df_2.index, y=self.df_2['Percentage before optimization']))
            self.axs2 = go.FigureWidget(data = fig2)
            self.df_2['Percentage before optimization'] = self.df_2['Percentage before optimization'].apply(lambda x : f"{np.round(x,2)}%")
            self.datagrid2 = DataGrid(self.df_2.sort_index(ascending=True),editable = True,layout=ipw.Layout(width = "auto",height = "1000px"))
            self.datagrid2.auto_fit_columns = True
            self.widgets["Seniorities_"] = self.datagrid2
    
            
            self.df_3 = pd.DataFrame(self.df.groupby(['SBR'])['Notional Amount'].sum() *100 /self.df['Notional Amount'].sum()).rename(columns={"Notional Amount":'Percentage before optimization'}).sort_values('Percentage before optimization',ascending = False)
            fig3 = go.Figure()
            fig3.add_trace(go.Bar(x=self.df_3.index, y=self.df_3['Percentage before optimization']))
            self.axs3 = go.FigureWidget(data = fig3)
            self.df_3['Percentage before optimization'] = self.df_3['Percentage before optimization'].apply(lambda x : f"{np.round(x,2)}%")
            self.df_3 = self.df_3.reindex(bond_rating_order)
            self.datagrid3 = DataGrid(self.df_3,editable = True,layout=ipw.Layout(width = "auto",height = "1000px"))
            self.datagrid3.auto_fit_columns = True
            self.widgets["Ratings_"] = self.datagrid3
            
            self.df_4 = pd.DataFrame(self.df.groupby(['ESG_RATING'])['Notional Amount'].sum() *100 /self.df['Notional Amount'].sum()).rename(columns={"Notional Amount":'Percentage before optimization'}).sort_values('Percentage before optimization',ascending = False)
            fig4 = go.Figure()
            fig4.add_trace(go.Bar(x=self.df_4.index, y=self.df_4['Percentage before optimization']))
            self.axs4 = go.FigureWidget(data = fig4)
            self.df_4['Percentage before optimization'] = self.df_4['Percentage before optimization'].apply(lambda x : f"{np.round(x,2)}%")
            self.df_4 = self.df_4.reindex(esg_order)
            self.datagrid4 = DataGrid(self.df_4,editable = True,layout=ipw.Layout(width = "auto",height = "1000px"))
            self.datagrid4.auto_fit_columns = True
            self.widgets["ESG Ratings_"] = self.datagrid4
            
            self.df_5 = pd.DataFrame(self.df.groupby(['Issuer Country'])['Notional Amount'].sum() *100 /self.df['Notional Amount'].sum()).rename(columns={"Notional Amount":'Percentage before optimization'}).sort_values('Percentage before optimization',ascending = False)
            fig5 = go.Figure()
            fig5.add_trace(go.Bar(x=self.df_5.index[:15], y=self.df_5['Percentage before optimization'][:15]))
            self.axs5 = go.FigureWidget(data = fig5)
            self.df_5['Percentage before optimization'] = self.df_5['Percentage before optimization'].apply(lambda x : f"{np.round(x,2)}%")
            self.datagrid5 = DataGrid(self.df_5.sort_index(ascending=True),editable = True,layout=ipw.Layout(width = "auto",height = "1000px"))
            self.datagrid5.auto_fit_columns = True
            self.widgets["Countries_"] = self.datagrid5
            
            self.df_6 = pd.DataFrame(self.df.groupby(['MaturityB'])['Notional Amount'].sum() *100 /self.df['Notional Amount'].sum()).rename(columns={"Notional Amount":'Percentage before optimization'}).sort_values('Percentage before optimization',ascending = False)
            fig6 = go.Figure()
            fig6.add_trace(go.Bar(x=self.df_6.index, y=self.df_6['Percentage before optimization']))
            self.axs6 = go.FigureWidget(data = fig6)
            self.df_6['Percentage before optimization'] = self.df_6['Percentage before optimization'].apply(lambda x : f"{np.round(x,2)}%")
            self.df_6 = self.df_6.reindex(maturity_order)
            self.datagrid6 = DataGrid(self.df_6,editable = True,layout=ipw.Layout(width = "auto",height = "1000px"))
            self.datagrid6.auto_fit_columns = True
            self.widgets["Maturities_"] = self.datagrid6
            
            self.df_7 = pd.DataFrame(self.df.groupby(['Ticker'])['Notional Amount'].sum() *100 /self.df['Notional Amount'].sum()).rename(columns={"Notional Amount":'Percentage before optimization'}).sort_values('Percentage before optimization',ascending = False)
            fig7 = go.Figure()
            fig7.add_trace(go.Bar(x=self.df_7.index[:10], y=self.df_7['Percentage before optimization'][:10]))
            self.axs7 = go.FigureWidget(data = fig7)
            self.df_7['Percentage before optimization'] = self.df_7['Percentage before optimization'].apply(lambda x : f"{np.round(x,2)}%")
            self.datagrid7 = DataGrid(self.df_7.sort_index(ascending=True),editable = True,layout=ipw.Layout(width = "auto",height = "1000px"))
            self.datagrid7.auto_fit_columns = True
            self.widgets["Tickers_"] = self.datagrid7
            

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
            
            
            self.df_8 = pd.DataFrame({"Metrics":["Yield","Duration","Maturity","ESG_SCORE","CI","Decarb","WARF"],"Average":
                                                                      [(self.df["Yield"] *  self.df['Notional Amount']).sum()/self.df['Notional Amount'].sum(),
                                                                      #(self.df["Curr. Spread"] *  self.df['Notional Amount']).sum()/self.df['Notional Amount'].sum(),
                                                                      (self.df["Duration"] *  self.df['Notional Amount']).sum()/self.df['Notional Amount'].sum(),
                                                                      (self.df["YTM"] *  self.df['Notional Amount']).sum()/self.df['Notional Amount'].sum(),
                                                                      #(self.df["SRC"] *  self.df['Notional Amount']).sum()/self.df['Notional Amount'].sum(),
                                                                      (self.df["ESG_SCORE"] *  self.df['Notional Amount']).sum()/self.df['Notional Amount'].sum(),
                                                                      (self.df["CI"] *  self.df['Notional Amount']).sum()/self.df['Notional Amount'].sum(),
                                                                      (self.df["Decarb"] *  self.df['Notional Amount']).sum()/self.df['Notional Amount'].sum(),
                                                                      (self.df["WARF"] *  self.df['Notional Amount']).sum()/self.df['Notional Amount'].sum()]})\
                                                                      .rename(columns={"Average":"Average before optimization"}).set_index("Metrics")
            self.df_8 = self.df_8.apply(lambda x : np.round(x,2))
            self.datagrid8 = DataGrid(self.df_8,editable = True,layout=ipw.Layout(width = "auto",height = "1000px"))
            self.datagrid8.auto_fit_columns = True
            self.widgets["Metrics_"] = self.datagrid8
            
            self.widgets["Sectors__"] = ipw.Tab([self.widgets["Sectors_"], self.axs1],layout=Layout(height='400px', width='auto'))
            self.widgets["Sectors__"].set_title(0, 'Table')
            self.widgets["Sectors__"].set_title(1, 'Chart')
            
            self.widgets["Seniorities__"] = ipw.Tab([self.widgets["Seniorities_"],self.axs2],layout=Layout(height='400px', width='auto'))
            self.widgets["Seniorities__"].set_title(0, 'Table')
            self.widgets["Seniorities__"].set_title(1, 'Chart')
            
            self.widgets["Ratings__"] = ipw.Tab([self.widgets["Ratings_"],self.axs3],layout=Layout(height='400px', width='auto'))
            self.widgets["Ratings__"].set_title(0, 'Table')
            self.widgets["Ratings__"].set_title(1, 'Chart')
            
            self.widgets["ESG Ratings__"] = ipw.Tab([self.widgets["ESG Ratings_"],self.axs4],layout=Layout(height='400px', width='auto'))
            self.widgets["ESG Ratings__"].set_title(0, 'Table')
            self.widgets["ESG Ratings__"].set_title(1, 'Chart')
            
            self.widgets["Countries__"] = ipw.Tab([self.widgets["Countries_"],self.axs5],layout=Layout(height='400px', width='auto'))
            self.widgets["Countries__"].set_title(0, 'Table')
            self.widgets["Countries__"].set_title(1, 'Chart')
            
            self.widgets["Maturities__"] = ipw.Tab([self.widgets["Maturities_"],self.axs6],layout=Layout(height='400px', width='auto'))
            self.widgets["Maturities__"].set_title(0, 'Table')
            self.widgets["Maturities__"].set_title(1, 'Chart')
            
            self.widgets["Tickers__"] = ipw.Tab([self.widgets["Tickers_"],self.axs7],layout=Layout(height='400px', width='auto'))
            self.widgets["Tickers__"].set_title(0, 'Table')
            self.widgets["Tickers__"].set_title(1, 'Chart')
            
            # if "Cashflow" in self.df.columns:
            #     self.widgets["CashFlows_"] = ipw.Tab([self.widgets["CashFlows"],self.axs9],layout=Layout(height='400px', width='auto'))
            #     self.widgets["CashFlows_"].set_title(0, 'Table')
            #     self.widgets["CashFlows_"].set_title(1, 'Chart')
            
            self.widgets["Summary"] = ipw.Tab(layout=Layout(height='500px', width='800px'))
            self.widgets["Summary"].children = [self.widgets["Sectors__"],self.widgets["Seniorities__"],self.widgets["Ratings__"],self.widgets["ESG Ratings__"],self.widgets["Countries__"],self.widgets["Maturities__"],self.widgets["Tickers__"]]
            self.widgets["Summary"].set_title(0, 'Sectors')
            self.widgets["Summary"].set_title(1, 'Seniorities')
            self.widgets["Summary"].set_title(2, 'Ratings')
            self.widgets["Summary"].set_title(3, 'ESG Ratings')
            self.widgets["Summary"].set_title(4, 'Countries')
            self.widgets["Summary"].set_title(5, 'Maturities')
            self.widgets["Summary"].set_title(6, 'Tickers')
            #self.widgets["Summary"].set_title(7, 'CashFlows')
            
            self.widgets["LabelSum"] = ipw.Label(value = 'Summary')
            self.widgets["LabelSum"].style = {'font-size': '16px'}
            self.widgets["Labeldata"] = ipw.Label(value = 'Bond level data (before optimization)',style = {'description_width': 'initial', 'font-weight': 'bold', 'font-size': '64px', 'font-family': 'Arial'})
            self.widgets["Labeldata"].style = { 'font-size': '16px'}
            
            self.widgets["History"] = ipw.Output()
            self.widgets["x_axis"] = ipw.Dropdown(layout=Layout(height='auto', width='auto'),description='X axis')
            self.widgets["y_axis"] = ipw.Dropdown(layout=Layout(height='auto', width='auto'),description='Y axis')
            self.widgets["Scatter"] = ipw.Button(description = "Plot",button_style = '',layout=Layout(height='30px', width='80px'),style={"color":'#D3D3D3',"font_weight":"bold","button_color":"#A9A9A9","description_color":"white"})
            self.widgets["Scatter"].on_click(self.scatterplot)
            
            self.widgets["x_y_"] = ipw.VBox([self.widgets["x_axis"],self.widgets["y_axis"]],layout=Layout(height='auto', width='auto',justify_content='center'))
            self.widgets["Comparison_"] = ipw.HBox([self.widgets["x_y_"],self.widgets["Scatter"]],layout=Layout(height='auto', width='auto',justify_content='center'))
            self.widgets["Comparison"] = ipw.VBox([self.widgets["Comparison_"]],layout=Layout(height='auto', width='auto',justify_content='center'))
            
            self.widgets["Track"] = ipw.Tab([self.widgets["Metrics_"],self.widgets["History"],self.widgets["Comparison"]],layout=Layout(height='500px', width='400px'))
            self.widgets["Track"].set_title(0, 'Current')
            self.widgets["Track"].set_title(1, 'History')
            self.widgets["Track"].set_title(2, 'Comparison')
            
            self.widgets["OutputU"] = ipw.HBox([self.widgets["Summary"],self.widgets["Track"]], layout=ipw.Layout(justify_content='flex-end',height='500px'))
            
            self.widgets["Output"] = ipw.VBox([self.widgets["LabelSum"],self.widgets["OutputU"],self.widgets["Labeldata"],self.datagrid], layout=ipw.Layout(justify_content='flex-start',width = '1200px',height = "1600px"))
            
            self.widgets["controls"] = ipw.HBox([self.widgets["LEFT"],self.widgets["Output"]
                                               ], layout=ipw.Layout(justify_content='center',align_item='flex-end'))
            
            self.children = [self.widgets["controls"]]
            
    def read_ui(self):
        
        metrics = { "MaxMin": self.widgets["MaxMin"].value,
                     "Objet": self.widgets["Objet"].value,
                     "salesbuys": self.widgets["salesbuys_"].value,
                     "portfolio": self.widgets["PORTFOLIO_"].value,
                     "solver":self.widgets['solver'].value,
                     "size":self.widgets['size'].value,
                     "Yield_lower": self.widgets["Yield_lower"].value,
                     "Yield_upper": self.widgets["Yield_upper"].value,
                     "Spread_lower": self.widgets["Spread_lower"].value,
                     'Spread_upper':self.widgets["Spread_upper"].value,
                     'Duration_lower': self.widgets["Duration_lower"].value,
                     'Duration_upper':self.widgets["Duration_upper"].value,
                     'Maturity_lower':self.widgets["Maturity_lower"].value,
                     'Maturity_upper':self.widgets["Maturity_upper"].value,
                     'SCR_lower':self.widgets["SCR_lower"].value,
                     'SCR_upper': self.widgets["SCR_upper"].value,
                     'ESG_SCORE_lower': self.widgets["ESG_SCORE_lower"].value,
                     'ESG_SCORE_upper' : self.widgets["ESG_SCORE_upper"].value,
                     'CI_lower' : self.widgets["CI_lower"].value,
                     'CI_upper': self.widgets["CI_upper"].value,
                     "Decarb_lower": self.widgets["Decarb_lower"].value,
                     "Decarb_upper":self.widgets["Decarb_upper"].value,
                     "WARF_lower": self.widgets["WARF_lower"].value,
                     "WARF_upper":self.widgets["WARF_upper"].value,
                     "PnL_lower": self.widgets["PnL_lower"].value,
                     "PnL_upper":self.widgets["PnL_upper"].value,
                     "weight_lower": self.widgets["weight_lower"].value,
                     "weight_upper": self.widgets["weight_upper"].value,
                     'recommendation' : self.widgets['recommendation'].value,
                     'turnover' : [self.widgets['turnover_lower'].value/100,self.widgets['turnover_upper'].value/100],
                     'nonzero':self.widgets['nonzero'].value,
                     'unit':self.widgets["unit"].value,
                     "fixed_size":self.widgets['fixed_size'].value
             }
        
        buffers = {}
        
        filters_metrics = { "Yield_lower_filter" : self.widgets['Yield_lower_filter'].value,
                   "Yield_upper_filter" : self.widgets['Yield_upper_filter'].value,
                   "Spread_lower_filter" : self.widgets['Spread_lower_filter'].value,
                   "Spread_upper_filter" : self.widgets['Spread_upper_filter'].value,
                   "Duration_lower_filter" : self.widgets['Duration_lower_filter'].value,
                   "Duration_upper_filter" : self.widgets['Duration_upper_filter'].value,
                   "Maturity_lower_filter" : self.widgets['Maturity_lower_filter'].value,
                   "Maturity_upper_filter" : self.widgets['Maturity_upper_filter'].value,
                   "SCR_lower_filter" : self.widgets['SCR_lower_filter'].value,
                   "SCR_upper_filter" : self.widgets['SCR_upper_filter'].value,
                   "ESG_SCORE_lower_filter" : self.widgets['ESG_SCORE_lower_filter'].value,
                   "ESG_SCORE_upper_filter" : self.widgets['ESG_SCORE_upper_filter'].value,
                   "CI_lower_filter" : self.widgets['CI_lower_filter'].value,
                   "CI_upper_filter" : self.widgets['CI_upper_filter'].value,
                   "WARF_lower_filter" : self.widgets['WARF_lower_filter'].value,
                   "WARF_upper_filter" : self.widgets['WARF_upper_filter'].value,
                   
            }

        filters_groups = {}
    
        for group in ["Sectors_filter","Ratings_filter","Seniority_filter","Maturity_filter","Country_filter","ESG_RATING_filter","Ticker_filter"]:
            values = [x.value for x in self.widgets[group].children]
            desc = [x.description[:len(x.description)] for x in self.widgets[group].children]
            group_dict = dict(zip(desc,values))    
            filters_groups[group] = group_dict
        
        for buffer in ["buffer_Sectors","buffer_Ratings","buffer_Seniorities","buffer_Maturities","buffer_Countries","buffer_ESG_Ratings","buffer_Tickers"]:
            values = [x.value for x in self.widgets[buffer+'LEFT'].children]
            desc = [x.description[:len(x.description)-2] for x in self.widgets[buffer+'LEFT'].children]
            buffer_dict = dict(zip(desc,values))
            buffer_dict = {key:val for key, val in buffer_dict.items() if val != 'Buffer:'}
            buffers[buffer] = buffer_dict
            
        # if "Cashflow" in self.df.columns:
        #     values = [x.value for x in self.widgets['buffer_CashFlowsLEFT'].children]
        #     desc = [x.description[:len(x.description)-2] for x in self.widgets['buffer_CashFlowsLEFT'].children]
        #     buffer_dict = dict(zip(desc,values))
        #     buffer_dict = { int(key):val for key, val in buffer_dict.items() if val != 'Buffer:'}
        #     buffers["buffer_Cashflows"] = buffer_dict
            
        return metrics,buffers, filters_metrics,filters_groups
    
    def run_optimizer(self,click):
        
        try:
            self.widgets['solution'].value='Running...' 
            self.widgets["RUN"].disabled = True

            metrics,buffers,filters_metrics,filters_groups = self.read_ui()

            if metrics['MaxMin'] == 'Maximize':
                maxmin = True
            else:
                maxmin = False

            df_filtered = self.df.copy()
            df_filtered = df_filtered[(df_filtered['Yield']<=filters_metrics["Yield_upper_filter"]) & (df_filtered['Yield']>=filters_metrics["Yield_lower_filter"]) &
                                      (df_filtered['Curr. Spread']<=filters_metrics["Spread_upper_filter"]) & (df_filtered['Curr. Spread']>=filters_metrics["Spread_lower_filter"]) &
                                      (df_filtered['Duration']<=filters_metrics["Duration_upper_filter"]) & (df_filtered['Duration']>=filters_metrics["Duration_lower_filter"]) &
                                      (df_filtered['SRC']<=filters_metrics["SCR_upper_filter"]) & (df_filtered['SRC']>=filters_metrics["SCR_lower_filter"]) & 
                                      (df_filtered['ESG_SCORE']<=filters_metrics["ESG_SCORE_upper_filter"]) & (df_filtered['ESG_SCORE']>=filters_metrics["ESG_SCORE_lower_filter"])&
                                      (df_filtered['CI']<=filters_metrics["CI_upper_filter"]) & (df_filtered['CI']>=filters_metrics["CI_lower_filter"]) & 
                                      (df_filtered['YTM']<=filters_metrics["Maturity_upper_filter"]) & (df_filtered['YTM']>=filters_metrics["Maturity_lower_filter"]) & 
                                      (df_filtered['WARF']<=filters_metrics["WARF_upper_filter"]) & (df_filtered['WARF']>=filters_metrics["WARF_lower_filter"])]

            for key, subdict in filters_groups.items():
                filters_groups[key] = [x for x in subdict.keys() if subdict[x] is True]

            subkeys_to_keep =  [value for sublist in filters_groups.values() for value in sublist]

            filtered_buffers = {
                key: {subkey: buffers[key][subkey] for subkey in subkeys_to_keep if subkey in buffers[key]}
                for key in buffers
            }

            # if 'Cashflow' in self.df.columns:
            #     filtered_buffers['buffer_Cashflows'] = buffers['buffer_Cashflows']

            df_filtered = df_filtered[(df_filtered["Sector"].isin(filters_groups['Sectors_filter'])) &
                                      (df_filtered["SBR"].isin(filters_groups['Ratings_filter'])) & 
                                      (df_filtered["Seniority"].isin(filters_groups['Seniority_filter'])) & 
                                      (df_filtered["MaturityB"].isin(filters_groups['Maturity_filter'])) & 
                                      (df_filtered["Issuer Country"].isin(filters_groups['Country_filter'])) & 
                                      (df_filtered["ESG_RATING"].isin(filters_groups['ESG_RATING_filter'])) & 
                                      (df_filtered["Ticker"].isin(filters_groups['Ticker_filter']))
                                      ]

            OP = Optimizer(thresholds = {
                                         "Yield" :[metrics["Yield_lower"],metrics["Yield_upper"]],
                                         "Spreads":[metrics["Spread_lower"],metrics["Spread_upper"]],
                                         "Duration":[metrics["Duration_lower"],metrics["Duration_upper"]],
                                         "Maturity":[metrics["Maturity_lower"],metrics["Maturity_upper"]],
                                         "Risk Charge":[metrics["SCR_lower"],metrics["SCR_upper"]],
                                         "ESG_SCORE":[metrics["ESG_SCORE_lower"],metrics["ESG_SCORE_upper"]],
                                         "CI":[metrics["CI_lower"],metrics["CI_upper"]],
                                         "WARF" :[metrics["WARF_lower"],metrics["WARF_upper"]],
                                         "Decarb" :[metrics["Decarb_lower"],metrics["Decarb_upper"]],
                                         "PnL" :[metrics["PnL_lower"],metrics["PnL_upper"]],
                                         "Weight":[metrics["weight_lower"],metrics['weight_upper']]
                                        },
                                          buffers = filtered_buffers,
                                          weights = [metrics["weight_lower"],
                                          metrics['weight_upper']],
                                          recommendation = metrics['recommendation'],
                                          turnover =  metrics['turnover' ],
                                          nonzero = metrics['nonzero'],
                                          size = metrics['size'],
                                          unit = metrics["unit"],
                                          fixed_size = metrics["fixed_size"]
                          )

            if "Cashflow" in self.df.columns:
                output,too_strict, order,multi,bounds = OP.optimize(df_filtered.copy(),total=metrics['size'],var=metrics['Objet'],
                                                                    maximize = maxmin ,optimizer=metrics['solver'],output_strict=True,
                                                                    constraints=["buffer_Sectors"])
            else:
                output,too_strict, order,multi,bounds = OP.optimize(df_filtered.copy(),total=metrics['size'],var=metrics['Objet'],
                                                                    maximize = maxmin ,optimizer=metrics['solver'],output_strict=True,
                                                                    constraints=["buffer_Sectors","buffer_Ratings","buffer_Seniorities","buffer_Maturities","buffer_Countries",
                                                                                 "buffer_ESG_Ratings","buffer_Tickers",
                                                                                 "Duration","Yield","Spreads",'WARF',"Decarb","ESG_SCORE",
                                                                                 "Risk Charge","CI","Maturity","size","nonzero"
                                                                                ])
                
#                 output,too_strict, order,multi,bounds = OP.optimize(df_filtered.copy(),total=metrics['size'],var=metrics['Objet'],
#                                                                     maximize = maxmin ,optimizer=metrics['solver'],output_strict=True,
#                                                                     constraints=["buffer_Sectors"

#                                                                                 ])
                
            log = {}

            metrics['turnover_lower'] = metrics['turnover'][0]
            metrics['turnover_upper'] = metrics['turnover'][1]
            del metrics["turnover"]
            log.update(metrics)
            update_subdicts(buffers)
            log.update(flatten_double_dict(buffers))

            if too_strict == 0:

                self.output_df = output

                self.widgets["Sectors__"].children = [child for child in self.widgets["Sectors__"].children if child != self.axs1]
                self.widgets["Seniorities__"].children = [child for child in self.widgets["Sectors__"].children if child != self.axs2]
                self.widgets["Ratings__"].children = [child for child in self.widgets["Ratings__"].children if child != self.axs3]
                self.widgets["ESG Ratings__"].children = [child for child in self.widgets["ESG Ratings__"].children if child != self.axs4]
                self.widgets["Countries__"].children = [child for child in self.widgets["Countries__"].children if child != self.axs5]
                self.widgets["Maturities__"].children = [child for child in self.widgets["Maturities__"].children if child != self.axs6]
                self.widgets["Tickers__"].children = [child for child in self.widgets["Tickers__"].children if child != self.axs7]

                df_1 = pd.DataFrame(output.groupby(['Sector'])['final_wt'].sum() *100).rename(columns={"final_wt":'Percentage after optimization'}).sort_values('Percentage after optimization',ascending = False)
                df_1 = df_1.reset_index()
                df_1 = df_1.rename(columns={'Sector' : 'Sector of bonds'})
                df_1 = df_1.set_index("Sector of bonds")
                fig1 = go.Figure()
                self.df_1 = pd.DataFrame(output.groupby(['Sector'])['Notional Amount'].sum() *100 /output['Notional Amount'].sum()).rename(columns={"Notional Amount":'Percentage before optimization'}).sort_values('Percentage before optimization',ascending = False).dropna()
                self.df_1['Percentage before optimization'] = self.df_1['Percentage before optimization'].apply(lambda x : f"{np.round(x,2)}%")
                self.df_1 = self.df_1.reset_index()
                self.df_1 = self.df_1.rename(columns={'Sector' : 'Sector of bonds'})
                self.df_1 = self.df_1.set_index("Sector of bonds")
                fig1 = go.Figure()
                fig1.add_trace(go.Bar(x=self.df_1.index, y=self.df_1['Percentage before optimization'].apply(lambda x : float(x[:len(x)-1])),name='Percentage before optimization'))
                fig1.add_trace(go.Bar(x=df_1.index, y=df_1['Percentage after optimization'],name='Percentage after optimization'))
                fig1.update_layout( legend=dict(
                                    orientation="h",  
                                    yanchor="top",    
                                    y=1.1  ))
                self.axs1 = go.FigureWidget(data = fig1)
                df_1['Percentage after optimization'] = df_1['Percentage after optimization'].apply(lambda x : f"{np.round(x,2)}%")
                df_1 = pd.merge(self.df_1, df_1, left_index=True, right_index=True)
                df_1 = df_1.rename(index={'Sector': 'Sector of bonds'})
                self.datagrid1 = DataGrid(df_1.sort_index(ascending=True),editable = True,layout=ipw.Layout(width = "auto",height = "1000px"))
                self.datagrid1.auto_fit_columns = True
                self.widgets["Sectors_"] = self.datagrid1

                df_2 = pd.DataFrame(output.groupby(['Seniority'])['final_wt'].sum()*100).rename(columns={"final_wt":'Percentage after optimization'}).sort_values('Percentage after optimization',ascending = False)
                self.df_2 = pd.DataFrame(output.groupby(['Seniority'])['Notional Amount'].sum() *100 /output['Notional Amount'].sum()).rename(columns={"Notional Amount":'Percentage before optimization'}).sort_values('Percentage before optimization',ascending = False).dropna()
                self.df_2['Percentage before optimization'] = self.df_2['Percentage before optimization'].apply(lambda x : f"{np.round(x,2)}%")
                fig2 = go.Figure()
                fig2.add_trace(go.Bar(x=self.df_2.index, y=self.df_2['Percentage before optimization'].apply(lambda x : float(x[:len(x)-1])),name='Percentage before optimization'))
                fig2.add_trace(go.Bar(x=df_2.index, y=df_2['Percentage after optimization'],name='Percentage after optimization'))
                fig2.update_layout( legend=dict(
                                    orientation="h",  
                                    yanchor="top",    
                                    y=1.1  ))
                self.axs2 = go.FigureWidget(data = fig2)
                df_2['Percentage after optimization'] = df_2['Percentage after optimization'].apply(lambda x : f"{np.round(x,2)}%")
                df_2 = pd.merge(self.df_2, df_2, left_index=True, right_index=True)
                self.datagrid2 = DataGrid(df_2.sort_index(ascending=True),editable = True,layout=ipw.Layout(width = "auto",height = "1000px"))
                self.datagrid2.auto_fit_columns = True
                self.widgets["Seniorities_"] = self.datagrid2



                df_3 = pd.DataFrame(output.groupby(['SBR'])['final_wt'].sum()*100).rename(columns={"final_wt":'Percentage after optimization'}).sort_values('Percentage after optimization',ascending = False)
                self.df_3 = pd.DataFrame(output.groupby(['SBR'])['Notional Amount'].sum() *100 /output['Notional Amount'].sum()).rename(columns={"Notional Amount":'Percentage before optimization'}).sort_values('Percentage before optimization',ascending = False)
                self.df_3['Percentage before optimization'] = self.df_3['Percentage before optimization'].apply(lambda x : f"{np.round(x,2)}%")
                self.df_3 = self.df_3.reindex(bond_rating_order).dropna()
                fig3 = go.Figure()
                fig3.add_trace(go.Bar(x=self.df_3.index, y=self.df_3['Percentage before optimization'].apply(lambda x : float(x[:len(x)-1])),name='Percentage before optimization'))
                fig3.add_trace(go.Bar(x=df_3.index, y=df_3['Percentage after optimization'],name='Percentage after optimization'))
                fig3.update_layout( legend=dict(
                                    orientation="h", 
                                    yanchor="top",    
                                    y=1.1  ))
                self.axs3 = go.FigureWidget(data = fig3)
                df_3['Percentage after optimization'] = df_3['Percentage after optimization'].apply(lambda x : f"{np.round(x,2)}%")
                df_3 = pd.merge(self.df_3, df_3, left_index=True, right_index=True)
                self.datagrid3 = DataGrid(df_3,editable = True,layout=ipw.Layout(width = "auto",height = "1000px"))
                self.datagrid3.auto_fit_columns = True
                self.widgets["Ratings_"] = self.datagrid3

                df_4 = pd.DataFrame(output.groupby(['ESG_RATING'])['final_wt'].sum()*100).rename(columns={"final_wt":'Percentage after optimization'}).sort_values('Percentage after optimization',ascending = False)
                self.df_4 = pd.DataFrame(output.groupby(['ESG_RATING'])['Notional Amount'].sum() *100 /output['Notional Amount'].sum()).rename(columns={"Notional Amount":'Percentage before optimization'}).sort_values('Percentage before optimization',ascending = False)
                self.df_4['Percentage before optimization'] = self.df_4['Percentage before optimization'].apply(lambda x : f"{np.round(x,2)}%")
                self.df_4 = self.df_4.reindex(esg_order).dropna()
                fig4 = go.Figure()
                fig4.add_trace(go.Bar(x=self.df_4.index, y=self.df_4['Percentage before optimization'].apply(lambda x : float(x[:len(x)-1])),name='Percentage before optimization'))
                fig4.add_trace(go.Bar(x=df_4.index, y=df_4['Percentage after optimization'],name='Percentage after optimization'))
                fig4.update_layout( legend=dict(
                                    orientation="h",  
                                    yanchor="top",    
                                    y=1.1  ))
                self.axs4 = go.FigureWidget(data = fig4)
                df_4['Percentage after optimization'] = df_4['Percentage after optimization'].apply(lambda x : f"{np.round(x,2)}%")
                df_4 = pd.merge(self.df_4, df_4, left_index=True, right_index=True)
                self.datagrid4 = DataGrid(df_4,editable = True,layout=ipw.Layout(width = "auto",height = "1000px"))
                self.datagrid4.auto_fit_columns = True
                self.widgets["ESG Ratings_"] = self.datagrid4



                df_5 = pd.DataFrame(output.groupby(['Issuer Country'])['final_wt'].sum()*100).rename(columns={"final_wt":'Percentage after optimization'}).sort_values('Percentage after optimization',ascending = False)
                df_5['Percentage after optimization'] = df_5['Percentage after optimization'].apply(lambda x : f"{np.round(x,2)}%")
                self.df_5 = pd.DataFrame(output.groupby(['Issuer Country'])['Notional Amount'].sum() *100 /output['Notional Amount'].sum()).rename(columns={"Notional Amount":'Percentage before optimization'}).sort_values('Percentage before optimization',ascending = False).dropna()
                self.df_5['Percentage before optimization'] = self.df_5['Percentage before optimization'].apply(lambda x : f"{np.round(x,2)}%")
                df_5 = pd.merge(self.df_5, df_5, left_index=True, right_index=True)
                fig5 = go.Figure()
                fig5.add_trace(go.Bar(x=df_5.index[:10], y=df_5['Percentage before optimization'].apply(lambda x : float(x[:len(x)-1]))[:10],name='Percentage before optimization'))
                fig5.add_trace(go.Bar(x=df_5.index[:10], y=df_5['Percentage after optimization'].apply(lambda x : float(x[:len(x)-1]))[:10],name='Percentage after optimization'))
                fig5.update_layout( legend=dict(
                                    orientation="h",  
                                    yanchor="top",   
                                    y=1.1  ))
                self.axs5 = go.FigureWidget(data = fig5)
                self.datagrid5 = DataGrid(df_5.sort_index(ascending=True),editable = True,layout=ipw.Layout(width = "auto",height = "1000px"))
                self.datagrid5.auto_fit_columns = True
                self.widgets["Countries_"] = self.datagrid5

                df_6 = pd.DataFrame(output.groupby(['MaturityB'])['final_wt'].sum()*100).rename(columns={"final_wt":'Percentage after optimization'}).sort_values('Percentage after optimization',ascending = False)
                self.df_6 = pd.DataFrame(output.groupby(['MaturityB'])['Notional Amount'].sum() *100 /output['Notional Amount'].sum()).rename(columns={"Notional Amount":'Percentage before optimization'}).sort_values('Percentage before optimization',ascending = False)
                self.df_6['Percentage before optimization'] = self.df_6['Percentage before optimization'].apply(lambda x : f"{np.round(x,2)}%")
                self.df_6 = self.df_6.reindex(maturity_order).dropna()
                fig6 = go.Figure()
                fig6.add_trace(go.Bar(x=self.df_6.index, y=self.df_6['Percentage before optimization'].apply(lambda x : float(x[:len(x)-1])),name='Percentage before optimization'))
                fig6.add_trace(go.Bar(x=df_6.index, y=df_6['Percentage after optimization'],name='Percentage after optimization'))
                fig6.update_layout( legend=dict(
                                    orientation="h", 
                                    yanchor="top",    
                                    y=1.1  ))
                self.axs6 = go.FigureWidget(data = fig6)
                df_6['Percentage after optimization'] = df_6['Percentage after optimization'].apply(lambda x : f"{np.round(x,2)}%")
                df_6 = pd.merge(self.df_6, df_6, left_index=True, right_index=True)
                self.datagrid6 = DataGrid(df_6,editable = True,layout=ipw.Layout(width = "auto",height = "1000px"))
                self.datagrid6.auto_fit_columns = True
                self.widgets["Maturities_"] = self.datagrid6

                df_7 = pd.DataFrame(output.groupby(['Ticker'])['final_wt'].sum()*100).rename(columns={"final_wt":'Percentage after optimization'}).sort_values('Percentage after optimization',ascending = False)
                self.df_7 = pd.DataFrame(output.groupby(['Ticker'])['Notional Amount'].sum() *100 /output['Notional Amount'].sum()).rename(columns={"Notional Amount":'Percentage before optimization'}).sort_values('Percentage before optimization',ascending = False).dropna()
                self.df_7['Percentage before optimization'] = self.df_7['Percentage before optimization'].apply(lambda x : f"{np.round(x,2)}%")
                df_7['Percentage after optimization'] = df_7['Percentage after optimization'].apply(lambda x : f"{np.round(x,2)}%")
                df_7 = pd.merge(self.df_7, df_7, left_index=True, right_index=True)
                fig7 = go.Figure()
                fig7.add_trace(go.Bar(x=df_7.index[:20], y=df_7['Percentage before optimization'].apply(lambda x : float(x[:len(x)-1]))[:20],name='Percentage before optimization'))
                fig7.add_trace(go.Bar(x=df_7.index[:20], y=df_7['Percentage after optimization'].apply(lambda x : float(x[:len(x)-1]))[:20],name='Percentage after optimization'))
                fig7.update_layout( legend=dict(
                                    orientation="h",  
                                    yanchor="top",   
                                    y=1.1  ) )
                self.axs7 = go.FigureWidget(data = fig7)
                self.datagrid7 = DataGrid(df_7.sort_index(ascending=True),editable = True,layout=ipw.Layout(width = "auto",height = "1000px"))
                self.datagrid7.auto_fit_columns = True
                self.widgets["Tickers_"] = self.datagrid7


                output['initial'] = output['Notional Amount'] 
                output["change"] = output['final'] - output['initial']
#                 if "Cashflow" in output.columns:
#                     change_ = (output.groupby("MaturityYear")['initial'].sum() - output.groupby("MaturityYear")['final'].sum()).to_frame()
#                     change_.columns = ['change']
#                     df_9 = (output.drop_duplicates(subset=["MaturityYear"])[["MaturityYear","Cashflow"]].sort_values(by="MaturityYear").set_index("MaturityYear")["Cashflow"] - change_["change"]).to_frame()
#                     df_9.columns = ['Cashflow after optimization']
#                     self.df_9 = output.drop_duplicates(subset=["MaturityYear"])[["MaturityYear","Cashflow"]].sort_values(by="MaturityYear").set_index("MaturityYear").rename(columns={"Cashflow":"Cashflow before optimization"})
#                     self.df_9['Cashflow before optimization'] = self.df_9['Cashflow before optimization'].apply(lambda x : np.round(x,2))
#                     df_9['Cashflow after optimization'] = df_9['Cashflow after optimization'].apply(lambda x : np.round(x,2))
#                     df_9 = pd.merge(self.df_9, df_9, left_index=True, right_index=True)
#                     fig9 = go.Figure()
#                     fig9.add_trace(go.Bar(x=df_9.index, y=df_9['Cashflow before optimization'],name='Cashflow before optimization'))
#                     fig9.add_trace(go.Bar(x=df_9.index, y=df_9['Cashflow after optimization'],name='Cashflow after optimization'))
#                     fig9.update_layout( legend=dict(
#                                         orientation="h",  
#                                         yanchor="top",   
#                                         y=1.1  ) )
#                     self.axs9 = go.FigureWidget(data = fig9)
#                     self.datagrid9 = DataGrid(df_9,editable = True,layout=ipw.Layout(width = "auto",height = "1000px"))
#                     self.datagrid9.auto_fit_columns = True
#                     self.widgets["Cashflow"] = self.datagrid9

#                 else:
#                     self.widgets["CashFlows_"] = ipw.Output()

                self.widgets["Sectors__"] = ipw.Tab([self.widgets["Sectors_"],self.axs1],layout=Layout(height='500px', width='auto'))
                self.widgets["Sectors__"].set_title(0, 'Table')
                self.widgets["Sectors__"].set_title(1, 'Chart')

                self.widgets["Seniorities__"] = ipw.Tab([self.widgets["Seniorities_"],self.axs2],layout=Layout(height='500px', width='auto'))
                self.widgets["Seniorities__"].set_title(0, 'Table')
                self.widgets["Seniorities__"].set_title(1, 'Chart')

                self.widgets["Ratings__"] = ipw.Tab([self.widgets["Ratings_"],self.axs3],layout=Layout(height='500px', width='auto'))
                self.widgets["Ratings__"].set_title(0, 'Table')
                self.widgets["Ratings__"].set_title(1, 'Chart')

                self.widgets["ESG Ratings__"] = ipw.Tab([self.widgets["ESG Ratings_"],self.axs4],layout=Layout(height='500px', width='auto'))
                self.widgets["ESG Ratings__"].set_title(0, 'Table')
                self.widgets["ESG Ratings__"].set_title(1, 'Chart')

                self.widgets["Countries__"] = ipw.Tab([self.widgets["Countries_"],self.axs5],layout=Layout(height='500px', width='auto'))
                self.widgets["Countries__"].set_title(0, 'Table')
                self.widgets["Countries__"].set_title(1, 'Chart')

                self.widgets["Maturities__"] = ipw.Tab([self.widgets["Maturities_"],self.axs6],layout=Layout(height='500px', width='auto'))
                self.widgets["Maturities__"].set_title(0, 'Table')
                self.widgets["Maturities__"].set_title(1, 'Chart')

                self.widgets["Tickers__"] = ipw.Tab([self.widgets["Tickers_"],self.axs7],layout=Layout(height='500px', width='auto'))
                self.widgets["Tickers__"].set_title(0, 'Table')
                self.widgets["Tickers__"].set_title(1, 'Chart')

                # if 'Cashflow' in output.columns:
                #     self.widgets["CashFlows_"] = ipw.Tab([self.widgets["Cashflow"],self.axs9],layout=Layout(height='500px', width='auto'))
                #     self.widgets["CashFlows_"].set_title(0, 'Table')
                #     self.widgets["CashFlows_"].set_title(1, 'Chart')

                self.widgets["Summary"].children = [self.widgets["Sectors__"],self.widgets["Seniorities__"],self.widgets["Ratings__"],self.widgets["ESG Ratings__"],self.widgets["Countries__"],self.widgets["Maturities__"],self.widgets["Tickers__"]]

                df_8 = pd.DataFrame({"Metrics":["Yield","Duration","Maturity","ESG_SCORE","CI","Decarb","WARF"],"Average after optimization":
                                                                          [(output["Yield"] *  output['final_wt']).sum(),
                                                                          (output["Duration"] *  output['final_wt']).sum(),
                                                                          (output["YTM"] *  output['final_wt']).sum(),
                                                                          (output["ESG_SCORE"] *  output['final_wt']).sum(),
                                                                          (output["CI"] *  output['final_wt']).sum(),
                                                                          (output["Decarb"] *  output['final_wt']).sum(),
                                                                          (output["WARF"] *  output['final_wt']).sum()]}).set_index("Metrics")
                log.update({"Yield":(output["Yield"] *  output['final_wt']).sum(),'Duration': (output["Duration"] *  output['final_wt']).sum(),
                            "Maturity":(output["YTM"] *  output['final_wt']).sum(),"ESG_SCORE":(output["ESG_SCORE"] *  output['final_wt']).sum(),
                            "CI":(output["CI"] *  output['final_wt']).sum(),"Decarb":(output["Decarb"] *  output['final_wt']).sum(),"WARF":(output["WARF"] *  output['final_wt']).sum()})

                log['Simulation Name'] = self.widgets['SimuName'].value

                self.history.append(log)
                hist_df = pd.DataFrame(self.history)

                self.widgets["x_axis"].options = hist_df.columns.tolist()[3:-1]
                self.widgets["y_axis"].options = hist_df.columns.tolist()[3:-1]

                duplicates = hist_df.duplicated('Simulation Name')
                counts = hist_df.groupby('Simulation Name').cumcount() + 1
                hist_df.loc[duplicates, 'Simulation Name'] = hist_df.loc[duplicates, 'Simulation Name'] + '_' + counts.astype(str)
                hist_df = hist_df.set_index("Simulation Name")

                datagrid_ = DataGrid(hist_df.transpose(),editable = True,layout=ipw.Layout(width = "auto",height = "1000px"))
                datagrid_.auto_fit_columns = True
                self.datagrid_hist = datagrid_

                self.df_8 = pd.DataFrame({"Metrics":["Yield","Duration","Maturity","ESG_SCORE","CI","Decarb","WARF"],"Average":
                                                                          [(output["Yield"] *  output['Notional Amount']).sum()/output['Notional Amount'].sum(),
                                                                          #(output["Curr. Spread"] *  output['Notional Amount']).sum()/output['Notional Amount'].sum(),
                                                                          (output["Duration"] *  output['Notional Amount']).sum()/output['Notional Amount'].sum(),
                                                                          (output["YTM"] *  output['Notional Amount']).sum()/output['Notional Amount'].sum(),
                                                                          #(output["SRC"] *  output['Notional Amount']).sum()/output['Notional Amount'].sum(),
                                                                          (output["ESG_SCORE"] *  output['Notional Amount']).sum()/output['Notional Amount'].sum(),
                                                                          (output["CI"] *  output['Notional Amount']).sum()/output['Notional Amount'].sum(),
                                                                          (output["Decarb"] *  output['Notional Amount']).sum()/output['Notional Amount'].sum(),
                                                                          (output["WARF"] *  output['Notional Amount']).sum()/output['Notional Amount'].sum()]})\
                                                                          .rename(columns={"Average":"Average before optimization"}).set_index("Metrics")

                df_8 = pd.merge(self.df_8, df_8, left_index=True, right_index=True)
                df_8 = df_8.apply(lambda x : np.round(x,2))
                self.datagrid8 = DataGrid(df_8,editable = True,layout=ipw.Layout(width = "auto",height = "1000px"))
                self.datagrid8.auto_fit_columns = True
                self.widgets["Metrics_"] = self.datagrid8
                self.widgets["Track"].children = [self.widgets["Metrics_"],self.datagrid_hist,self.widgets["Comparison"]]
                self.widgets["solution"].value = 'Solution found !'

                try:
                    output = output[["ISIN","SecDes","Ticker","Issuer","Sector",'Subsector',"Seniority","MaturityB","Issuer Country","ESG_RATING",'SBR','WARF',"Decarb",'Curr. Spread',"Yield","Duration","YTM","SRC","ESG_SCORE","CI","Notional Amount","initial_wt","final_wt","final"]]
                except:
                    output = output[["ISIN","Ticker","Sector","Seniority","MaturityB","Issuer Country","ESG_RATING",'SBR','WARF',"Decarb",'Curr. Spread',"Yield","Duration","YTM","SRC","ESG_SCORE","CI","Notional Amount","initial_wt","final_wt","final","MaturityYear"]]

                prev_pf = set(output[output['initial_wt'] != 0]['ISIN'])
                curr_pf = set(output[output['final'] != 0]['ISIN'])
                changes = len(prev_pf.symmetric_difference(curr_pf))
                print("Turnover rate: ",changes / len(prev_pf) * 100)

                datagrid = DataGrid(output,editable = True, layout=ipw.Layout(width = "auto",height = "1000px"))
                datagrid.auto_fit_columns = True
                self.datagrid = datagrid
                self.widgets["Labeldata"] = ipw.Label(value = 'Bond level data (after optimization)')
                self.widgets["OutputU"].children = [self.widgets["Summary"],self.widgets["Track"]]
                self.widgets["Output"].children = [self.widgets["LabelSum"],self.widgets["OutputU"],self.widgets["Labeldata"],self.datagrid]
                self.widgets["controls"].children = [self.widgets["LEFT"],self.widgets["Output"]]
                self.children = [self.widgets["controls"]]

            else:

                for key in bounds:
                    try:
                        bounds[key] = np.round(bounds[key],2)
                    except:
                        for key_ in bounds[key]:
                            bounds[key][key_] = np.round(bounds[key][key_],2)
                if metrics['recommendation'] == True:
                    self.widgets["solution"].value = f'Optimal solution not found. Strict constraints : {[item for sublist in list(order .values()) for item in sublist] }.' +  f"<br>Recommended thresholds: {bounds}"
                else:
                    self.widgets["solution"].value = 'Optimal solution not found.'
            self.widgets["RUN"].disabled = False
            
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            self.widgets['solution'].value='Optimization failed. Please try again.' 
        finally:
            self.widgets["RUN"].disabled = False          

    def scatterplot(self,click):
        
        hist_df = pd.DataFrame(self.history)
        
        duplicates = hist_df.duplicated('Simulation Name')
        counts = hist_df.groupby('Simulation Name').cumcount() + 1
        hist_df.loc[duplicates, 'Simulation Name'] = hist_df.loc[duplicates, 'Simulation Name'] + '_' + counts.astype(str)       
        hist_df = hist_df.set_index("Simulation Name")
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x= hist_df[self.widgets["x_axis"].value], y=hist_df[self.widgets["y_axis"].value],mode='markers',text=hist_df.index.tolist()))
        
        fig.update_layout(
                        xaxis={'title': {'text': self.widgets["x_axis"].value}},
                        yaxis={'title': {'text': self.widgets["y_axis"].value}},
                        
                    )
        
        self.comparison = go.FigureWidget(data = fig)
        
        self.widgets["Comparison"].children = [self.widgets["Comparison_"],self.comparison]
        self.widgets["Track"].children = [self.widgets["Metrics_"],self.datagrid_hist,self.widgets["Comparison"]]
        self.widgets["OutputU"].children = [self.widgets["Summary"],self.widgets["Track"]]
        self.widgets["Output"].children = [self.widgets["LabelSum"],self.widgets["OutputU"],self.widgets["Labeldata"],self.datagrid]
        self.widgets["controls"].children = [self.widgets["LEFT"],self.widgets["Output"]]
        self.children = [self.widgets["controls"]]
        
    def reset(self,click):
        self.df = self.df.rename(columns = dict(zip([x.value for x in self.widgets['mapping'].children],[x.description for x in self.widgets['mapping'].children])))
        self.show_mapping = 0
        if 'MaturityYear' in self.df.columns:
            self.df = self.df[self.df["EligibilityRC"] == "Y"]
            self.df = self.df.merge(cashflow,on='MaturityYear',how='left') 
        self.df["Ticker"] = self.df["Ticker"].fillna('NA')
        self.df["ESG_RATING"] = self.df["ESG_RATING"].fillna('N')
        self.df["CI"] = self.df["CI"].fillna(0)
        self.df["ESG_SCORE"] = self.df["ESG_SCORE"].fillna(0)
        self.df["WARF"] = self.df["WARF"].fillna(0)
        self.df = self.df.fillna(0).reset_index(drop=True)
        print(len(self.df))
        self._build_view()
        