import scipy.linalg as scla
import scipy.stats as stats
import scipy.sparse as spar
import numpy as np
import numpy.linalg as la
from ...utils import splogdet, chol_mvn
from ...steps import metropolis

def sample(Model):
    st = Model.state

    ### Sample the Beta conditional posterior
    ### P(beta | . ) \propto L(Y|.) \dot P(\beta) 
    ### is
    ### N(Sb, S) where
    ### S = (X' Sigma^{-1}_Y X + S_0^{-1})^{-1}
    ### b = X' Sigma^{-1}_Y (Y - Delta Alphas) + S^{-1}\mu_0
    covm_update = st.X.T.dot(st.PsiSigma2i).dot(st.X)
    covm_update += st.Betas_cov0i
    covm_update = la.inv(covm_update) 

    resids = st.y - st.Delta.dot(st.Alphas)
    XtSresids = st.X.T.dot(st.PsiSigma2i).dot(resids)
    mean_update = XtSresids + st.Betas_cov0i.dot(st.Betas_mean0)
    mean_update = np.dot(covm_update, mean_update)
    st.Betas = chol_mvn(mean_update, covm_update)
    st.XBetas = np.dot(st.X, st.Betas)

    ### Sample the Random Effect conditional posterior
    ### P( Alpha | . ) \propto L(Y|.) \dot P(Alpha | \lambda, Tau2)
    ###                               \dot P(Tau2) \dot P(\lambda)
    ### is
    ### N(Sb, S)
    ### Where
    ### S = (Delta'Sigma_Y^{-1}Delta + Sigma_Alpha^{-1})^{-1}
    ### b = (Delta'Sigma_Y^{-1}(Y - X\beta) + 0)
    covm_update = st.Delta.T.dot(st.PsiSigma2).dot(st.Delta)
    covm_update += st.PsiTau2i
    covm_update = la.inv(covm_update)

    resids = st.y - st.XBetas
    mean_update = st.Delta.T.dot(st.PsiSigma2i).dot(resids)
    mean_update = np.dot(covm_update, mean_update)
    st.Alphas = chol_mvn(mean_update, covm_update)
    st.DeltaAlphas = np.dot(st.Delta, st.Alphas)

    ### Sample the Random Effect aspatial variance parameter
    ### P(Tau2 | .) \propto L(Y|.) \dot P(\Alpha | \lambda, Tau2)
    ###                            \dot P(Tau2) \dot P(\lambda)
    ### is
    ### IG(J/2 + a0, u'(\Psi(\lambda))^{-1}u * .5 + b0)
    bn = st.Alphas.T.dot(st.PsiLambdai).dot(st.Alphas) * .5 + st.Tau2_b0
    st.Tau2 = stats.invgamma.rvs(st.Tau2_an, scale=bn)
    st.PsiTau2 = st.Ij * st.Tau2
    st.PsiTau2i = la.inv(st.PsiTau2)
    
    ### Sample the response aspatial variance parameter
    ### P(Sigma2 | . ) \propto L(Y | .) \dot P(Sigma2)
    ### is
    ### IG(N/2 + a0, eta'Psi(\rho)^{-1}eta * .5 + b0)
    ### Where eta is the linear predictor, Y - X\beta + \DeltaAlphas
    eta = st.y - st.XBetas - st.DeltaAlphas
    bn = eta.T.dot(st.PsiRhoi).dot(eta) * .5 + st.Sigma2_b0
    st.Sigma2 = stats.invgamma.rvs(st.Sigma2_an, scale=bn)
    st.PsiSigma2 = st.In * st.Sigma2
    st.PsiSigma2i = la.inv(st.PsiSigma2)
    
    Model.cycles += 1
