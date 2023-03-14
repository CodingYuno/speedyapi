# speedyapi

An easy to use Python module for creating Restful API.

Built on `Flask` / `Async Flask` with features for easily creating API endpoints

Features:
- Parameter Parsing and Checking
- API Authentication
- Rate Limiting (user, address, global)
- In depth Endpoint Testing (Write tests to be ran to confirm endpoints act as intended)
- Automatic OpenAPI `swagger.json` Generation (with access to full specification)
- Common JSON Response Formatting

# Dependencies

- **[Python](https://www.python.org/downloads/)** 3.10
- **[Requests](https://github.com/kennethreitz/requests)** >= 2.9.2
- **[Flask](https://github.com/pallets/flask)** >= 2.2

# Example Usage

```python
from speedyapi import API, QueryParameter, PathParameter, respond, request, Test, types
from speedyapi.swagger_objects import InfoObject, XLogoObject


info = InfoObject(title="Example API", version="1.0.1")

app = API(__name__, info=info)
app.swagger.info.logo = XLogoObject(url="")
app.swagger.info.description = "# Introduction\nThis is an example API for the speedyapi python module."


@app.authentication(apikey_required=True, description="Example apikey: `CorrectApikey`")
def auth():
    return "allowed" if request.apikey == "CorrectApikey" else None


@app.endpoint(path="/maths/<method>", method="GET", authentication="allowed", name="Simple Maths", description="Simple operations.")
@app.limits(user_limits=["10/min"], ip_limits=["30/min"], global_limits=["5000/5 min"])
@app.tests(Test(url="/maths/multiply?a=3&b=5", headers={"Apikey": "CorrectApikey"}, expected_status_code=200, checks=[lambda x: x["result"] == 15]),
           Test(url="/maths/multiply?a=3&b=5", headers={"Apikey": "WrongApikey"}, expected_status_code=403),
           Test(url="/maths/modulo?a=3&b=5", headers={"Apikey": "CorrectApikey"}, expected_status_code=422),
           Test(url="/maths/multiply?a=3&b=5", expected_status_code=400))
@app.parameters(PathParameter(name="method", options=["multiply", "divide", "add", "subtract"], default="add", description="Choose operation."),
                QueryParameter(name="a", type=types.Number, required=True, description="First number to use."),
                QueryParameter(name="b", type=types.Number, required=True, description="Second number to use."))
def simple_maths_endpoint(method, a, b):
    methods = {"multiply": lambda x, y: x * y, "divide": lambda x, y: x / y, "add": lambda x, y: x + y, "subtract": lambda x, y: x - y}
    return respond.json({"result": methods[method](a, b), "method": method, "authentication": request.authentication})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, tests=True, threaded=True)
```

```
------------------------------------------------------------------------------------------
 *  Test on path `/maths/multiply - - GET` returned correct status code 200 [Time: 2.12s] - - {"success": true, "result": 15, "method": "multiply", "authentication": "allowed"}
 *  Test on path `/maths/multiply - - GET` Success [Time: 2.12s] - - {"success": true, "result": 15, "method": "multiply", "authentication": "allowed"}
 *  Test on path `/maths/modulo - - GET` returned correct status code 422 [Time: 2.12s] - - {"success": false, "cause": "Malformed [method]"}
 *  Test on path `/maths/multiply - - GET` returned correct status code 400 [Time: 2.12s] - - {"success": false, "cause": "Missing one or more fields [key]"}
 *  Test on path `/maths/multiply - - GET` returned correct status code 403 [Time: 2.12s] - - {"success": false, "cause": "Access is forbidden, usually due to an invalid API key being used."}
 *  Tests Completed - - (Success: 5/5) - [Time: 2.13s]
 -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  - 
 *  API Ready - - [Running on: http://0.0.0.0:80/] - - (Press CTRL+C to quit!)
------------------------------------------------------------------------------------------
```
