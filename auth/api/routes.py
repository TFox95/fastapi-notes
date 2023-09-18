from fastapi import APIRouter, Depends, status, HTTPException, Request, Cookie
from fastapi.encoders import jsonable_encoder as jEnc
from fastapi.responses import JSONResponse

from sql_app.database import get_db
from sqlalchemy.orm import Session

from auth import schemas, models, crud
from core.config import JsonRender

NAMESPACE = f"Auth Routes"

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

UserModel = models.User


async def checkAuthorization(request: Request, Authorization=Cookie(None)) -> str:
    """
     Check if Authorization header is present and return Authorization token if it
     is. Otherwise raise HTTPException
     
     Args:
     	 request: Request to check Authorization header
     	 Authorization: Authorization cookie to use for token validation defaults to None
     
     Returns: 
     	 Authorization token as string or raises an HTTPException
    """
    try:
        Authorization = Authorization if Authorization else str(
            request.headers["Authorization"]).split(" ")[-1] if not None else None
        # HTTPException HTTP401_UNAUTHORIZED if no token is found.
        if not Authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="No token found")
        return Authorization
    except:
        raise HTTPException(
            detail=f"Token invalid", status_code=status.HTTP_401_UNAUTHORIZED)


async def getCurrentUser(token=Depends(checkAuthorization), db: Session = Depends(get_db)) -> UserModel:
    """
     Get the user associated with the token. This is a wrapper around the CRUD method retrieve_user
     
     Args:
     	 token: The token to use for the retrieval
     	 db: The database to use for the retrieval. Defaults to : data : ` get_db `
     
     Returns: 
     	 The user associated with the token or None if there is which will then return an
       HTTPException of HTTP_500_INTERNAL_SERVER_ERROR.
    """
    try:
        decodedToken: dict = crud.AuthHandler().decode_token(token)
        decodedUser = crud.UserCRUD.retrieve_User(
            db, username=decodedToken.get("username"))
        return decodedUser
    # HTTPExceprion HTTP_500_INTERNAL_SERVER_ERROR if no User was recovered
    except:
        raise HTTPException(detail="Internal Error",
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/")
async def get_auth():
    return "auth app created!"


@router.post("/register")
async def Register(request: schemas.UserCreate, db: Session = Depends(get_db)):
    """
     Register a new user. This will check to make sure email and username are not already in use
     as well as check to ensure the psw and re_psw are equivalient.
     Args:
     	 request: request to register the user
     	 db: db to use for database operations. If you don't want to use this you can pass a session here
     
     Returns: 
     	a Json Response that contains a data object on success which will provide an user has been
      successfully created string, but on error will raise an Exception whilist delivering an detail 
      object .
    """
    dbEmailQuery: UserModel = db.query(UserModel).filter(
        UserModel.email == request.email).scalar() or None
    dbUsernameQuery: UserModel = db.query(UserModel).filter(
        UserModel.username == request.username).scalar() or None
    # Checks if the database email and username query are in use.
    if dbEmailQuery or dbUsernameQuery or (request.psw != request.re_psw):
        # If the email is already in use raise an HTTPException.
        if dbEmailQuery:
            raise HTTPException(
                detail=f"Email, {dbEmailQuery.email}, is already in use", status_code=status.HTTP_409_CONFLICT)
        # If the username is already in use raise an HTTPException.
        if dbUsernameQuery:
            raise HTTPException(
                detail=f"Username, {dbUsernameQuery.username}, is already in use", status_code=status.HTTP_409_CONFLICT)
                        # If the passwords dont match raise an HTTPException.
        raise HTTPException(
            detail="Passwords don't match; Passwords must be the same", status_code=status.HTTP_409_CONFLICT)
    _user = crud.UserCRUD.create_User(db, request)
    return JSONResponse({
        "data": f"User, {_user.username}, has been created!"
    }, status.HTTP_201_CREATED)


@router.post("/token")
async def token(request: schemas.UserLogin, db: Session = Depends(get_db)):
    """
    Return JWT token for user. This authorization token is used to ensure the necessary 
    privleges is provided to the specific user so they can access protected content 
    
    Args:
        request: UserLogin object with username and password
        db: database to use for authentication. If not provided database will be created
    
    Returns: 
        On success a JSON response that contains a data object which will provide a token
        key with the authorization, as well as an username key which will provide the user's 
        Username, but on failure a detail object will be return with a reason of it's failure.
    """

    user: UserModel = crud.UserCRUD.retrieve_User(db, email=request.username
                                                  ) if "@" in str(request.username) else crud.UserCRUD.retrieve_User(db, username=request.username)
    checkPassword = crud.AuthHandler().verify_password(psw=request.password,
                                                        hashed_psw=user.password) if (user) else None
    # Check if password is valid; if not retry
    if not checkPassword:
        raise HTTPException(detail="Password or Username doesn't match; Check credintials and retry",
            status_code=status.HTTP_409_CONFLICT)
    #Update User's lastLogin field within the data base then encode the jwt which will be provide in the reponse
    crud.UserCRUD.lastLogin(db, user.username)
    jwt = crud.AuthHandler().encode_token(user.UUID, user.username)
    content = {"data": {
        "username": f"{user.username}", "token": f"bearer {jwt}"}}
    res = JSONResponse(content, status_code=status.HTTP_302_FOUND)
    res.set_cookie(key="Authorization", value=jwt, secure=True, httponly=True)
    return res


@router.get("/protected")
async def protectedRoute(decoded=Depends(getCurrentUser)):
    data = decoded
    if not data:
        raise HTTPException(detail="uhh some went wrong!", status_code=status.HTTP_400_BAD_REQUEST)
    return JSONResponse({"data": "lets go!"}, status_code=status.HTTP_200_OK)


@router.post("/logout")
async def logout(decoded: dict = Depends(getCurrentUser)):
    """
     Logs out the user from the API. This is a no - op if the user isn't logged in

     Args:
     	 decoded: The decoded data from the request

     Returns: 
     	 A response containing a sting with the user's username that
       has been logged out
    """
    username = decoded.username
    content = {"data": f"{username} has been Logged out"}
    res = JSONResponse(content, status.HTTP_202_ACCEPTED)
    res.delete_cookie("Authorization")
    return res


@router.get("/retrieve_user", response_class=JsonRender, response_model=schemas.UserBase, response_model_exclude=["user_profile", "isAdmin", "password"])
async def retrieveUserData(request: Request, User=Depends(getCurrentUser)) -> schemas.UserBase:
    """
     Retrieves the user data. This is called by User Arg and should return the user data as a 
     dictionary based on the schema of UserBase, so we do this by using the reponse_model, 
     but there are fields that we do not want to pass to the standard user. So we utilize the, 
     reponse_model_exclude Argument, to leave out the following fields: isAdmin, password, and 
     user_profile
     
     Args:
     	 request: The request being processed. Used to determine if we are in a context where user data is available or not.
     	 User: The user that should be returned. If not provided it will be determined based on the current user.
     
     Returns: 
     	 Returns the User within the custom JsonRender response class which on success will provide
       a data Json object but on failure will provide a detail object containing the reason of the exception 
    """
    return User


@router.get("/retrieve_user/all")
async def retrieveAllUserData(request: Request, User=Depends(getCurrentUser)):
    """
     Retrieve all user data. This is used to retrieve all user of a Users data
     that the user has access to.
     
     Args:
     	 request: The request for this request. ( required )
     	 User: The user to retrieve data for. ( optional )
     
     Returns: 
     	 A JSON response with the user data in the format : { " data " : json. dumps ( user )
    """
    decodedUser = jEnc(User)
    content = {"data": decodedUser}
    return JSONResponse(content, status.HTTP_200_OK)


@router.get("/users_all", response_class=JsonRender)
async def getAllUsers(request: Request, db: Session = Depends(get_db)):
    """
     Grab all users from the database. This is used to grab a list of all users that are in the database
     
     Args:
     	 request: HTTP request from client ( unused )
     	 db: SQLAlchemy session to use ( unused )
     
     Returns: 
     	 List of UserModel's with information about their specific User
    """
    grabUsers: list = db.query(UserModel).all()
    # This method will raise an HTTPException if the user is not grabUsers
    if not grabUsers:
        raise HTTPException(detail="Something went wrong, please Try again later", status_code=status.HTTP_400_BAD_REQUEST)
    return grabUsers


@router.patch("/patch_profile", response_class=JsonRender, response_model=schemas.ProfileBase, response_model_exclude=["pk", "user_pk", "stripe_Cust_ID"] )
async def patchProfile(req:schemas.PatchProfile, db:Session=Depends(get_db), decodeUser:schemas.UserBase=Depends(getCurrentUser)):
    """
     Updates a User's Profile in the Database This is a wrapper around CRUD's patch_profile method
     Also checks weather the keys in the data to update dict is areaddy stored in the decodedUserprofile
     dict.
     
     Args:
     	 req: Request object to be used for patching
     	 db: Object that holds the database connection to be used
     	 decodeUser: User object that contains the profile to be updated
     
     Returns: 
     	 A response containing the updated profile as part of a successful 
       data object which the profile will be defined in the _profile variable, 
       but on failure it will return a detail Json object which will contain 
       the reaon of failure.
    """
    decodedUserProfile: dict= decodeUser.profile.dict()
    data_to_update: dict= req.dict(exclude_unset=True)
    # If the user profile is already stored within the database raise an HTTPException.
    if all((key, value) in decodedUserProfile for (key,value) in data_to_update.items()):
        raise HTTPException(status.HTTP_406_NOT_ACCEPTABLE, "Value's already stored within Database")
    _profile = crud.ProfileCRUD.patch_profile(db, req, decodeUser.pk)
    return _profile