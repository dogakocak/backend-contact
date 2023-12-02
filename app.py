from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flasgger import Swagger
import hashlib

app = Flask(__name__)
app.config[
    'SQLALCHEMY_DATABASE_URI'] = 'mysql://doadmin:AVNS_Wvj598dywbNenMoAW5k@db-mysql-fra1-55994-do-user-15111911-0.c.db.ondigitalocean.com:25060/dogadb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SWAGGER'] = {
    'title': 'Contact API',
    'uiversion': 3
}

db = SQLAlchemy(app)
swagger = Swagger(app)
ma = Marshmallow(app)


class Contact(db.Model):
    __tablename__ = 'Contacts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    name = db.Column(db.String(255), nullable=False)
    surname = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)


class Users(db.Model):
    __tablename__ = 'Users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(64), nullable=False)


# Veritabanını oluştur
with app.app_context():
    db.create_all()


class UserSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Users


class ContactSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Contact

    id = ma.auto_field()
    name = ma.auto_field()
    surname = ma.auto_field()
    phone_number = ma.auto_field()


user_schema = UserSchema()
contact_schema = ContactSchema()


# Endpoint to add a new user
@app.route('/add_user', methods=['POST'])
def add_user():
    """
    Add a new user
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          properties:
            username:
              type: string
              description: User's username
            password:
              type: string
              description: User's password
    responses:
      200:
        description: User added successfully
    """
    data = request.get_json()

    existing_user = Users.query.filter_by(username=data['username']).first()
    if existing_user:
        return jsonify({'message': 'Username is taken!'}), 400

    password_hash = hashlib.sha256(data['password'].encode()).hexdigest()

    new_user = Users(
        username=data['username'],
        password=password_hash
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User added successfully!'})


# Endpoint to list all users
@app.route('/list_users', methods=['GET'])
def list_users():
    """
    List all users
    ---
    responses:
      200:
        description: List of users
    """
    users = Users.query.all()
    user_list = []

    for user in users:
        user_list.append(user_schema.dump(user))

    return jsonify({'users': user_list})


# Yeni iletişim eklemek için endpoint
@app.route('/add_contact', methods=['POST'])
def add_contact():
    """
    Add a new contact
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          id: Contact
          properties:
            user_id:
              type: integer
              description: User ID
            name:
              type: string
              description: Contact name
            surname:
              type: string
              description: Contact surname
            phone_number:
              type: string
              description: Contact phone number
    responses:
      200:
        description: Contact added successfully
    """
    data = request.get_json()

    existing_user = Users.query.filter_by(id=data['user_id']).first()
    if not existing_user:
        return jsonify({'message': 'User cannot be found'}), 400

    new_contact = Contact(
        user_id=data['user_id'],
        name=data['name'],
        surname=data['surname'],
        phone_number=data['phone_number']
    )

    db.session.add(new_contact)
    db.session.commit()

    return jsonify({'message': 'Contact added successfully!'})


# İletişim silmek için endpoint
@app.route('/delete_contact/<int:contact_id>', methods=['DELETE'])
def delete_contact(contact_id):
    """
    Delete a contact
    ---
    parameters:
      - name: contact_id
        in: path
        type: integer
        required: true
        description: Contact ID to delete
    responses:
      200:
        description: Contact deleted successfully
      404:
        description: Contact not found
    """
    contact_to_delete = Contact.query.get(contact_id)

    if contact_to_delete:
        db.session.delete(contact_to_delete)
        db.session.commit()
        return jsonify({'message': 'Contact deleted successfully!'})
    else:
        return jsonify({'message': 'Contact not found!'}), 404


# Endpoint to list all contacts
@app.route('/list_contacts', methods=['GET'])
def list_contacts():
    """
    List all contacts
    ---
    responses:
      200:
        description: List of contacts
    """
    contacts = Contact.query.all()
    contact_list = []

    for contact in contacts:
        contact_list.append({
            'id': contact.id,
            'user_id': contact.user_id,
            'name': contact.name,
            'surname': contact.surname,
            'phonenumber': contact.phonenumber
        })

    return jsonify({'contacts': contact_list})


@app.route('/get_contact/<int:contact_id>', methods=['GET'])
def get_contact(contact_id):
    """
    Get a contact by ID
    ---
    parameters:
      - name: contact_id
        in: path
        type: integer
        required: true
        description: Contact ID to retrieve
    responses:
      200:
        description: Contact retrieved successfully
      404:
        description: Contact not found
    """
    contact = Contact.query.get(contact_id)

    if contact:
        return jsonify({
            'id': contact.id,
            'user_id': contact.user_id,
            'name': contact.name,
            'surname': contact.surname,
            'phonenumber': contact.phonenumber
        })
    else:
        return jsonify({'message': 'Contact not found!'}), 404


@app.route('/search_contacts', methods=['GET'])
def search_contacts_by_name():
    """
    Search for contacts by name
    ---
    parameters:
      - name: name
        in: query
        type: string
        required: true
        description: Contact name for search
    responses:
      200:
        description: List of contacts matching the search criteria
    """
    name = request.args.get('name')

    # Check if 'name' parameter is provided
    if not name:
        return jsonify({'message': 'Please provide a name for search'}), 400

    # Build the query based on the provided name
    query = Contact.query.filter(Contact.name.ilike(f'%{name}%'))

    # Execute the query and serialize the results
    results = []
    for contact in query.all():
        dumped_contact = contact_schema.dump(contact)
        if dumped_contact is not None:
            results.append(dumped_contact)
        else:
            print(f"Skipped a contact due to dump result being None: {contact}")

    return jsonify({'contacts': results})


if __name__ == '__main__':
    app.run(debug=True)
