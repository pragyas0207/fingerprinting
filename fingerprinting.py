import socket
import ssl
from concurrent.futures import ThreadPoolExecutor
import streamlit as st

# ---------------- CORE FUNCTIONS ---------------- #

def grab_banner(host, port):
    try:
        s = socket.socket()
        s.settimeout(3)
        s.connect((host, port))

        request = f"HEAD / HTTP/1.1\r\nHost: {host}\r\n\r\n"
        s.send(request.encode())

        response = s.recv(4096).decode(errors="ignore")
        s.close()

        return response
    except:
        return None


def extract_server_info(response):
    if not response:
        return "No response"

    for line in response.split("\n"):
        if "Server:" in line:
            return line.strip()
    return "Server header not found"


def check_ssl(host, port=443):
    try:
        context = ssl.create_default_context()
        with socket.create_connection((host, port), timeout=3) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
                return f"SSL Enabled | Issuer: {cert.get('issuer')}"
    except:
        return "No SSL / SSL Error"


def fingerprint(host):
    result = {}

    http_response = grab_banner(host, 80)
    https_response = grab_banner(host, 443)

    result["HTTP Info"] = extract_server_info(http_response)
    result["HTTPS Info"] = extract_server_info(https_response)
    result["SSL Info"] = check_ssl(host)

    return result


# ---------------- STREAMLIT UI ---------------- #

st.set_page_config(page_title="Fingerprint Tool", layout="wide")

st.title("🔍 Website Fingerprinting Tool")

# Input
targets = st.text_input("Enter websites (comma separated)", "google.com, github.com")

if st.button("Start Scan"):
    hosts = [h.strip() for h in targets.split(",")]

    st.info("Scanning in progress...")

    results = []

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fingerprint, host): host for host in hosts}

        for future in futures:
            host = futures[future]
            try:
                res = future.result()
                results.append((host, res))
            except:
                results.append((host, {"Error": "Scan failed"}))

    st.success("Scan completed ✅")

    # Display results
    for host, res in results:
        st.subheader(f"🌐 {host}")
        for key, value in res.items():
            st.write(f"**{key}:** {value}")
        st.markdown("---")
