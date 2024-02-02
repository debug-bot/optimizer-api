from sklearn.preprocessing import StandardScaler
import numpy as np
import cvxpy as cp
import itertools
import pandas as pd
from tqdm import tqdm

class Constraint:
    
    def __init__(self):
        pass
    
    #Inequalities clusters
    def constraint_ineq(self,df,field,categories=[],thresholds=[],rng=True):
        if rng==True:
            for i,(cat,th) in enumerate(zip(categories,thresholds)):
                th = list(th)
                c1=-(np.ones(shape=(len(df),1))*(np.array(df[field]==cat) ).reshape(-1,1)).T
                c2=-c1
                if i==0:
                    G=np.concatenate([c1,c2])
                    h=np.array([-th[0],th[1]]).reshape(-1,1)  
                else:
                    G=np.concatenate([G,c1,c2])
                    h=np.concatenate([h,np.array([-th[0],th[1]]).reshape(-1,1)]).reshape(-1,1)
                
        else:
            for i,(cat,th) in enumerate(zip(categories,thresholds)):
                th = list(th)
                c1=-(np.ones(shape=(len(df),1))*(np.array(df[field]==cat) ).reshape(-1,1)).T
    
                if i==0:
                    G=np.concatenate([c1])
                    h=np.array([-th]).reshape(-1,1)  
                else:
                    G=np.concatenate([G,c1])
                    h=np.concatenate([h,np.array([-th]).reshape(-1,1)]).reshape(-1,1)            

        return G,h,len(G)
    
    #Inequalities metrics
    def constraint_ineq_metrics(self,df,metric,thresholds=[],rng=True):
        if rng==True:
            #c1=-np.array((df['Notional Amount'].astype('float') * df[metric].astype('float'))/df['Notional Amount'].astype('float').sum()).reshape(1,-1)
            c1=-np.array(df[metric].astype('float')).reshape(1,-1)
            c2=-c1
            G=np.concatenate([c1,c2])
            h=np.array([-thresholds[0],thresholds[1]]).reshape(-1,1)
        
        else:
            #c1=-np.array((df['Notional Amount'].astype('float') * df[metric].astype('float'))/df['Notional Amount'].sum()).reshape(1,-1)
            c1=-np.array(df[metric].astype('float')).reshape(1,-1)
            G=np.concatenate([c1])
            h=np.array([-thresholds[0]]).reshape(-1,1)            

        return G,h
        
    #Constraint for Notional
    def constraint_not(self,df,tot=10):
        G=np.eye(len(df))*tot 
        h=np.array(df['Notional Amount'].astype('float64')  ).reshape(-1,1) 
        
        return G,h 
    
    #Constraint for individual bonds
    def constraint_individual(self,df,xmin,xmax):
        c1=-np.eye(len(df))
        c2=-c1
        G_=np.concatenate([c1,c2])
        h_=np.array([np.array([[-xmin] for i in range(len(df))]),np.array([[xmax] for i in range(len(df))])]).reshape(-1,1)
        return G_,h_
    
    #Constraint for weights summing to 1
    def constraint_sum_one(self,df):
        #A=np.array(df['Notional Amount'].astype('float')/df['Notional Amount'].sum()).reshape(1,-1)
        A=np.array([[1.0] for i in range(len(df))]).reshape(1,-1)
        b=np.array([1.0]).reshape(-1,1)
        return A,b

