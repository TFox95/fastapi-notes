from pydantic import BaseModel as Base, EmailStr
from datetime import datetime

class OrmBase(Base):
    class Config:
        orm_mode=True


class CountryCode(OrmBase):
    pk: int | None
    name: str | None


class AddressBase(OrmBase):
    profile_pk: int

    streetNumber: int | None 
    streetName: str | None = None
    aptNumber: str | None = None

    ZipCode: int | None
    city: str | None = None
    state: str | None = None
    country_Code: CountryCode | None


class ProfileBase(OrmBase):
    pk: int | None
    user_pk: int | None

    firstName: str | None = None
    lastName: str | None = None

    stripe_Cust_ID: str | None = None
    One_click_Purchasing: bool | None = None

    AddressList: list[AddressBase] | None


class PatchProfile(OrmBase):
    firstName: str | None
    lastName: str | None
    
    One_click_Purchasing: bool | None
    
    
class UserLogin(Base):
    username: str
    password: str


class UserBase(OrmBase):
    pk: int | None
    UUID: str | None = None
    email: EmailStr
    username: str
    password: str
    
    verified: bool = False
    isAdmin: bool | None

    dateJoined: datetime | str | None
    lastLogin: datetime | str | None = None

    profile: ProfileBase | None | object = {}


class UserCreate(OrmBase):
    email: EmailStr
    username: str
    psw: str
    re_psw: str


class Token(Base):
    exp: int
    iat: int
    iss: str
    uuid: str
    username: str
