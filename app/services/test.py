from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

plain_password = "Tahina1@"
hash_new = pwd_context.hash(plain_password)
print(f"Hash généré: {hash_new}")

# Puis teste
print("Vérification :", pwd_context.verify(plain_password, hash_new))
