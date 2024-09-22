from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

app= Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///registration.sqlite3'
db=SQLAlchemy(app)

@app.route("/")

#CREATING DATABASE

#creating 3 db tables
class Registration(db.Model):
    __tablename__= "registrations"
    userId=db.Column("id",db.Integer, primary_key=True)
    firstName=db.Column("first_Name", db.String(20))
    lastName=db.Column("last_Name", db.String(20))
    email=db.Column("email", db.String(30))
    password=db.Column("password", db.String(20),unique=True)
    login= db.relationship("Login", backref="registration")
    userInformation = db.relationship("User_information", backref="registration")

    
    #requirements for users
    def __init(self,firstName,lastName,email,password):
        self.firstName = firstName
        self.lastName= lastName
        self.email= email
        self.password=password



class Login(db.Model):
    __tablename__= "login"
    _id=db.Column("id",db.Integer, primary_key=True)
    dateCreated= ("date_Created", db.Integer)
    destination_state= ("destination_state", db.String(10))
    pdf_link= ("pdf_Link", db.String(30))
    registration_id= db.Column(db.Integer,db.ForeignKey("registrations.id"))



    
    def __init(self, dateCreated, destination_state, pdf_link):
        self.dateCreated= dateCreated
        self.destination_state=destination_state
        self.pdf_link=pdf_link

class User_information(db.Model):
    __tablename__= "user_information"
    _id=db.Column("id",db.Integer, primary_key=True)
    keywords_picked= db.Column("keywords_picked", db.String(30))
    registration_id= db.Column(db.Integer,db.ForeignKey("registrations.id"))


    def __init(self,keywords_picked):
        self.keywords_picked=keywords_picked

with app.app_context():
    db.create_all()

#CREATING FLASK PAGES 
@app.route('/')
def home():
    return "This is the homepage"
@app.route('/sign in', methods=["POST", "GET"])
def sign_in():
    if request.method =="POST":
        username= request.form['username']
        password= request.form['password']
        #need a return statement to redirect user to next page which should be flight & car

    return "Welcome to the sign in page"
@app.route('/', methods=["POST", "GET"])
def register():
    return "Welcome to the register page"
@app.route('/flightandcar')
def flight_car():
    return "Welcome to the flight and cars page"
@app.route('/hotel')
def hotel():
    return "Welcome to the hotel page"
@app.route('/itinerary')
def itinerary():
    return "Welcome to the itinerary"
@app.route('/confirmation')
def confirmation():
    return "Welcome to the confirmation page Confirmation page"







if __name__=="__main__":
    app.run(debug=True)
    
    

#f.close()   