import pandas as pd
import numpy as np
import os
import pymc as pm
import arviz as az
import matplotlib.pyplot as plt

def load_data(filepath):
    print("Trying to load:", filepath)
    print("Full absolute path:", os.path.abspath(filepath))
    df = pd.read_csv(filepath)
    data = df.drop(columns=["Informant"]).to_numpy()
    return data

def run_cct_model(X):
    N, M = X.shape

    with pm.Model() as model:
        D = pm.Uniform("D", lower=0.5, upper=1.0, shape=N)
        Z = pm.Bernoulli("Z", p=0.5, shape=M)

        D_reshaped = D[:, None]
        p = Z * D_reshaped + (1 - Z) * (1 - D_reshaped)

        X_obs = pm.Bernoulli("X_obs", p=p, observed=X)

        trace = pm.sample(300, chains=2, return_inferencedata=True)


    return model, trace

def naive_majority_vote(X):
    return (X.mean(axis=0) > 0.5).astype(int)

if __name__ == "__main__":
    X = load_data("data/plant_knowledge.csv")
    print(X)
    print("Shape:", X.shape)

    model, trace = run_cct_model(X)

    az.plot_posterior(trace, var_names=["D"])
    plt.show() # Close this plot window manually to continue
    az.plot_posterior(trace, var_names=["Z"])
    plt.show() # Close this too to allow script to finish printing

    summary = az.summary(trace, var_names=["D", "Z"])
    print(summary)

    majority_vote = naive_majority_vote(X)
    print("Naive majority vote:", majority_vote)

    posterior_Z = trace.posterior["Z"].mean(dim=["chain", "draw"]).values
    cct_consensus = np.round(posterior_Z).astype(int)
    print("CCT consensus:", cct_consensus)

    mismatches = majority_vote != cct_consensus
    print("Disagreements:", mismatches.sum(), "out of", len(majority_vote))

    posterior_D = trace.posterior["D"].mean(dim=["chain", "draw"]).values
    most_competent = np.argmax(posterior_D)
    least_competent = np.argmin(posterior_D)

    print("Most competent informant: P" + str(most_competent + 1))
    print("Least competent informant: P" + str(least_competent + 1))
