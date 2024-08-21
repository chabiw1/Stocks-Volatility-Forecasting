import sqlite3

import matplotlib.pyplot as plt
import io
import base64

from config import settings
from data import SQLRepository
from fastapi import FastAPI
from model import GarchModel
from pydantic import BaseModel


# Task 8.4.14, `FitIn` class
class FitIn(BaseModel):
    ticker: str
    use_new_data: bool
    n_observations: int
    q: int
    p: int
    

# Task 8.4.14, `FitOut` class
class FitOut(FitIn):
    success: bool
    message: str
    #####################
    #plot: str
    ####################


# Task 8.4.18, `PredictIn` class
class PredictIn(BaseModel):
    ticker : str
    n_days : int

# Task 8.4.18, `PredictOut` class
class PredictOut(PredictIn):
    ticker : str
    n_days : int
    success : bool
    forecast: dict
    message : str

# Task 8.4.15
def build_model(ticker, use_new_data):

    # Create DB connection
    connection = sqlite3.connect(settings.db_name, check_same_thread=False)

    # Create `SQLRepository`
    repo = SQLRepository(connection=connection)

    # Create model
    model = GarchModel(ticker=ticker, use_new_data=use_new_data, repo=repo)

    # Return model
    return model


# Task 8.4.9
app = FastAPI()

# Task 8.4.11
# `"/hello" path with 200 status code
@app.get("/hello",status_code=200)
def hello():
    """Return dictionary with greeting message."""
    return {'message':'Hello World!'}


@app.post("/fit", status_code=200, response_model=FitOut)
# Task 8.4.16, `"/fit" path, 200 status code
def fit_model(request: FitIn):

    """Fit model, return confirmation message.

    Parameters
    ----------
    request : FitIn

    Returns
    ------
    dict
        Must conform to `FitOut` class
    """
    # Create `response` dictionary from `request`
    response = request.dict()

    # Create try block to handle exceptions
    try:
        # Build model with `build_model` function
        model = build_model(ticker=request.ticker, use_new_data=request.use_new_data)

        # Wrangle data
        model.wrangle_data(n_observations = request.n_observations)

        # Fit model
        model.fit(p=request.p, q=request.q)
        
        #find AIC and BIC
        aic = model.aic
        bic = model.bic

        # Save model
        filename = model.dump()

        # Add `"success"` key to `response`
        response["success"] = True

        #response["plot"] = img_base64


        # Add `"message"` key to `response` with `filename`
        response["message"] = (
            f"Trained and saved {filename}"
            "\n"
            f"Metrics: AIC {aic}, BIC {bic}."
        )
     
                                     
    # Create except block
    except Exception as e:

        # Add `"success"` key to `response`
        response["success"] = False

        # Add `"message"` key to `response` with error message
        response["message"] = str(e)

    # Return response
    return response

@app.post("/predict", status_code=200, response_model=PredictOut)
# Task 8.4.19 `"/predict" path, 200 status code
def get_prediction(request:PredictIn):

    # Create `response` dictionary from `request`
    response = request.dict()


    # Create try block to handle exceptions
    try:
        # Build model with `build_model` function
        model = build_model(ticker=request.ticker, use_new_data=False)

        # Load stored model
        model.load()

        # Generate prediction
        prediction = model.predict_volatility(horizon=request.n_days)

        # Add `"success"` key to `response`
        response["success"] = True

        # Add `"forecast"` key to `response`
        response["forecast"] = prediction

        # Add `"message"` key to `response`
        response["message"] = ""


    # Create except block
    except Exception as e:

        # Add `"success"` key to `response`
        response["success"] = False

        # Add `"forecast"` key to `response`
        response["forecast"] = {}

        #  Add `"message"` key to `response`
        response["message"] = str(e)


    # Return response
    return response
