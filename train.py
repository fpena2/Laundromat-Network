import os
import pandas as pd
import pickle

from sklearn.model_selection import GridSearchCV, train_test_split

# R^4 input - ts, current, seconds, avg - current

# TODO: argparse for cli training of models

def train_model(data_path, model, param_grid, label_str, out_path = "./models", header=0, index_col=False, cv=5, train_size=0.8, refit=True, scoring=None, stratify=False):
    assert scoring is not None, "provide a scoring metric"
    if not os.path.isfile(data_path):
        raise ValueError(f"{data_path} does not exist")

    assert param_grid is not None, "No param grid provided"
    assert train_size <= 0.9 and train_size >= 0.5, "too little training data increase train_size"
    df = pd.read_csv(data_path, header=header, index_col=index_col) 
    if label_str not in df.columns:
        raise ValueError(f"{label_str} is not a column in the dataset")

    y = df[label_str]
    y += 0.001
    X = df.drop(["ect", "status"], axis=1)
    if label_str.lower() == "ect":
        X = X.drop("epoch_time", axis=1)

    X["avg_curr_diff"] = X["current"] - X["current"].mean()
    X_train, X_test, y_train, y_test = None, None, None, None
    if stratify:
        X_train, X_test, y_train, y_test = train_test_split(X, y, train_size=train_size, stratify=y)
    else:
        X_train, X_test, y_train, y_test = train_test_split(X, y, train_size=train_size)

    search = GridSearchCV(model, param_grid, cv=cv, scoring=scoring, refit=refit) 
    search.fit(X_train, y_train)

    tuned_model = search.best_estimator_
    tuned_params = search.best_params_
    score = tuned_model.score(X_test, y_test)

    tuned_model.fit(X, y)
    if out_path:
        with open(out_path, "wb") as fid:
            pickle.dump(tuned_model, fid)

    return tuned_model, tuned_params, score

if __name__ == "__main__":
    #from sklearn.gaussian_process import GaussianProcessClassifier
    #from sklearn.gaussian_process.kernels import RBF, ConstantKernel, Matern
    #from sklearn.neighbors import KNeighborsClassifier
    from sklearn.linear_model import GammaRegressor
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    out_path = os.path.join("models", "gamma_regressor.pkl")
    data_path = os.path.join("data", "hand_labeled_data.csv")
    label_str = "ect"
    param_grid = {"estimator__alpha": [0.1, 0.2, 0.5, 0.7, 0.8, 0.9]}
    scoring = "neg_mean_gamma_deviance"
    stratify = False
    model = GammaRegressor()
    standard_scaler = StandardScaler()
    pipe = Pipeline(steps=[("scaler", standard_scaler), ("estimator", model)])
    
    pipe, params, score = train_model(data_path, pipe, param_grid, label_str, out_path=out_path, train_size=0.8, cv=5, scoring=scoring, stratify=stratify)
    print("======= Train Stats =======")
    print("prediction_score =", score)
    print("best params =", params)
    print("fitted model =", pipe)
