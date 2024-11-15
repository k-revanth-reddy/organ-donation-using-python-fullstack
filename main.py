from flask import Flask, request, render_template, session, redirect, url_for, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId  

cluster = MongoClient("127.0.0.1:27017")
db = cluster['organdonation']
donors = db['donors']
users = db['users']
donations = db['donations']
requests_db = db['requests']

app = Flask(__name__)
app.secret_key = "1234567890"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/registerpage")
def registerpage():
    return render_template("register.html")

@app.route("/donorregisterpage")
def donorregisterpage():
    return render_template("donorregister.html")

@app.route("/registerdata", methods=['POST'])
def registerdata():
    a = request.form.get("username")
    b = request.form.get("email")
    c = request.form.get("password")
    d = request.form.get("blood_type")
    e = request.form.get("contact")
    
    user = users.find_one({"email": b})
    if user:
        return render_template("register.html", status="User already exists with this email")
    
    users.insert_one({
        "username": a,
        "email": b,
        "password": c,
        "blood_type": d,
        "contact": e
    })
    return render_template("register.html", status="User registration successful")

@app.route("/donorregister", methods=['POST'])
def donorregisterdata():
    a = request.form.get("username")
    b = request.form.get("email")
    c = request.form.get("password")
    d = request.form.get("blood_type")
    e = request.form.get("contact")
    
    donor = donors.find_one({"email": b})
    if donor:
        return render_template("donorregister.html", status="Donor already exists with this email")
    
    donors.insert_one({
        "username": a,
        "email": b,
        "password": c,
        "blood_type": d,
        "contact": e
    })
    return render_template("donorregister.html", status="Donor registration successful")

@app.route("/userlogin")
def userlogin():
    return render_template("login.html")

@app.route("/userlogindata", methods=['POST'])
def userlogindata():
    a = request.form.get("username")
    b = request.form.get("password")
    
    user = users.find_one({"username": a})
    if user and user['password'] == b:
        session['username'] = a
        return redirect(url_for("dashboard"))
    
    return render_template("login.html", status="Invalid credentials")

@app.route("/dashboard")
def dashboard():
    if 'username' not in session:
        return redirect(url_for("userlogin"))
    
    donations_data = list(donations.find())
    
    requests_data = list(requests_db.find({"patientname": session['username']}))
    
    return render_template("dashboard.html", username=session['username'], donations=donations_data, requests=requests_data)

@app.route("/myrequests")
def userrequests():
    if 'username' not in session:
        return redirect(url_for("userlogin"))
    requestername=session['username']
    requestdata=list(requests_db.find_one({"patientname":requestername}))
    return render_template("myrequests.html",requests=requestdata)

@app.route("/donorlogin")
def donorlogin():
    return render_template("donorlogin.html")

@app.route("/donorlogindata", methods=['POST'])
def donorlogindata():
    a = request.form.get("username")
    b = request.form.get("password")
    
    donor = donors.find_one({"username": a})
    if donor and donor['password'] == b:
        session['donorusername'] = a
        return redirect(url_for("donordashboard"))
    
    return render_template("donorlogin.html", status="Invalid credentials")

@app.route("/donordashboard")
def donordashboard():
    if 'donorusername' not in session:
        return redirect(url_for("donorlogin"))
    
    requests_data = list(requests_db.find({"donor_username": session['donorusername']}))

    return render_template("donordashboard.html", username=session['donorusername'],organ_requests=requests_data)

@app.route("/donationform")
def donationform():
    return render_template("adddonation.html")

@app.route("/adddonation", methods=['POST'])
def adddonation():
    if 'username' not in session:
        return redirect(url_for("donorlogin"))
    
    donor_username = session['username']
    organ_type = request.form.get("organType")
    donor_name = request.form.get("donorName")
    donor_age = request.form.get("donorAge")
    blood_group = request.form.get("bloodGroup")
    gender = request.form.get("gender")
    image = request.form.get("image")
    
    donations.insert_one({
        "donor_username": donor_username, 
        "organType": organ_type,
        "donorName": donor_name,
        "donorAge": donor_age,
        "bloodGroup": blood_group,
        "gender": gender,
        "image": image
    })
    return render_template("adddonation.html", status="Donation added successfully!")

@app.route("/mydonations")
def mydonations():
    if 'donorusername' not in session:
        return redirect(url_for("donorlogin"))
    
    donor_username = session['donorusername']
    donations_data = list(donations.find({"donor_username": donor_username}))
    return render_template("mydonations.html", donations=donations_data)

@app.route("/request_donation/<donation_id>", methods=['POST'])
def request_donation(donation_id):
    if 'username' not in session:
        return redirect(url_for("userlogin"))

    user = session['username']
    patientdetails=users.find_one({"username":user})
    donation = donations.find_one({"_id": ObjectId(donation_id)})
    if donation:
        requests_db.insert_one({
            "donation_id": donation_id,
            "donor_username": donation['donor_username'],
            "patientname": user,
            "mobileno":patientdetails['contact'],
            "donorname":donation['donorName'],
            "organname":donation['organType'],
            "status": "Pending" 

        })
        return redirect(url_for("dashboard", message="Request sent successfully!"))
    else:
        return redirect(url_for("dashboard", message="Donation not found."))

@app.route("/handle_request/<request_id>/<action>", methods=['POST'])
def handle_request(request_id, action):
    if 'username' not in session:
        return jsonify({"success": False, "message": "Unauthorized"})


    request_record = requests_db.find_one({"_id": ObjectId(request_id)})

    if request_record:
        if action == 'accept':
            requests_db.update_one({"_id": ObjectId(request_id)}, {"$set": {"status": "Accepted"}})
            return jsonify({"success": True, "message": "Request accepted"})
        elif action == 'reject':
            requests_db.update_one({"_id": ObjectId(request_id)}, {"$set": {"status": "Rejected"}})
            return jsonify({"success": True, "message": "Request rejected"})
    return jsonify({"success": False, "message": "Request not found"})

@app.route('/logout')
def logout():
    session['username'] = None
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(port=6010, debug=True)
