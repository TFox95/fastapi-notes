import jwt
from fastapi import HTTPException, status
from uuid import uuid4

from datetime import timedelta, datetime

from pydantic import EmailStr
from sqlalchemy.orm import Session
from sql_app.database import get_db

from auth import schemas, models

from core import logging
from core.hash import Hash
from core.config import settings
from core.logging import ServerINFO

NAMESPACE: str = "Auth CRUD"

# Model variables
UserModel = models.User
ProfileModel = models.Profile

# Schema variables
ProfileSchema = schemas.ProfileBase
TokenSchema = schemas.Token

class AuthHandler():
    Secret = settings.AUTH_SECRET
    Pepper = settings.PEPPER


    def get_password_hash(self, psw: str) -> str:
        """
         Generate a hash based on the password. This is used to generate passwords
         that are stored in the database for the purposes of logging in / verifying 
         a user's password.
         
         Args:
         	 psw: The password to hash.
         
         Returns: 
         	 The hashed password as a bytestring with the length of 256 bytes in 
             the range 0 to 255. Note that the password is encrypted.
        """
        return Hash.encode(key=psw, pepper=self.Pepper)


    def verify_password(self, psw, hashed_psw) -> bool:
        """
         Verifies a password. This is a wrapper around Hash.verify
         that we have a key and a encoded key.
         
         Args:
         	 psw: The password to verify.
         	 hashed_psw: The encoded password that we want to verify.
         
         Returns: 
         	 True if the password is correct False otherwise. Note 
             that this does not check the validity of the password.
        """
        pswKeyHash = self.get_password_hash(psw)
        return Hash.verify(key=pswKeyHash, encoded_key=hashed_psw, pepper=self.Pepper)


    def encode_token(self, uuid: str, username: str) -> str:
        """
         Encode a token to be used in requests. This is a helper method to encode 
         an auth token that can be used in requests.
         
         Args:
         	 uuid: The UUID of the user
         	 username: The username of the user ( if any )
         
         Returns: 
         	 The encoded token as a base64 - encoded string. Note that you must 
             add the token yourself.
        """
        payload = {
            "iss": "https://www.Aestriks.com",
            "exp": datetime.utcnow() + timedelta(days=100, hours=0, minutes=0),
            "iat": datetime.utcnow(),
            "uuid": uuid,
            "username": username}
        return jwt.encode(
            payload,
            self.Secret,
            algorithm="HS256")


    def decode_token(self, token) -> TokenSchema:
        """
         Decodes a JWT token. This is a wrapper around jwt.decode 
         to handle exceptions that are raised in the process.
         
         Args:
         	 token: The JWT token to decode
         
         Returns: 
         	 The payload of the JWT token as a TokenSchema or 
             raises HTTPException if the token is invalid.
        """
        try:
            payload = jwt.decode(
                token,
                self.Secret,
                algorithms="HS256")
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail='Signature has expired')
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token')
        return payload


    def grant_access(self, token: str, uuid: str):
        """
         Check if token is valid. This is used to verify that 
         a user has access to the resource identified by token.
         
         Args:
         	 token: Token obtained from token_generator
         	 uuid: UUID of the resource being accessed
         
         Returns: 
         	 True if access is granted False if access is not 
             granted and exception is raised if token is not valid.
        """
        decoded = self.decode_token(token)
        # Returns true if uuid is not equal to decoded. uuid.
        if not uuid == decoded.uuid:
            return False
        return True


class UserCRUD():

    def create_User(db: Session, request: schemas.UserCreate) -> UserModel:
        """
         function to create a user & a linked user profile instance in 
         the database and return the UserModel instance.
         
         Args:
         	 db: db connection to be used to perform database operations
         	 request: request containing user details to be created and linked
         
         Returns: 
         	 user instance of the created user or None if creation 
           failed for some reason ( such as not having a password ).
        """

        _dict: dict = request.dict()
        _dict["uuid"] = f"user_{uuid4()}"
        _dict["psw"] = AuthHandler().get_password_hash(psw=_dict.get("re_psw"))
        _dict.pop("re_psw", None)
        _user: UserModel = UserModel(email=_dict.get("email"), username=_dict.get("username"),
                                     password=Hash.encode(_dict.get("psw"), settings.PEPPER), UUID=_dict.get("uuid"),
                                     verified=_dict.get("verified"), isAdmin=_dict.get("isAdmin"))
        # adding User & User's Profile to db and then refreshing the _user instance with the updated information
        db.add(_user)
        db.commit()
        db.refresh(_user)
        _profile = models.Profile(user_pk=_user.pk)
        db.add(_profile)
        db.commit()
        return _user


    def retrieve_User(db: Session, username: str = None, email: EmailStr = None) -> UserModel:
        """
         Retrieve a user from the database. This is used to retrieve users that 
         have been logged in via email or username.
         
         Args:
         	 db: The database to query.
         	 username: The username of the user to retrieve. If None all users are retrieved.
         	 email: The email of the user to retrieve. If None all users are retrieved.
         
         Returns: 
         	 The user or None if not found. Note that the return value is a 
             scalar but may be different from the value returned.
        """
        _retrieve_user = db.query(UserModel).filter(
            UserModel.username == username).scalar() if (username) else db.query(
            UserModel).filter(UserModel.email == email).scalar() if (email) else None
        return _retrieve_user


    def lastLogin(db: Session, username: str) -> bool:
        """
         Update the lastLogin field of a user. This is 
         used to determine when was the user last logged in. 
         
         Args:
         	 db: database connection to use for database operations
         	 username: username of the user to update the lastLogin field
         
         Returns: 
         	 True if successful else False if failed.
        """
        updateUserData = db.query(UserModel).filter(
            UserModel.username == username).update({
                "lastLogin": datetime.now()})
        # If updateUserData is not set to true the user data is not updated.
        if not updateUserData:
            return False
        db.commit()
        return True

class ProfileCRUD():
    
    def patch_profile(db: Session, request: ProfileSchema, identifier: int | str) -> ProfileSchema:
        """
        Updates the profile with the given identifier with the data from the request object.

        Args:
            db: The database session.
            request: The request object.
            identifier: The identifier of the profile to update.

        Returns:
            The updated ProfileSchema object.
        """

        # Check the permissions of the user who is calling the function.
        # if not db.query(UserModel).filter_by(pk=request.pk).first().isAdmin:
        #     raise PermissionError("You do not have permission to update profiles.")

        # Get the profile from the database.
        profile = db.query(ProfileModel).filter_by(user_pk=identifier).scalar()

        # Update the profile with the data from the request object.
        for key, value in request.dict(exclude_unset=True).items():
            setattr(profile, key, value)
        # Refresh the profile in the database.
        # db.refresh(profile)

        # Commit the changes to the database.
        db.commit()
        
        db.refresh(profile)

        # Return the updated ProfileSchema object.
        return ProfileSchema(**profile.dict())
