from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow import ValidationError
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Table, String, Column,select, Boolean
from typing import List

#Initialize flask app
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = 'mysql+mysqlconnector://root:BAC146@localhost/flask_api_db'

#Create Base Class
class Base(DeclarativeBase):
    pass

#Initialize extensions
db = SQLAlchemy(model_class=Base)
db.init_app(app)
ma = Marshmallow(app)


#=========Models==========

#Associtation Table
user_pet = Table(
    "user_pet",
    Base.metadata,
    Column("user_id", ForeignKey("users.id")),
    Column("pet_id", ForeignKey("pets.id"))
)

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(200))

    #One-to-Many
    pets: Mapped[List["Pet"]] = relationship(secondary=user_pet, back_populates="owners")

class Pet(Base):
    __tablename__ = "pets"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    animal: Mapped[str] = mapped_column(String(100))

    #One-to-Many
    owners: Mapped[List["User"]] = relationship(secondary=user_pet, back_populates="pets")

class HouseHold(Base):
    __tablename__="households"

    id: Mapped[int] = mapped_column(primary_key=True)
    address: Mapped[str] = mapped_column(String(255))
    residence_type: Mapped[str] = mapped_column(String(100))
    fenced_yard: Mapped[bool] = mapped_column(Boolean())
    grass_access: Mapped[bool] = mapped_column(Boolean())



#========== Schemas ==========

class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User


class PetSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Pet

user_schema = UserSchema()
users_schema = UserSchema(many=True) #Allows for the serialization of a List of User objects
pet_schema = PetSchema()
pets_schema = PetSchema(many=True)


#=============== Routes ================

#CREATE a user
@app.route('/users', methods=['POST'])
def create_user():
    try:
        user_data = user_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    new_user = User(name=user_data['name'], email=user_data['email'])
    db.session.add(new_user)
    db.session.commit()

    return user_schema.jsonify(new_user), 201

#READ users
@app.route('/users', methods=['GET'])
def get_users():
    query = select(User)
    users = db.session.execute(query).scalars().all()

    return users_schema.jsonify(users), 200

#READ individual User
@app.route('/users/<int:id>', methods=['GET'])
def get_user(id):
    user = db.session.get(User, id)
    return user_schema.jsonify(user), 200

#UPDATE individual User
@app.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    user = db.session.get(User, id)

    if not user:
        return jsonify({"message": "Invalid user id"}), 400
    
    try:
        user_data = user_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    user.name = user_data['name']
    user.email = user_data['email']

    db.session.commit()
    return user_schema.jsonify(user), 200

#DELETE a user
@app.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    user = db.session.get(User, id)

    if not user:
        return jsonify({"message": "Invalid user id"}), 400
    
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": f"succefully deleted user {id}"}), 200


#CREATE Pet
@app.route('/pets', methods=['POST'])
def create_pet():
    try:
        pet_data = pet_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    new_pet = Pet(name=pet_data['name'], animal=pet_data['animal'])
    db.session.add(new_pet)
    db.session.commit()

    return pet_schema.jsonify(new_pet), 201


#Add pet to user
@app.route('/users/<int:user_id>/add_pet/<int:pet_id>', methods=['GET'] )
def adopt_pet(user_id, pet_id):
    user = db.session.get(User, user_id)
    pet = db.session.get(Pet, pet_id)

    user.pets.append(pet)
    db.session.commit()
    return jsonify({"message": f"{user.name} adopted the {pet.animal}, {pet.name}!"}), 200

#Add multiple Pets
@app.route('/users/<int:user_id>/add_pets', methods=['POST'])
def add_pets(user_id):
    user = db.session.get(User, user_id)
    pet_data = request.json

    for id in pet_data['pet_ids']:
        pet = db.session.get(Pet, id)
        user.pets.append(pet)
        db.session.commit()

    return jsonify({"message": "All pets added!"}), 200


#Show User Pets
@app.route("/users/my-pets/<int:user_id>", methods=['GET'])
def my_pets(user_id):
    user = db.session.get(User, user_id)
    return pets_schema.jsonify(user.pets), 200
    


if __name__ == "__main__":

    with app.app_context():
        #db.drop_all()
        db.create_all()

    app.run(debug=True)