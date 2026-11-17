import logging

import azure.functions as func

from prediction import make_prediction

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


@app.route(route="predict")
def predict(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request.")

    tenure = req.params.get("tenure")
    monthly = req.params.get("monthly")
    techsupport = req.params.get("techsupport")

    if not (tenure and monthly and techsupport):
        return func.HttpResponse(
            "Pass tenure, monthly and techsupport in the query string.",
            status_code=400,
        )

    try:
        prediction = make_prediction(
            tenure=float(tenure),
            MonthlyCharges=float(monthly),
            TechSupport_yes=float(techsupport),
        )
    except ValueError:
        return func.HttpResponse(
            "tenure, monthly and techsupport must be numbers.", status_code=400
        )

    return func.HttpResponse(str(prediction))
