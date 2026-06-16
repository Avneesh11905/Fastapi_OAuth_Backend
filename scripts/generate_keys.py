from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def generate_rsa_keypair():
    """Generates a secure 2048-bit RSA key pair for JWT signing."""
    print("Generating RSA-2048 Keypair...")
    
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # Serialize private key to PEM format
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')

    # Get public key and serialize to PEM format
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')

    print("\n" + "="*50)
    print("Keypair generated successfully!")
    print("Copy the following lines into your .env file:")
    print("="*50 + "\n")

    # Use single double-quotes for python-dotenv multiline support
    print(f'JWT_PRIVATE_KEY="{private_pem}"')
    print()
    print(f'JWT_PUBLIC_KEY="{public_pem}"')
    
    print("="*50 + "\n")
    print("Note: In a production environment, you should never share your PRIVATE_KEY.")
    print("You can distribute your PUBLIC_KEY to other microservices so they can verify your JWTs.")

if __name__ == "__main__":
    generate_rsa_keypair()
