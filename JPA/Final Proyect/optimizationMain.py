from resampledOptimization import resampledAllocation
import seaborn as sns
import pandas as pd

def computeAssetsMeanVariance(data):
    ret = data.pct_change()
    mu = ret.mean()
    omega = ret.cov()
    return mu, omega

if __name__ == '__main__':
#    p = pd.read_excel('L:\\Rates & FX\\Quant Analysis\\py\\Optimizacion\\indices.xlsx', sheetname='prices_short', headers=1, index_col=0)
#    names = pd.read_excel('L:\\Rates & FX\\Quant Analysis\\py\\Optimizacion\\indices.xlsx', sheetname='Classif', headers=0)
#    rA = resampledAllocation()
#    s = p.columns
#    mu, omega = rA.computeAssetsMeanVariance(p)
#    pr, pv, pw = rA.portfolioOptimization(mu,omega)
#    sim_mu, sim_sigma, avg_mu, avg_sigma, avg_w = rA.reSampledFrontier(mu,omega,60)
#    rA.plotEfficientFrontier(sim_mu, sim_sigma, avg_mu, avg_sigma)
#    average_weight = abs(pd.DataFrame(data = avg_w, columns = s))
#    average_weight = average_weight.transpose()
#    
#    tuples = list(zip(names['assetclass'],names['indexname']))
#    index = pd.MultiIndex.from_tuples(tuples,names=['Asset Class','Index Name'])
#    weights = pd.DataFrame(data=average_weight.values, index=index)
#    w_class = weights.groupby(weights.index.get_level_values(0)).sum()
##    sns.palplot(sns.color_palette("Set3", 20))
#    sns.set_palette('RdBu_r',15)
#    w_class.transpose().plot(kind='area', ylim = [0,1])

## Analisis Fondos
#    p = pd.read_excel('L:\\Rates & FX\\Quant Analysis\\py\\Optimizacion\\fondos.xlsx', sheetname='precio', headers=1, index_col=0)
#    names = pd.read_excel('L:\\Rates & FX\\Quant Analysis\\py\\Optimizacion\\fondos.xlsx', sheetname='Classif', headers=0)
#    rA = resampledAllocation()
#    s = p.columns
#    mu, omega = rA.computeAssetsMeanVariance(p)
#    pr, pv, pw = rA.portfolioOptimization(mu,omega)
#    sim_mu, sim_sigma, avg_mu, avg_sigma, avg_w = rA.reSampledFrontier(mu,omega,60)
#    rA.plotEfficientFrontier(sim_mu, sim_sigma, avg_mu, avg_sigma)
#    average_weight = abs(pd.DataFrame(data = avg_w, columns = s))
#    average_weight = average_weight.transpose()
#    
#    tuples = list(zip(names['assetclass'],names['indexname']))
#    index = pd.MultiIndex.from_tuples(tuples,names=['Asset Class','Index Name'])
#    weights = pd.DataFrame(data=average_weight.values, index=index)
#    w_class = weights.groupby(weights.index.get_level_values(0)).sum()
##    sns.palplot(sns.color_palette("Set3", 20))
#    sns.set_palette('RdBu_r',15)
#    w_class.transpose().plot(kind='area', ylim = [0,1])

## Analisis Fondos
    p = pd.read_excel('spmac.xlsx', sheetname='precio', headers=1, index_col=0)
    names = pd.read_excel('spmac.xlsx', sheetname='Classif', headers=0)
    rA = resampledAllocation()
    s = p.columns
    mu, omega = rA.computeAssetsMeanVariance(p)
    pr, pv, pw = rA.portfolioOptimization(mu,omega)
    sim_mu, sim_sigma, avg_mu, avg_sigma, avg_w = rA.reSampledFrontier(mu,omega,30)
#    rA.plotEfficientFrontier(sim_mu, sim_sigma, avg_mu, avg_sigma)
    rA.plotEfficientFrontier(np.asarray(pr), np.asarray(pv), np.asarray(pr), np.asarray(pv))
#    average_weight = abs(pd.DataFrame(data = avg_w, columns = s))
    average_weight = abs(pd.DataFrame(data = pw, columns = s))
    average_weight = average_weight.transpose()
    
    tuples = list(zip(names['assetclass'],names['indexname']))
    index = pd.MultiIndex.from_tuples(tuples,names=['Asset Class','Index Name'])
    weights = pd.DataFrame(data=average_weight.values, index=index)
    w_class = weights.groupby(weights.index.get_level_values(0)).sum()
#    sns.palplot(sns.color_palette("Set3", 20))
    sns.set_palette('RdBu_r',15)
    w_class.transpose().plot(kind='area', ylim = [0,1])