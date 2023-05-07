# This service is dedicated for the UI team only
# and contains APIs related to their use

from datetime import date
from sqlite3 import Date
from flask import Flask
import datetime
import os

# from microservice_1.src.status import AUTH_MISSING_TOKEN
from kafka import KafkaConsumer
from mongoengine import *
from models import User, Robot
from functools import wraps
from flask import Flask, jsonify, request
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
)


app = Flask(__name__)
jwt = JWTManager(app)


app.config["MONGODB_SETTINGS"] = {"db": "cloud", "host": "13.57.249.237", "port": 27017}


try:
    db = connect(
        db=app.config["MONGODB_SETTINGS"]["db"],
        host=app.config["MONGODB_SETTINGS"]["host"],
        port=app.config["MONGODB_SETTINGS"]["port"],
    )

    print("Database connection established.")
except ConnectionError:
    print("Unable to establish a database connection.")
# consumer = KafkaConsumer("my-topic", bootstrap_servers="localhost:9092")


app.config["JWT_SECRET_KEY"] = "CMPE-295-B"


def set_token_cookie(response, token):
    response.set_cookie("access_token", token, httponly=True)
    return response


# Below are the APIs


@app.route("/login", methods=["POST"])
def login():
    print("Login Request Received!")
    data = request.json
    print(data)

    user = User.objects(email=data["email"]).first()
    if not user:
        return jsonify({"message": "Invalid email or password"}), 401

    # Check if the provided password matches
    if user.password != data["password"]:
        return jsonify({"message": "Invalid email or password"}), 401

    # Here we will be query the db

    # generate a token
    access_token = create_access_token(identity=str(user.email))

    # Successful login
    # return (
    #     jsonify(
    #         {
    #             "message": "Login successful",
    #             "access_token": access_token,
    #             "response_code": 200,
    #         }
    #     ),
    #     200,
    # )

    response = jsonify(
        {"message": "Authentication successful", "access_token": access_token}
    )
    response = set_token_cookie(response, access_token)
    return response, 200


@app.route("/signup", methods=["POST"])
def signup():
    data = request.json

    # Check if the user already exists
    existing_user = User.objects(email=data["email"]).first()
    if existing_user:
        return jsonify({"message": "Email already exists"}), 400

    # Create a new user
    new_user = User(
        user_type=data["user_type"],
        email=data["email"],
        password=data["password"],
        first_name=data["first_name"],
        last_name=data["last_name"],
        modified=datetime.datetime.now(),
    )
    try:
        new_user.save()
        return jsonify({"message": "User registered successfully"}), 201
    except Exception as e:
        return jsonify({"message": "Failed to register user", "error": str(e)}), 500


# ToBeTested
@app.route("/updateProfile", methods=["PUT"])
@jwt_required()
def update_profile():
    data = request.json

    # Find the user based on the provided user ID
    user = User.objects(email=data["email"]).first()
    if not user:
        return jsonify({"message": "User not found"}), 404

    # Update the user's profile information
    user.first_name = data.get("first_name", user.first_name)
    user.last_name = data.get("last_name", user.last_name)
    user.email = data.get("email", user.email)

    try:
        user.save()
        return jsonify({"message": "Profile updated successfully"}), 200
    except Exception as e:
        return jsonify({"message": "Failed to update profile", "error": str(e)}), 500


@app.route("/getRobots", methods=["GET"])
@jwt_required()
def get_robots():
    robots = Robot.objects()

    response = []
    for robot in robots:
        response.append(
            {
                "id": robot.id,
                "serial_no": robot.serial_no,
                "user_id": robot.user_id,
                "status": robot.status,
            }
        )

    return jsonify({"robots": response}), 200


# MarkedForLater
@app.route("/move", methods=["POST"])
@app.route("/getLocation", methods=["GET"])
@jwt_required()
def get_location():
    data = request.json

    robot_id = data.get("robot_id")

    # Check if the robot exists
    robot = Robot.objects(id=robot_id).first()
    if not robot:
        return jsonify({"response_code": "Error", "message": "Robot not found"}), 404

    # Get the location coordinates
    location = robot.location
    if not location:
        return (
            jsonify({"response_code": "Error", "message": "Location not available"}),
            400,
        )

    x_coordinate = location["coordinates"][0]
    y_coordinate = location["coordinates"][1]

    return jsonify({"x_coordinate": x_coordinate, "y_coordinate": y_coordinate}), 200


@app.route("/registerRobot", methods=["POST"])
@jwt_required()
def register_robot():
    data = request.json

    user_id = data.get("user_id")
    robot_id = data.get("robot_id")

    # Check if the user exists
    user = User.objects(id=user_id).first()
    if not user:
        return jsonify({"response_code": "Error", "message": "User not found"}), 404

    # Check if the robot exists
    robot = Robot.objects(id=robot_id).first()
    if not robot:
        return jsonify({"response_code": "Error", "message": "Robot not found"}), 404

    # Update the robot's user_id in the database
    robot.update(user_id=user_id)

    return (
        jsonify(
            {"response_code": "Success", "message": "Robot registered successfully"}
        ),
        200,
    )


@app.route("/deregisterRobot", methods=["POST"])
@jwt_required()
def deregister_robot():
    data = request.json

    user_id = data.get("user_id")
    robot_id = data.get("robot_id")

    # Check if the user exists
    user = User.objects(id=user_id).first()
    if not user:
        return jsonify({"response_code": "Error", "message": "User not found"}), 404

    # Check if the robot exists
    robot = Robot.objects(id=robot_id).first()
    if not robot:
        return jsonify({"response_code": "Error", "message": "Robot not found"}), 404

    # Check if the robot is registered to the specified user
    if robot.user_id != user_id:
        return (
            jsonify(
                {
                    "response_code": "Error",
                    "message": "Robot is not registered to the user",
                }
            ),
            400,
        )

    # Deregister the robot by setting its user_id to an empty string
    robot.update(user_id="")

    return (
        jsonify(
            {"response_code": "Success", "message": "Robot deregistered successfully"}
        ),
        200,
    )


@app.route("/assignMaster", methods=["POST"])
@jwt_required()
def assign_master():
    data = request.json

    user_id = data.get("user_id")
    robot_id = data.get("robot_id")

    # Check if the user exists
    user = User.objects(id=user_id).first()
    if not user:
        return jsonify({"response_code": "Error", "message": "User not found"}), 404

    # Check if the robot exists
    robot = Robot.objects(id=robot_id).first()
    if not robot:
        return jsonify({"response_code": "Error", "message": "Robot not found"}), 404

    # Assign the master by updating the robot's user_id in the database
    robot.update(user_id=user_id)

    return (
        jsonify(
            {"response_code": "Success", "message": "Master assigned successfully"}
        ),
        200,
    )


@app.route("/getStats", methods=["GET"])
@app.route("/")
def hello():
    
    return "Hello! "


@app.route("/dummy", methods=["POST"])
def dummy():
    dummy = request.json
    print(dummy)
    print("The date is ", datetime.datetime.now())
    return "Hello!"


@app.route("/receive", methods=["GET"])
def receive_message():
    message = next(consumer)
    return message.value.decode("utf-8")


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
