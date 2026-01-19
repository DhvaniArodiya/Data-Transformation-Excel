import pandas as pd
import sys

def test_xml():
    file_path = 'temp_uploads/Bill Receivable.xml'
    print(f"Testing file: {file_path}")
    try:
        # Try default
        print("Attempting default pd.read_xml...")
        df = pd.read_xml(file_path)
        print("Success! Head:")
        print(df.head())
    except Exception as e:
        print(f"Default failed: {e}")
        
    try:
        # Try with different xpath if it's nested
        print("\nAttempting pd.read_xml with xpath='.//row' (common default inference)...")
        # Since I don't know the structure, let's try to inspect it first
        import lxml.etree as ET
        tree = ET.parse(file_path)
        root = tree.getroot()
        print(f"Root tag: {root.tag}")
        for child in root[:3]:
            print(f"Child tag: {child.tag}")
    except Exception as e:
        print(f"Inspection failed: {e}")

if __name__ == "__main__":
    test_xml()
