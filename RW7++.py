import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Default downsampling factor
DOWN_SAMPLE_DEFAULT = 175


COLORS = {
    f"Rotation {i}": f'rgba({(i*35)%256}, {(i*85)%256}, {(i*125)%256}, 0.5)' for i in range(1, 26)
}


def rgba_to_matplotlib_color(rgba_str):
    rgba_values = rgba_str.strip('rgba()').split(',')
    rgba_values = [float(val) / 255.0 if i < 3 else float(val) for i, val in enumerate(rgba_values)]
    return tuple(rgba_values)

def process_dataset(df, position_col, torque_col, downsample_factor):
    # Identify where ActualPosition [rad] starts with 2
    start_index = df[df[position_col].apply(lambda x: int(x) == 2)].index.min()
    if pd.isna(start_index):
        return None  

    # Slice the dataframe from the detected start index
    df = df.iloc[start_index:].reset_index(drop=True)

    rotations = []
    last_position = df[position_col].iloc[0]  
    rotation_data = []

    for _, row in df.iterrows():
        position = row[position_col]
        torque = row[torque_col]

        if position - last_position >= 6.28318531:  # Full rotation
            rotations.append(rotation_data)
            rotation_data = []
            last_position = position
        rotation_data.append((position, torque))

    if rotation_data: 
        rotations.append(rotation_data)

   
    downsampled_rotations = {}
    for i, rotation in enumerate(rotations):
        positions = [p for p, _ in rotation]
        torques = [t for _, t in rotation]

        position_start = positions[0]
        relative_positions = [p - position_start for p in positions]

        degrees_positions = np.degrees([p % (2 * np.pi) for p in relative_positions])

        downsampled_torques = [
            np.mean(torques[j:j + downsample_factor]) for j in range(0, len(torques), downsample_factor)
        ]

        max_degrees = degrees_positions[-1]
        downsampled_positions = np.linspace(0, max_degrees, len(downsampled_torques))

        downsampled_rotations[f"Rotation {i+1}"] = {
            "positions": downsampled_positions,
            "torques": downsampled_torques
        }

    return downsampled_rotations


def plot_downsampled_data(rotations):
    plt.figure(figsize=(10, 6))
    
    for label, data in rotations.items():
        color = rgba_to_matplotlib_color(COLORS.get(label, 'rgba(0, 0, 0, 0.5)'))
        plt.plot(data["positions"], data["torques"], label=label, color=color)

    plt.title(f"Torque vs. Position for {uploaded_file.name}")
    plt.xlabel("Position [°]")
    plt.ylabel("Torque")
    plt.xticks(np.arange(0, 361, 20))
    plt.ylim(-0.5, -0.2)
    plt.grid(True)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0.)
    st.pyplot(plt.gcf())

# Streamlit App UI
st.title("Torque and Position Analyzer")
st.write("Upload datasets, adjust downsampling size, and visualize the results!")


downsample_factor = st.sidebar.slider("Downsampling Size", min_value=10, max_value=400, value=DOWN_SAMPLE_DEFAULT, step=5)


uploaded_files = st.file_uploader("Upload CSV Files", type=["csv"], accept_multiple_files=True)


if uploaded_files:
    for uploaded_file in uploaded_files:
        st.subheader(f"File: {uploaded_file.name}")
        df = pd.read_csv(uploaded_file, delimiter='\t')

        df = df.drop(columns=['Unnamed: 3'], errors='ignore')

        position_col = "ActualPosition [rad]"
        torque_col = "Actual Torque [of nominal]"

        if position_col not in df.columns or torque_col not in df.columns:
            st.error(f"File {uploaded_file.name} does not contain the required columns: {position_col}, {torque_col}")
            continue

        timeframes = process_dataset(df, position_col, torque_col, downsample_factor)

        if timeframes is None:
            st.warning(f"File {uploaded_file.name} does not contain valid data starting with a minimum {position_col} value of 2.")
            continue

        plot_downsampled_data(timeframes)
else:
    st.info("Upload one or more CSV files to begin.")

st.sidebar.write("Adjust the downsampling size using the slider.")
