from speedyapi import API, QueryParameter, PathParameter, JsonBodyParameter, respond, request, Test, types
from speedyapi.swagger_objects import InfoObject, XLogoObject


info = InfoObject(title="Maths API", version="1.0.1")

app = API(__name__, logger="requests.txt", print_traceback=True, info=info, user_limits=["8/min"], global_limits=["10000/min"])
app.swagger.info.logo = XLogoObject(url="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTFfIP_NiAxmaKhPf0noGYmO2d103EV_s1GWP4rt8pH&s")
app.swagger.info.description = "# Introduction\nThis is an example API for the speedyapi python module.\n\nPowered By: `Python` `Flask` `SpeedyAPI`"


@app.authentication(apikey_required=True, description="Example apikey: `ThisIsAnApikey`")
def auth():
    return "admin" if request.apikey == "ThisIsAnApikey" else None


@app.endpoint(path=f"/maths/<method>", method="GET", authentication="admin", name="Simple Maths", description="Simple operations between two given numbers.")
@app.limits(user_limits=["10/min", "120/2 hours"], ip_limits=["30/min"], global_limits=["5000/5 min"])
@app.tests(Test(url="/maths/multiply?a=3&b=5", headers={"Apikey": "ThisIsAnApikey"}, expected_status_code=200, checks=[lambda x: x["result"] == 15]),
           Test(url="/maths/multiply?a=3&b=5", headers={"Apikey": "WrongApikey"}, expected_status_code=403),
           Test(url="/maths/modulo?a=3&b=5", headers={"Apikey": "ThisIsAnApikey"}, expected_status_code=422),
           Test(url="/maths/multiply?a=3&b=5", expected_status_code=400))
@app.parameters(PathParameter(name="method", options=["multiply", "divide", "add", "subtract"], default="add", description="Choose some maths stuff."),
                QueryParameter(name="a", type=types.Number, required=True, description="First number to use."),
                QueryParameter(name="b", type=types.Number, required=True, description="Second number to use."))
def simple_maths_endpoint(method, a, b):
    methods = {"multiply": lambda x, y: x * y, "divide": lambda x, y: x / y, "add": lambda x, y: x + y, "subtract": lambda x, y: x - y}
    return respond.json({"result": methods[method](a, b), "method": method, "authentication": request.authentication})


@app.endpoint(path=f"/maths/<method>", method="POST", authentication=None, name="More Maths", description="Send a list of numbers to the server.")
@app.limits(user_limits=["10/min", "120/2 hours"], ip_limits=["10/min"])
@app.tests(Test(url="/maths/multiply", json={"a_numbers": [1, 2, 3], "b_numbers": [4, 5, 6]}, expected_status_code=200, checks=[lambda x: x["results"] == [4, 10, 18]]),
           Test(url="/maths/multiply?", json={"a_numbers": "not an array"}, expected_status_code=422),
           Test(url="/maths/multiply?", json={"numbers": [1, 2, 3, 4, 5]}, expected_status_code=400),
           Test(url="/maths/multiply?", expected_status_code=400))
@app.parameters(PathParameter(name="method", options=["multiply", "divide", "add", "subtract"], default="add", description="Choose some maths stuff."),
                JsonBodyParameter(name="a_numbers", checks=[lambda numbers: all(type(num) in [int, float] for num in numbers)], type=types.Array, description="Numbers to send."),
                JsonBodyParameter(name="b_numbers", checks=[lambda numbers: all(type(num) in [int, float] for num in numbers)], type=types.Array, description="Numbers to send."))
def maths_post_endpoint(method, a_numbers, b_numbers):
    methods = {"multiply": lambda x, y: x * y, "divide": lambda x, y: x / y, "add": lambda x, y: x + y, "subtract": lambda x, y: x - y}
    return respond.json({"results": [methods[method](a, b) for a, b in zip(a_numbers, b_numbers)], "method": method})


if __name__ == "__main__":
    app.run(threaded=True, host="0.0.0.0", port=80, tests=True)
