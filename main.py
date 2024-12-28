import streamlit as st
import requests
import base64
from dotenv import load_dotenv
import os
import pandas as pd

# Load environment variables and set page config
load_dotenv()
st.set_page_config(
    page_title="Chart Data Extractor",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for smaller fonts and compact layout
st.markdown("""
    <style>
        .main > div {
            padding-top: 2rem;
        }
        .block-container {
            padding-top: 1rem;
            padding-bottom: 0rem;
        }
        h1 {
            font-size: 1.5rem !important;
            margin-bottom: 0.5rem !important;
        }
        .stMarkdown p {
            font-size: 0.9rem;
            margin-bottom: 0.5rem;
        }
        .uploadedFile {
            margin-bottom: 1rem;
        }
        .css-1d391kg {  /* Sidebar title */
            font-size: 1.2rem;
        }
        .stButton button {
            width: 100%;
            margin-top: 0.5rem;
        }
    </style>
""", unsafe_allow_html=True)

def process_chart_image(image_bytes):
    """Process the uploaded chart image and return the extracted data"""
    image_b64 = base64.b64encode(image_bytes).decode()

    # Check file size
    if len(image_b64) >= 180_000:
        st.error("Image is too large. Please use an image smaller than 180KB")
        return None

    # Get API key from environment variables
    api_key = os.getenv('NVIDIA_API_KEY')
    if not api_key:
        st.error("NVIDIA_API_KEY not found in environment variables")
        return None

    invoke_url = "https://ai.api.nvidia.com/v1/vlm/google/deplot"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    }

    payload = {
        "messages": [
            {
                "role": "user",
                "content": f'Generate underlying data table of the figure below: <img src="data:image/png;base64,{image_b64}" />'
            }
        ],
        "max_tokens": 1024,
        "temperature": 0.20,
        "top_p": 0.20,
        "stream": False
    }

    try:
        response = requests.post(invoke_url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error calling API: {str(e)}")
        return None

def parse_markdown_table(markdown_text):
    """Convert markdown table text to pandas DataFrame"""
    try:
        # Split the markdown table into lines
        lines = markdown_text.strip().split('\n')
        
        # Extract headers and data
        headers = [h.strip() for h in lines[0].split('|')[1:-1]]
        data = []
        for line in lines[2:]:  # Skip the separator line
            row = [cell.strip() for cell in line.split('|')[1:-1]]
            data.append(row)
        
        # Create DataFrame
        df = pd.DataFrame(data, columns=headers)
        return df
    except Exception as e:
        st.error(f"Error parsing table: {str(e)}")
        return None

def main():
    # Sidebar
    with st.sidebar:
        st.title("Upload Chart")
        uploaded_file = st.file_uploader(
            "Choose a chart image",
            type=['png', 'jpg', 'jpeg'],
            help="Upload an image of a chart or graph (max 180KB)"
        )
        
        if uploaded_file is not None:
            # Preview image in sidebar with fixed width
            st.image(uploaded_file, 
                    caption="Preview",
                    use_container_width=True,  # Fixed deprecation warning
                    width=250)  # Control preview size
            
            process_button = st.button("Extract Data", type="primary")
        
        # Add info section in sidebar
        with st.expander("ℹ️ About"):
            st.markdown("""
                **Chart Data Extractor**
                - Supports PNG, JPG, JPEG
                - Max file size: 180KB
                - Extracts data tables from charts
                - Download results as CSV
            """)

    # Main content area with custom styling
    st.markdown("""
        <h1 style='margin-bottom: 2rem; font-size: 2rem;'>
            📊 Chart Data Extractor
        </h1>
    """, unsafe_allow_html=True)
    
    # Create two columns for layout with adjusted ratio
    col1, col2 = st.columns([2, 1])  # Adjusted ratio for better layout
    
    with col1:
        if uploaded_file is not None:
            if process_button:
                with st.spinner("Extracting data from chart..."):
                    result = process_chart_image(uploaded_file.getvalue())
                    
                    if result and 'choices' in result:
                        markdown_table = result['choices'][0]['message']['content']
                        df = parse_markdown_table(markdown_table)
                        
                        if df is not None:
                            st.markdown("### 📈 Extracted Data")
                            st.dataframe(
                                df,
                                use_container_width=True,  # Using recommended parameter
                                height=250  # Slightly reduced height
                            )
                            
                            # Download buttons with better layout
                            col1a, col1b, col1c = st.columns([1, 1, 2])
                            with col1a:
                                csv = df.to_csv(index=False).encode('utf-8')
                                st.download_button(
                                    label="📥 Download CSV",
                                    data=csv,
                                    file_name="extracted_data.csv",
                                    mime="text/csv",
                                    use_container_width=True
                                )
    
    with col2:
        if uploaded_file is not None and process_button and result and 'choices' in result:
            with st.expander("🔍 Raw Data", expanded=False):
                st.code(markdown_table, language="markdown")

    # Show upload prompt if no file
    if uploaded_file is None:
        st.info("👈 Please upload a chart image using the sidebar")

    # Add footer
    st.markdown("""
        <div style='position: fixed; bottom: 0; width: 100%; text-align: center; padding: 10px; background: rgba(255,255,255,0.9);'>
            <p style='font-size: 0.8rem; color: #666;'>
                Powered by NVIDIA AI & Streamlit
            </p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
