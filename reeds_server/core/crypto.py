# Handle python imports
import datetime
import jwt
import bcrypt
import os


# TDOO: During production get this from environment key
JWT_KEY = os.getenv('JWT_KEY')
assert JWT_KEY != None

# class for each user
class User:

    def __init__(self, 
            username: str, 
            email: str,
            password: str,
            country: str,
            organization: str,
            image_name: str
            ):
        
        self.user = {
                'username': username,
                'email': email,
                'password': password,
                'country': country,
                'organization': organization,
                'image_name': image_name
            }

# Hash class
class Hash:

    def __init__(self, db):

        self.db = db

    def get_reset_token(self, user):

        try:
            user_token = jwt.encode({
                'username': user.username,
                'email': user.email,
                'country': user.country,
                'organization': user.organization,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=24*60*60)},
                JWT_KEY,algorithm='HS256')
            
            hashed_token, salt = self.hash_string(user_token)
            return user_token, hashed_token
        except Exception as e:
            print(str(e))
            return None

       
    def hash_string(self, mystring):
        
        salt = bcrypt.gensalt()
        hashed_token = bcrypt.hashpw(mystring.encode('utf-8'), salt)
        return hashed_token, salt

    def get_user_for_reset_token(self, token, email):

        htoken = self.db.get_htoken(email)
        
        if htoken != None:
            if bcrypt.checkpw(token.encode('utf-8'), htoken.encode('utf-8')):
                return True
            else:
                return False
        else: 
            return False

    def signup(self, session, user):
        
        # Fill up the missing info with null values
        user_exists = self.db.is_user_exist(session, user)

        if not user_exists:

            try:
                hash_key, salt = self.hash_string(user['password'])
               
                user_obj = User(user['username'], user['email'], hash_key.decode(), user['country'],\
                    user['org'], user['image_name'])
                
                if user_obj.user != None:
                    if self.db.insert_user(session, user_obj.user):
                        print('Success')
                        return ('Success creating user!', 201)
                    else:
                        return ('Can not write into database!', 500) 
                else:
                    return ('User creation failed make sure you enter valid email', 500)
                
            except Exception as e:
                print(e)
                return (f'User creation failed, make sure to provide both email and password > {str(e)}', 500)

        else:
            return ('User already exists!', 409)

    def check_password(self, session, username, password):

        user = {
            'username': username,
            'password': password
        }
        hpwd = self.db.get_hpwd(session, username)
        if hpwd !=None:
            if bcrypt.checkpw(user['password'].encode('utf-8'),hpwd.encode('utf-8')):
                return True
            else:
                return False
        else:
            return False


    def login(self, session, user):

        try:
            hpwd = self.db.get_hpwd(session, user['username'])

            if hpwd != None:
                if bcrypt.checkpw(user['password'].encode('utf-8'),hpwd.encode('utf-8')):
                    token = jwt.encode({
                        'username': user['username'],
                        'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=60*60)},
                        JWT_KEY,algorithm='HS256')
                    return ('Login successful', str(token), 200)
                else:
                    return ('Login Failed', None, 500)
            else:
                return ('Login Failed', None, 500)
        except Exception as e:
            return (str(e), None, 500)

    def generate_token(self, data, life_seconds):

        data.update({
            'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=life_seconds)
        })
        return jwt.encode(data,JWT_KEY,algorithm='HS256')

