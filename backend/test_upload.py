import requests

def test_upload():
    import numpy as np
    import cv2
    import io

    # Create a simple valid JPEG image
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    ok, buf = cv2.imencode(".jpg", img)
    
    files = {'image': ('test.jpg', buf.tobytes(), 'image/jpeg')}
    
    try:
        # Get login token first
        login_url = "http://localhost:8001/api/auth/login"
        login_data = {"email": "admin@visionid.ai", "password": "Admin@12345"}
        r = requests.post(login_url, json=login_data)
        r.raise_for_status()
        token = r.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        url = "http://localhost:8001/api/recognition/image"
        r = requests.post(url, files=files, headers=headers)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_upload()
