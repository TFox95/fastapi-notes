import hashlib
from core.config import settings


class Hash():

    def encode(key: str, pepper: str, algorithm: str = None) -> str:
        """
        class Based function that takes in a key and optional algorithm arguments
        to return a salted and peppered hashed value string for the key that was implemented based on the
        algorithm used. Avaiable algorithms are sha3_256 & sha3_512.

        If no algorithm is Selected, the default algorithm of sha3_256 will
        be selected.
        """
        saltKeyPepper: str = f"{settings.SALT}{key}{pepper}"

        if type(key) is not str:
            raise Exception(
                "value passed was not a str; argument must be a String")
        if type(pepper) is not str:
            raise Exception(
                "Pepper passed was not a str; argument must be a String")
        if algorithm and type(algorithm) is not str:
            raise Exception(
                "value passed was not Falsy or a str; Field must either be blank, Falsy, or a String")

        try:
            encoder: str | None = hashlib.sha3_256(saltKeyPepper.encode()).hexdigest() if algorithm is str(
            "sha3_256") or not algorithm else hashlib.sha3_512(saltKeyPepper.encode()).hexdigest() if algorithm is str(
                "sha3_512") else None

            if not encoder:
                raise Exception("incorrect algorithm used. Please utilize one of the following algorithms: sha3_256 & sha3_512. Or leave algorithm field blank, which will invoke default algorithm, which is sha3_256")
            
            return encoder

        except Exception as exc:
            raise exc


    def verify(key: str, encoded_key: str, pepper: str, algorithm: str = None) -> bool:
        """
        class Based function that takes in a key, a hash of a key, & optional algorithm arguments
        to return a True or False value depending on the comparison of the  salted & peppered two 
        provided keys. Avaiable algorithms are sha3_256 & sha3_512.

        If no algorithm is Selected, the default algorithm of sha3_256 will be
        be selected.
        """
        saltKeyPepper: str = f"{settings.SALT}{key}{pepper}"

        if type(key) is not str:
            raise Exception(
                "key passed wasn't a str; argument must be a String")
        if type(encoded_key) is not str:
            raise Exception(
                "encoded_key passed wasn't a str; argument must be a String")
        if type(pepper) is not str:
            raise Exception(
                "Pepper passed wasn't a str; argument must be a String")
        if algorithm and type(algorithm) is not str:
            raise Exception(
                "value passed was not None or a str; Field must either be blank, or a String")

        try:
            encoder:hashlib.sha3_256 = hashlib.sha3_256(saltKeyPepper.encode()).hexdigest() if algorithm is str(
            "sha3_256") or not algorithm else hashlib.sha3_512(saltKeyPepper.encode()).hexdigest() if algorithm is str(
                "sha3_512") else None

            if not encoder or encoder != encoded_key:
                return False
            
            return True
                
        except Exception as exc:
            raise exc