class Optimizer(Constraint):
    def __init__(self, thresholds, buffers, weights, recommendation, turnover, size, nonzero, unit, fixed_size, 
                 column_names = {"buffer_Sectors":"Sector",
                                 "buffer_Ratings":"SBR", 
                                 "buffer_Seniorities":"Seniority",
                                 "buffer_Maturities":"MaturityB",
                                 "buffer_Countries":"Issuer Country", 
                                 'buffer_ESG_Ratings':'ESG_RATING',
                                 "buffer_Tickers":"Ticker",
                                 "Duration":"Duration",
                                 "Yield":"Yield",
                                 'WARF':'WARF',
                                 "ESG_SCORE":"ESG_SCORE",
                                 "Risk Charge":"SRC",
                                 "CI":"CI",
                                 "Maturity":"YTM",
                                 "Spreads":"Curr. Spread",
                                 "size":'Notional Amount'}):
        
        super().__init__()
        
        self.thresholds=thresholds
        self.buffers=buffers
        self.weights = weights
        self.column_names = column_names
        self.recommendation = recommendation
        self.turnover = turnover
        self.nonzero = nonzero
        self.size = size
        self.unit = unit
        self.fixed_size = fixed_size
    
    def optimize(self, df, num_nzero=100, constraints=['Sectors'],
                 var='Yield', var_min = 'Duration', maximize=True, total=10,
                 optimizer = "cvxpy", output_strict = True,
                 ratio_increment_penalty = 0.2, ratio_penalty = 0.1):
        
        var='ESG_SCORE' if var=='ESG Score' else var
        var='CI' if var=='Carbon Intensity (EVIC)' else var
        var='CI_' if var=='Carbon Intensity (Sales)' else var
        var='Decarb' if var=='Decarbonization' else var
        
        G=np.empty_like(np.ones(shape=df.shape[0])).reshape(1,-1)
        h=np.empty_like(np.ones(shape=1)).reshape(-1,1)
        
        #if self.unit == 'None':
        df['Notional Amount'] = df['Notional Amount']/1e6
        total = total * 1e3
    
        for constraint in self.column_names.keys():
            if constraint in constraints and constraint in self.buffers.keys() and constraint != "buffer_Cashflows":
                bmk_ = pd.DataFrame(df.groupby(self.column_names[constraint])['Notional Amount'].sum()/df['Notional Amount'].sum())
                bmk_["buffer"] = bmk_.index.map(self.buffers[constraint])
                bmk_["threshold"] = bmk_.apply(lambda x: [(max(x["Notional Amount"] - x["buffer"], 0), min(x["Notional Amount"] + x["buffer"], 1))], axis=1)
                bmk_["threshold"] = bmk_["threshold"].apply(lambda x : list(x[0]))

                G_,h_,length=self.constraint_ineq(df.copy(),field= self.column_names[constraint] ,categories=bmk_.index.tolist(),thresholds=bmk_.threshold.tolist())
                if len(G)==1:
                    G=G_
                    h=h_
                else:
                    G=np.concatenate([G,G_])
                    h=np.concatenate([h,h_])
            if constraint in constraints and constraint in self.thresholds.keys() and constraint not in ["Weight",'size',"nonzero"]:
                G_,h_=self.constraint_ineq_metrics(df.copy(),metric= self.column_names[constraint],thresholds=[float(self.thresholds[constraint][0]),float(self.thresholds[constraint][1])])
                if len(G)==1:
                    G=G_
                    h=h_
                else:
                    G=np.concatenate([G,G_])
                    h=np.concatenate([h,h_])    

        G_not,h_not=self.constraint_not(df.copy(),tot=float(total))
        
        G=np.concatenate([G,G_not])
        h=np.concatenate([h,h_not])
        
        G_,h_=self.constraint_individual(df.copy(),xmin=self.weights[0],xmax=self.weights[1])
        G=np.concatenate([G,G_])
        h=np.concatenate([h,h_])       
        
        A,b = self.constraint_sum_one(df.copy())      
        c = -np.array(df[var].astype('float')).reshape(-1,1)  if maximize==True else  np.array(df[var].astype('float')).reshape(-1,1)     
        x = cp.Variable(len(df))
        h=h.ravel()
        obj = cp.Minimize(c.T @ x)
        constraints_cp = [A @ x == b, G @ x <= np.squeeze(h)]
                       
        prob = cp.Problem(obj, constraints_cp)
        prob.solve(verbose=True)
        status = prob.status
        
        print('status: ',status)
        df['initial_wt']=np.round(df['Notional Amount']/df['Notional Amount'].sum(),4)*1

        soln=np.array(x.value)

        df['final_wt']=list(np.round(soln,4).ravel()*1)
        df['final']=np.round(df['final_wt']*total,8)
        print(len(df[df.final_wt!=0]))
        print('Yield: ', sum(df['Yield'] * df["final_wt"]))
        
        try:
            df['PnL']=(df['CPX']-df['BPX'])*(df['sales_nominal'])*0.01
            print(df.PnL.sum())
        except:
            pass
            
        return df,False,[],[],[]
