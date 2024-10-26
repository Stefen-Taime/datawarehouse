from cryptography.fernet import Fernet
import os

def generate_fernet_key():
    """Generate a valid Fernet key and save it to .env file."""
    # Generate a new Fernet key
    fernet_key = Fernet.generate_key().decode()
    
    # Read existing .env file content if it exists
    env_content = {}
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    env_content[key] = value

    # Update or add AIRFLOW_FERNET_KEY
    env_content['AIRFLOW_FERNET_KEY'] = fernet_key
    
    # Write back to .env file
    with open('.env', 'w') as f:
        for key, value in env_content.items():
            f.write(f"{key}={value}\n")
    
    print(f"Generated Fernet key: {fernet_key}")
    print("Key has been saved to .env file")
    return fernet_key

if __name__ == "__main__":
    generate_fernet_key()